from utils.llm import get_llm
from utils.piratetreads import get_all_books
from utils.book_prompts import reading_summary_prompt, genre_analysis_prompt, personality_prompt, recommendation_prompt, review_prompt
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_core.runnables import RunnableParallel, RunnableLambda
from utils.output_utils import make_safe_parser
from pydantic import BaseModel, Field
from typing import List

str_parser = StrOutputParser()

# ── One LLM per task — spreads load across model rate limit buckets ──
# Lazily initialized on first use so st.secrets is available.
llm = None
llm_summary         = None
llm_genre           = None
llm_personality     = None
llm_recommendations = None
llm_reviews         = None

def _init_llms():
    global llm, llm_summary, llm_genre, llm_personality, llm_recommendations, llm_reviews
    if llm is not None:
        return
    llm                 = get_llm()
    llm_summary         = get_llm(model="llama-3.3-70b-versatile",                    max_tokens=1024)  # 8K TPM  / 200K TPD — analytical
    llm_genre           = get_llm(model="meta-llama/llama-4-scout-17b-16e-instruct",  max_tokens=3000)  # 30K TPM / 500K TPD — reliable structured output, room for full JSON
    llm_personality     = get_llm(model="openai/gpt-oss-120b",                        max_tokens=1024)  # replacement for decommissioned kimi-k2 — creative, witty
    llm_recommendations = get_llm(model="qwen/qwen3-32b",                             max_tokens=2500)  # 6K TPM  / 500K TPD — strong reasoning, book knowledge
    llm_reviews         = get_llm(model="meta-llama/llama-4-scout-17b-16e-instruct",  max_tokens=1500)  # 30K TPM / 500K TPD — highest TPM, handles large review payloads

# ── Pydantic models ──────────────────────────────────────────

class Genre(BaseModel):
    genre: str = Field(description="Name of the genre")
    books: List[str] = Field(description="Books from the reading list only — use exact titles as provided, no modifications")
    reason: str = Field(description="One line explaining why these books share this genre")

class GenreOutput(BaseModel):
    genres: List[Genre] = Field(description="Top 5 genres with their corresponding books")

class PersonalityCard(BaseModel):
    personality_type: str = Field(description="Short catchy name for their reader personality e.g. 'The Reluctant Philosopher' or 'The Cozy Crime Addict'")
    description: str = Field(description="2-3 sentence warm and witty description of their reading personality")
    traits: List[str] = Field(description="Exactly 4 short punchy traits e.g. 'Cries at short novellas', 'Secretly loves comfort reads'")
    guilty_pleasure: str = Field(description="The most unexpected or lighthearted book on their list that contrasts with their other reads")
    signature_author: str = Field(description="The one author that defines their taste most based on frequency or book choices")
    diagnosis: str = Field(description="One punchy witty one-liner that sums up their entire reader identity. Make it memorable.")

class BookRecommendation(BaseModel):
    title: str = Field(description="Title of the recommended book")
    author: str = Field(description="Author of the recommended book")
    reason: str = Field(description="2 sentence explanation of why this reader would love it, referencing specific books from their list")
    similar_to: str = Field(description="One book from their reading list this recommendation is most similar to")
    mood: str = Field(description="One word mood this book fits e.g. 'Melancholic', 'Thrilling', 'Comforting'")

class RecommendationOutput(BaseModel):
    recommendations: List[BookRecommendation] = Field(description="Exactly 5 book recommendations")

class ReviewAnalysis(BaseModel):
    rating_style: str = Field(description="Are they a harsh, generous, or balanced rater? 1-2 sentences with specific examples from their ratings")
    review_personality: str = Field(description="How do they write reviews — emotional, analytical, brief, poetic? 1-2 sentences")
    most_enthusiastic_about: str = Field(description="Book or author they seemed most positive about based on review text and rating combined")
    most_critical_about: str = Field(description="Book or author they were hardest on")
    hidden_pattern: str = Field(description="One interesting or surprising pattern found in their reviews or ratings — something they might not have noticed about themselves")
    reviewer_type: str = Field(description="A fun one-liner label for their reviewer personality e.g. 'The Reluctant Star Giver' or 'The Emotional Analyst'")

# ── Helper ───────────────────────────────────────────────────

def _max_books_within_token_limit(books: list, max_tokens: int = 11000) -> int:
    total = 0
    for i, book in enumerate(books):
        total += len(str(book)) // 4
        if total > max_tokens:
            return i
    return len(books)

# ── Public functions ─────────────────────────────────────────

def fetch_user_books(user_id: int) -> dict:
    """Fetch all shelves and return a prepared data dict ready for analysis."""
    all_books = get_all_books(user_id)
    read_books = all_books["read"]["books"]
    return {
        "all_books": all_books,
        "num_read_books": all_books["read"]["count"],
        "read_titles": [b["book_title"] for b in read_books],
        "currently_reading_titles": [b["book_title"] for b in all_books["currently_reading"]["books"]],
        "books_with_reviews": [
            {
                "title": b["book_title"],
                "author": b["book_author"],
                "rating": b["rating"],
                "avg_rating": b["avg_rating"],
                "review": b["review_text"]
            }
            for b in read_books if b["review_text"]
        ]
    }

def get_reading_summary(read_titles: list, num_read_books: int, currently_reading_titles: list, style: str = "witty and warm", length: str = "short (1 or 2 paragraphs)") -> str:
    _init_llms()
    chain = reading_summary_prompt | llm_summary | str_parser
    return chain.invoke({
        "books": read_titles,
        "num_read_books": num_read_books,
        "currently_reading": currently_reading_titles,
        "style": style,
        "length": length
    })

def get_genre_analysis(read_titles: list) -> GenreOutput:
    _init_llms()
    parser = PydanticOutputParser(pydantic_object=GenreOutput)
    chain = genre_analysis_prompt | llm_genre | make_safe_parser(GenreOutput)
    return chain.invoke({
        "books": read_titles,
        "format_instructions": parser.get_format_instructions()
    })

def get_personality_card(read_titles: list) -> PersonalityCard:
    _init_llms()
    parser = PydanticOutputParser(pydantic_object=PersonalityCard)
    chain = personality_prompt | llm_personality | make_safe_parser(PersonalityCard)
    return chain.invoke({
        "books": read_titles,
        "format_instructions": parser.get_format_instructions()
    })

def get_genre_and_personality(read_titles: list) -> dict:
    """Run genre analysis and personality card in parallel via RunnableParallel.
    Returns dict with 'genres' (GenreOutput) and 'personality' (PersonalityCard).
    """
    _init_llms()
    genre_parser = PydanticOutputParser(pydantic_object=GenreOutput)
    personality_parser = PydanticOutputParser(pydantic_object=PersonalityCard)

    genre_chain = (
        RunnableLambda(lambda x: {"books": x["books"], "format_instructions": genre_parser.get_format_instructions()})
        | genre_analysis_prompt | llm_genre | make_safe_parser(GenreOutput)
    )
    personality_chain = (
        RunnableLambda(lambda x: {"books": x["books"], "format_instructions": personality_parser.get_format_instructions()})
        | personality_prompt | llm_personality | make_safe_parser(PersonalityCard)
    )

    parallel_chain = RunnableParallel(genres=genre_chain, personality=personality_chain)
    return parallel_chain.invoke({"books": read_titles})

def get_recommendations(read_titles: list) -> RecommendationOutput:
    """Genre → Recommendations sequential chain.
    First identifies top genres, then uses them to give more targeted recommendations.
    """
    _init_llms()
    genre_parser = PydanticOutputParser(pydantic_object=GenreOutput)
    rec_parser = PydanticOutputParser(pydantic_object=RecommendationOutput)

    genre_chain = (
        RunnableLambda(lambda x: {"books": x["books"], "format_instructions": genre_parser.get_format_instructions()})
        | genre_analysis_prompt | llm_genre | make_safe_parser(GenreOutput)
    )

    def build_rec_input(genre_output: GenreOutput) -> dict:
        top_genres = ", ".join([g.genre for g in genre_output.genres])
        return {
            "books": read_titles,
            "top_genres": top_genres,
            "format_instructions": rec_parser.get_format_instructions()
        }

    sequential_chain = genre_chain | RunnableLambda(build_rec_input) | recommendation_prompt | llm_recommendations | make_safe_parser(RecommendationOutput)
    return sequential_chain.invoke({"books": read_titles})

def get_review_analysis(books_with_reviews: list) -> ReviewAnalysis:
    _init_llms()
    parser = PydanticOutputParser(pydantic_object=ReviewAnalysis)
    chain = review_prompt | llm_reviews | make_safe_parser(ReviewAnalysis)
    max_books = _max_books_within_token_limit(books_with_reviews)
    return chain.invoke({
        "books_with_reviews": books_with_reviews[:max_books],
        "format_instructions": parser.get_format_instructions()
    })