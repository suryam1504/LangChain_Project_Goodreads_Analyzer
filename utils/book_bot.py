import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

llm = get_llm(model="llama-3.3-70b-versatile", temperature=0.7, max_tokens=512)

SYSTEM_PROMPT = (
    "You are a helpful, conversational assistant. "
    "You have a perfect memory of everything said in this conversation — "
    "refer back to earlier messages naturally when relevant."
)


def run_bot():
    print("=" * 50)
    print("  Simple Chatbot with Memory")
    print("  Commands: 'clear' to reset memory, 'quit' to exit")
    print("=" * 50 + "\n")

    # Memory is just the growing list of messages passed to the LLM each turn
    history = [SystemMessage(content=SYSTEM_PROMPT)]

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        if user_input.lower() == "clear":
            history = [SystemMessage(content=SYSTEM_PROMPT)]
            print("[Memory cleared]\n")
            continue

        history.append(HumanMessage(content=user_input))

        try:
            response = llm.invoke(history)
        except Exception as e:
            print(f"[Error: {e}]\n")
            history.pop()  # remove the unanswered human message
            continue

        history.append(AIMessage(content=response.content))
        print(f"\nBot: {response.content}\n")


if __name__ == "__main__":
    run_bot()
