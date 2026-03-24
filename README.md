# 📚 Goodreads Reader Analyzer

A **LangChain-powered** Streamlit web app that takes any public Goodreads profile and produces a deep, AI-generated analysis of the user's reading personality, genre preferences, reviews, and personalised book recommendations — all through structured LLM pipelines. A live chatbot lets users ask questions about their reading history in natural language.

---

## Demo

> *(Add screenshot here)*

Try it with this sample profile:
`https://www.goodreads.com/user/show/142334643-suryam-gupta`

---

## Features

| Feature | Description |
|---|---|
| **Reader Summary** | A witty, personalised narrative of your reading history. Supports multiple styles: Warm & Witty, Baby Talk, Pirate, and Roast Master. |
| **Genre Analysis** | Top 5 genres identified from your reading list, with the books in each genre and a one-line rationale. |
| **Personality Card** | A reader personality type, description, 4 traits, guilty pleasure, signature author, and a memorable one-liner diagnosis. |
| **Book Recommendations** | 5 personalised recommendations driven by a **sequential chain**: genre analysis → targeted recommendations. Each rec includes mood, reason, and a similar book from your list. |
| **Review Analysis** | Analyses your written reviews for rating style, review voice, most enthusiastic/critical reactions, and a hidden pattern in your behaviour. |
| **Book Chat** | An always-available sidebar chatbot that answers questions about your reading history: ratings, reviews, authors, patterns. |

---

## Architecture & LangChain Patterns

### Parallel Chain — `RunnableParallel`
Genre analysis and personality card are run **simultaneously** using `RunnableParallel`, cutting wait time roughly in half:

```python
parallel_chain = RunnableParallel(
    genres=genre_chain,
    personality=personality_chain
)
```

### Sequential Chain — Genre → Recommendations
Recommendations are produced through a **two-step sequential chain**: the genre LLM identifies your top genres first, then passes them as context into the recommendation prompt:

```python
sequential_chain = (
    genre_chain
    | RunnableLambda(build_rec_input)
    | recommendation_prompt
    | llm_recommendations
    | make_safe_parser(RecommendationOutput)
)
```

### Structured Output with Pydantic
Every LLM output is parsed into a typed **Pydantic model** via `PydanticOutputParser`, ensuring consistent, validated JSON:

```python
class PersonalityCard(BaseModel):
    personality_type: str
    description: str
    traits: List[str]        # exactly 4
    guilty_pleasure: str
    signature_author: str
    diagnosis: str
```

### Robust Output Parsing — `make_safe_parser`
Thinking models (e.g. `kimi-k2`, `qwen3`) emit `<think>...</think>` blocks and sometimes echo back the format schema before the actual JSON. `make_safe_parser` handles all of this:

1. Strips `<think>...</think>` blocks with regex
2. Tries to parse the cleaned text directly
3. Extracts **all** `{...}` JSON objects and tries each until one validates — so an echoed schema block doesn't shadow the real answer
4. Raises `OutputParserException` on total failure (caught gracefully in the UI)

### Chatbot with Context Stuffing
The sidebar chatbot sends the **entire reading history** as a system prompt on every turn — no vector database or embeddings needed. The growing `[SystemMessage, HumanMessage, AIMessage, ...]` list gives the model full conversational memory. Automatic model fallback on `RateLimitError` cycles through three models:

```
llama-3.3-70b-versatile  →  llama-4-scout-17b  →  llama-3.1-8b-instant
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM Orchestration | [LangChain 0.3](https://python.langchain.com/) (`langchain-core`, `langchain-groq`) |
| LLM Provider | [Groq](https://groq.com/) — multiple models per task to spread rate limits |
| Structured Output | Pydantic v2 + `PydanticOutputParser` |
| Frontend | [Streamlit](https://streamlit.io/) |
| Data Source | [PirateReads API](https://api.piratereads.com/) (Goodreads data) |
| Language | Python 3.11 |

---

## Models Used

Each task uses a separate model to spread across Groq's per-model rate limit buckets:

| Task | Model | Why |
|---|---|---|
| Summary | `llama-3.3-70b-versatile` | Strong narrative quality |
| Genre + Personality (parallel) | `llama-4-scout-17b` | 30K TPM — high throughput |
| Recommendations | `qwen3-32b` | Strong book knowledge |
| Review Analysis | `llama-4-scout-17b` | Handles large review payloads |
| Chat | `llama-3.3-70b-versatile` → fallback chain | Conversational quality + reliability |

---

## Project Structure

```
├── st_pages/
│   └── 1_Book_Analyzer.py     # Streamlit UI — all sections + sidebar chat
├── utils/
│   ├── llm.py                 # get_llm() factory (ChatGroq wrapper)
│   ├── piratetreads.py        # Goodreads API client with pagination
│   ├── book_prompts.py        # All ChatPromptTemplates
│   ├── book_analyzer.py       # LangChain chains + Pydantic models
│   ├── book_chat.py           # Chatbot backend with model fallback
│   ├── output_utils.py        # make_safe_parser — thinking-model resilience
│   └── book_bot.py            # Standalone terminal chatbot (for testing)
├── .env                       # GROQ_API_KEY (not committed)
└── requirements.txt
```

---

## Setup & Running

```bash
# 1. Clone and create venv
git clone https://github.com/suryam1504/LangChain_Project.git
cd LangChain_Project
python3.11 -m venv langvenv
source langvenv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your Groq API key
echo "GROQ_API_KEY=your_key_here" > .env

# 4. Run
streamlit run st_pages/1_Book_Analyzer.py
```

Get a free Groq API key at [console.groq.com](https://console.groq.com).
