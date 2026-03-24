from groq import RateLimitError
from utils.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# Three high-TPM models in priority order — cycled on RateLimitError
# llama-3.3-70b: 6K TPM / llama-4-scout: 30K TPM / llama-3.1-8b: 6K TPM
_CHAT_MODELS = [
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.1-8b-instant",
]
_chat_llms = [get_llm(model=m, temperature=0.7, max_tokens=512) for m in _CHAT_MODELS]


def _build_system_prompt(user_data: dict) -> str:
    read_books = user_data["all_books"]["read"]["books"]

    lines = [
        "You are a knowledgeable and warm assistant who knows this user's complete reading history.",
        f"Total books read: {user_data['num_read_books']}",
        f"Currently reading: {', '.join(user_data['currently_reading_titles']) or 'nothing currently'}",
        "",
        "Full reading list (Title | Author | User Rating | Avg Rating | Review excerpt):", 
    ]

    for b in read_books:
        review_excerpt = (b.get("review_text") or "")[:300].replace("\n", " ")
        lines.append(
            f"- {b['book_title']} | {b['book_author']} | "
            f"{b.get('rating', '?')}/5 | avg {b.get('avg_rating', '?')} | {review_excerpt}"
        )

    lines += [
        "",
        "Answer the user's questions accurately based on the reading history above.",
        "Be conversational, warm, and reference specific books when relevant.",
        "If asked about a book not on the list, say so clearly.",
    ]
    return "\n".join(lines)


def get_chat_response(user_message: str, chat_history: list, user_data: dict) -> str:
    """Return the assistant's reply, falling back across models on RateLimitError.

    Args:
        user_message:  The new message from the user (not yet in chat_history).
        chat_history:  List of {'role': 'user'/'assistant', 'content': str} — history
                       EXCLUDING the current user_message.
        user_data:     Dict returned by fetch_user_books.
    """
    messages = [SystemMessage(content=_build_system_prompt(user_data))]

    for msg in chat_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=user_message))

    last_error = None
    for llm in _chat_llms:
        try:
            return llm.invoke(messages).content
        except RateLimitError as e:
            last_error = e
            continue  # try next model

    raise last_error
