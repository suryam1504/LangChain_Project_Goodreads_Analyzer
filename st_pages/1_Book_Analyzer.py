import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import traceback
import streamlit as st
from langchain_core.exceptions import OutputParserException
from utils.book_analyzer import fetch_user_books, get_reading_summary, get_genre_analysis, get_personality_card, get_recommendations, get_review_analysis

# ── Cached wrappers (ttl=1 hour) ─────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def cached_fetch_user_books(gr_id: int):
    return fetch_user_books(gr_id)

@st.cache_data(ttl=3600, show_spinner=False)
def cached_reading_summary(books_tuple: tuple, num_read: int, currently_reading: tuple, style: str, length: str):
    return get_reading_summary(list(books_tuple), num_read, list(currently_reading), style=style, length=length)

@st.cache_data(ttl=3600, show_spinner=False)
def cached_personality_card(books_tuple: tuple):
    return get_personality_card(list(books_tuple)).model_dump()

@st.cache_data(ttl=3600, show_spinner=False)
def cached_genre_analysis(books_tuple: tuple):
    result = get_genre_analysis(list(books_tuple))
    return [g.model_dump() for g in result.genres]

@st.cache_data(ttl=3600, show_spinner=False)
def cached_review_analysis(reviews_tuple: tuple):
    return get_review_analysis(list(reviews_tuple)).model_dump()

@st.cache_data(ttl=3600, show_spinner=False)
def cached_recommendations(books_tuple: tuple):
    result = get_recommendations(list(books_tuple))
    return [r.model_dump() for r in result.recommendations]

st.set_page_config(page_title="Book Analyzer", page_icon="📚")
st.title("📚 Book Analyzer")
st.caption("Enter a Goodreads profile link to analyze your reading personality.")

gr_link = st.text_input("Goodreads Profile Link", placeholder="https://www.goodreads.com/user/show/142334643-suryam-gupta")

col1, col2 = st.columns(2)
with col1:
    style = st.selectbox("Summary Style", [
        "Warm and Witty",
        "A Small Baby",
        "Ahoy Pirate!",
        "Roast Master"
    ])

STYLE_PROMPTS = {
    "Warm and Witty": "A Warm and Witty person",
    "A Small Baby": "A Small Baby: You do baby talk, make cute observations, and spelling mistakes",
    "Ahoy Pirate!": "Ahoy Pirate!: Pirate talk, lots of 'Arrr's and 'Matey''s, and references to the sea and adventure",
    "Roast Master": "Roast Master: You talk negative, do not appraise user at all, negate the fact that they have read many books, and make fun of their reading choices in a lighthearted way",
}

with col2:
    length = st.selectbox("Summary Length", [
        "Short (1 paragraph)",
        "Long (2-3 paragraphs)"
    ])

if st.button("Analyze", type="primary"):
    if not gr_link.strip():
        st.warning("Please enter a Goodreads profile link.")
    else:
        # Extract numeric ID from the URL
        try:
            gr_id = int(gr_link.strip().split("/")[-1].split("-")[0])
        except ValueError:
            st.error("Please enter only a valid Goodreads profile link. e.g. https://www.goodreads.com/user/show/142334643-suryam-gupta")
            st.stop()

        # Only re-fetch if the user ID changed
        if st.session_state.get("gr_id") != gr_id:
            for key in ["personality", "genre_result", "review", "recs"]:
                st.session_state.pop(key, None)
            with st.spinner("Fetching your books..."):
                st.session_state.user_data = cached_fetch_user_books(gr_id)
            st.session_state.gr_id = gr_id

user_data = st.session_state.get("user_data")

if user_data:
    st.success(f"Found {user_data['num_read_books']} books!")

    # ── Quick debug view ──────────────────────────────────
    with st.expander("📖 Raw data (debug)"):
        st.write(f"**Read titles ({len(user_data['read_titles'])}):**")
        st.write(user_data["read_titles"])
        st.write(f"**Currently reading:** {user_data['currently_reading_titles']}")
        st.write(f"**Books with reviews:** {len(user_data['books_with_reviews'])}")

    # ── Reading Summary ───────────────────────────────────
    try:
        with st.spinner("Generating your reader summary..."):
            summary = cached_reading_summary(
                tuple(user_data["read_titles"]),
                user_data["num_read_books"],
                tuple(user_data["currently_reading_titles"]),
                style=STYLE_PROMPTS[style],
                length=length
            )
        st.subheader("🎭 Your Reader Summary")
        st.write(summary)
    except OutputParserException:
        traceback.print_exc()
        st.error("Parsing error generating summary — try again.")

    st.divider()

    # ── Personality Card ──────────────────────────────────
    st.subheader("🧠 Your Reader Personality")
    if st.button("Generate Personality Card"):
        try:
            with st.spinner("Generating your reader personality..."):
                st.session_state.personality = cached_personality_card(tuple(user_data["read_titles"]))
        except OutputParserException:
            traceback.print_exc()
            st.error("Parsing error — try again.")

    if st.session_state.get("personality"):
        personality = st.session_state.personality
        st.markdown(f"### {personality['personality_type']}")
        st.write(personality['description'])
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Traits**")
            for trait in personality['traits']:
                st.markdown(f"- {trait}")
            st.markdown(f"**Guilty Pleasure:** {personality['guilty_pleasure']}")
            st.markdown(f"**Signature Author:** {personality['signature_author']}")
        with col_b:
            st.info(f"💊 Diagnosis: *{personality['diagnosis']}*")

    st.divider()

    # ── Genre Analysis ────────────────────────────────────
    st.subheader("📊 Your Top Genres")
    if st.button("Analyse My Genres"):
        try:
            with st.spinner("Analysing your genres..."):
                st.session_state.genre_result = cached_genre_analysis(tuple(user_data["read_titles"]))
        except OutputParserException:
            traceback.print_exc()
            st.error("Parsing error — try again.")

    if st.session_state.get("genre_result"):
        for genre in st.session_state.genre_result:
            with st.expander(f"**{genre['genre']}** — {len(genre['books'])} books"):
                st.caption(genre['reason'])
                for book in genre['books']:
                    st.markdown(f"- {book}")

    st.divider()

    # ── Review Analysis ───────────────────────────────────
    if user_data["books_with_reviews"]:
        st.subheader("📝 What Your Reviews Reveal")
        if st.button("Analyse My Reviews"):
            try:
                with st.spinner("Analysing your reviews..."):
                    st.session_state.review = cached_review_analysis(tuple(frozenset(b.items()) for b in user_data["books_with_reviews"]))
            except OutputParserException:
                traceback.print_exc()
                st.error("Parsing error — try again.")

        if st.session_state.get("review"):
            review = st.session_state.review
            st.markdown(f"**{review['reviewer_type']}**")
            row1_c, row1_d = st.columns(2)
            with row1_c:
                st.markdown("**Rating Style**")
                st.write(review['rating_style'])
            with row1_d:
                st.markdown("**Most Enthusiastic About**")
                st.write(review['most_enthusiastic_about'])

            row2_c, row2_d = st.columns(2)
            with row2_c:
                st.markdown("**Review Voice**")
                st.write(review['review_personality'])
            with row2_d:
                st.markdown("**Most Critical About**")
                st.write(review['most_critical_about'])
            st.info(f"🔍 Hidden Pattern: *{review['hidden_pattern']}*")

        st.divider()

    # ── Recommendations ───────────────────────────────────
    st.subheader("🔮 What to Read Next")
    if st.button("Recommend Me Books"):
        try:
            with st.spinner("Finding your next reads..."):
                st.session_state.recs = cached_recommendations(tuple(user_data["read_titles"]))
        except OutputParserException:
            traceback.print_exc()
            st.error("Parsing error — try again.")

    if st.session_state.get("recs"):
        for rec in st.session_state.recs:
            with st.expander(f"**{rec['title']}** by {rec['author']} — *{rec['mood']}*"):
                st.write(rec['reason'])
                st.caption(f"Similar to: {rec['similar_to']}")


