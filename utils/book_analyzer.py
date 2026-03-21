# from llm import get_llm
# from piratetreads import get_books, get_all_books
# from book_prompts import reading_summary_prompt, genre_analysis_prompt, personality_prompt, recommendation_prompt, review_prompt
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.output_parsers import PydanticOutputParser
# from pydantic import BaseModel, Field
# from typing import Literal, List
# from pprint import pprint
# import json
# # from langchain_core.prompts import ChatPromptTemplate
#
# llm = get_llm(model="llama-3.3-70b-versatile", temperature=0.7, max_tokens=1024)
# str_parser = StrOutputParser()
#
# print("-"*150)
#
# # https://www.goodreads.com/user/show/142334643-suryam-gupta
# suryam_id = 142334643
#
# # gr_link = input("Enter the Goodreads profile link: ")
# # gr_id = (gr_link.split("/")[-1]).split("-")[0]
# # print(gr_id)
#
# suryam_read = get_books(suryam_id, "read")
# print(suryam_read.keys())
# num_read_books = suryam_read["count"]
# print(f"Number of books read: {num_read_books}")
# suryam_all = get_all_books(suryam_id)
# print(suryam_all.keys())
#
# all_read_book_titles = [book["book_title"] for book in suryam_all["read"]["books"]]
# currently_reading_titles = [book["book_title"] for book in suryam_all["currently_reading"]["books"]]
# # print(all_read_book_titles)
#
# # ============================================================
# # FUN SUMMARY
# # ============================================================
#
# summary_chain = reading_summary_prompt | llm | str_parser
# result = summary_chain.invoke({"books": all_read_book_titles, "num_read_books": num_read_books, "currently_reading": currently_reading_titles, "style": "ELI5 (Explain like I am 5)", "length": "short (1 or 2 paragraphs)"})
# print(result)
#
# # ============================================================
# # GENRE ANALYSIS
# # ============================================================
#
# class Genre(BaseModel):
#     genre: str = Field(description="Name of the genre")
#     books: List[str] = Field(description="Books from the reading list only — use exact titles as provided, no modifications")
#     reason: str = Field(description="One line explaining why these books share this genre")
#
# class GenreOutput(BaseModel):
#     genres: List[Genre] = Field(description="Top 5 genres with their corresponding books")
#
# genre_parser = PydanticOutputParser(pydantic_object=GenreOutput)
#
# # genre_chain = genre_analysis_prompt | llm | genre_parser
# # genre_result = genre_chain.invoke({"books": all_read_book_titles, "format_instructions": genre_parser.get_format_instructions()})
# # print(genre_result)
#
# # for i in range(len(genre_result.genres)):
# #     print(f"Genre: {genre_result.genres[i].genre}")
# #     print(f"Books: {genre_result.genres[i].books}")
# #     print(f"Reason: {genre_result.genres[i].reason}")
# #     print("-"*50)
#
# # ============================================================
# # PERSONALITY CARD
# # ============================================================
#
# class PersonalityCard(BaseModel):
#     personality_type: str = Field(description="Short catchy name for their reader personality e.g. 'The Reluctant Philosopher' or 'The Cozy Crime Addict'")
#     description: str = Field(description="2-3 sentence warm and witty description of their reading personality")
#     traits: List[str] = Field(description="Exactly 4 short punchy traits e.g. 'Cries at short novellas', 'Secretly loves comfort reads'")
#     guilty_pleasure: str = Field(description="The most unexpected or lighthearted book on their list that contrasts with their other reads")
#     signature_author: str = Field(description="The one author that defines their taste most based on frequency or book choices")
#     diagnosis: str = Field(description="One punchy witty one-liner that sums up their entire reader identity. Make it memorable.")
#
# personality_parser = PydanticOutputParser(pydantic_object=PersonalityCard)
#
# # personality_chain = personality_prompt | llm | personality_parser
# # personality_result = personality_chain.invoke({"books": all_read_book_titles, "format_instructions": personality_parser.get_format_instructions()})
# # print(personality_result)
# # print("-"*50)
# # pprint(personality_result.model_dump())
#
# # ============================================================
# # BOOK RECOMMENDATIONS
# # ============================================================
#
# class BookRecommendation(BaseModel):
#     title: str = Field(description="Title of the recommended book")
#     author: str = Field(description="Author of the recommended book")
#     reason: str = Field(description="2 sentence explanation of why this reader would love it, referencing specific books from their list")
#     similar_to: str = Field(description="One book from their reading list this recommendation is most similar to")
#     mood: str = Field(description="One word mood this book fits e.g. 'Melancholic', 'Thrilling', 'Comforting'")
#
# class RecommendationOutput(BaseModel):
#     recommendations: List[BookRecommendation] = Field(description="Exactly 5 book recommendations")
#
# recommendation_parser = PydanticOutputParser(pydantic_object=RecommendationOutput)
#
# # recommendation_chain = recommendation_prompt | llm | recommendation_parser
# # recommendation_result = recommendation_chain.invoke({"books": all_read_book_titles, "format_instructions": recommendation_parser.get_format_instructions()})
# # print(recommendation_result)
# # print("-"*50)
# # pprint(recommendation_result.model_dump())
#
# # ============================================================
# # REVIEW ANALYSIS
# # ============================================================
#
# books_with_reviews = [
#     {
#         "title": book["book_title"],
#         "author": book["book_author"],
#         "rating": book["rating"],
#         "avg_rating": book["avg_rating"],
#         "review": book["review_text"]
#     }
#     for book in suryam_all['read']['books']
#     if book["review_text"]  # only include books that have a review
# ]
#
# def get_max_books_within_token_limit(books: list, max_tokens: int = 11000) -> int:
#     total_tokens = 0
#     for i, book in enumerate(books):
#         book_tokens = len(str(book)) // 4
#         if total_tokens + book_tokens > max_tokens:
#             return i  # return the index where we stopped
#         total_tokens += book_tokens
#     return len(books)  # all books fit
#
# max_books = get_max_books_within_token_limit(books_with_reviews)
#
# class ReviewAnalysis(BaseModel):
#     rating_style: str = Field(description="Are they a harsh, generous, or balanced rater? 1-2 sentences with specific examples from their ratings")
#     review_personality: str = Field(description="How do they write reviews — emotional, analytical, brief, poetic? 1-2 sentences")
#     most_enthusiastic_about: str = Field(description="Book or author they seemed most positive about based on review text and rating combined")
#     most_critical_about: str = Field(description="Book or author they were hardest on")
#     hidden_pattern: str = Field(description="One interesting or surprising pattern found in their reviews or ratings — something they might not have noticed about themselves")
#     reviewer_type: str = Field(description="A fun one-liner label for their reviewer personality e.g. 'The Reluctant Star Giver' or 'The Emotional Analyst'")
#
# review_parser = PydanticOutputParser(pydantic_object=ReviewAnalysis)
#
# review_chain = review_prompt | llm | review_parser
# review_result = review_chain.invoke({"books_with_reviews": books_with_reviews[:max_books], "format_instructions": review_parser.get_format_instructions()})
# print(review_result)
# print("-"*50)
# pprint(review_result.model_dump())

# ============================================================
# FUNCTIONIZED CODE
# ============================================================

from utils.llm import get_llm
from utils.piratetreads import get_all_books
from utils.book_prompts import reading_summary_prompt, genre_analysis_prompt, personality_prompt, recommendation_prompt, review_prompt
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List

llm = get_llm()
str_parser = StrOutputParser()

# ── One LLM per task — spreads load across model rate limit buckets ──
# Model limits: TPM / TPD
llm_summary         = get_llm(model="llama-3.3-70b-versatile",                    max_tokens=1024)  # 8K TPM  / 200K TPD — analytical
llm_genre           = get_llm(model="llama-3.1-8b-instant",                       max_tokens=2048)  # 6K TPM  / 500K TPD — needs room for full JSON
llm_personality     = get_llm(model="moonshotai/kimi-k2-instruct",                max_tokens=1024)  # 10K TPM / 300K TPD — creative, witty
llm_recommendations = get_llm(model="qwen/qwen3-32b",                             max_tokens=1500)  # 6K TPM  / 500K TPD — strong reasoning, book knowledge
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
    chain = reading_summary_prompt | llm_summary | str_parser
    return chain.invoke({
        "books": read_titles,
        "num_read_books": num_read_books,
        "currently_reading": currently_reading_titles,
        "style": style,
        "length": length
    })

def get_genre_analysis(read_titles: list) -> GenreOutput:
    parser = PydanticOutputParser(pydantic_object=GenreOutput)
    chain = genre_analysis_prompt | llm_genre | parser
    return chain.invoke({
        "books": read_titles,
        "format_instructions": parser.get_format_instructions()
    })

def get_personality_card(read_titles: list) -> PersonalityCard:
    parser = PydanticOutputParser(pydantic_object=PersonalityCard)
    chain = personality_prompt | llm_personality | parser
    return chain.invoke({
        "books": read_titles,
        "format_instructions": parser.get_format_instructions()
    })

def get_recommendations(read_titles: list) -> RecommendationOutput:
    parser = PydanticOutputParser(pydantic_object=RecommendationOutput)
    chain = recommendation_prompt | llm_recommendations | parser
    return chain.invoke({
        "books": read_titles,
        "format_instructions": parser.get_format_instructions()
    })

def get_review_analysis(books_with_reviews: list) -> ReviewAnalysis:
    parser = PydanticOutputParser(pydantic_object=ReviewAnalysis)
    chain = review_prompt | llm_reviews | parser
    max_books = _max_books_within_token_limit(books_with_reviews)
    return chain.invoke({
        "books_with_reviews": books_with_reviews[:max_books],
        "format_instructions": parser.get_format_instructions()
    })

print(2+2)