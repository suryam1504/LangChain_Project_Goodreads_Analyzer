import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import traceback
import streamlit as st
from langchain_core.exceptions import OutputParserException
from utils.book_analyzer import fetch_user_books, get_reading_summary, get_genre_and_personality, get_recommendations, get_review_analysis
from utils.book_chat import get_chat_response

# ── Cached wrappers (ttl=1 hour) ─────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def cached_fetch_user_books(gr_id: int):
    return fetch_user_books(gr_id)

@st.cache_data(ttl=3600, show_spinner=False)
def cached_reading_summary(books_tuple: tuple, num_read: int, currently_reading: tuple, style: str, length: str):
    return get_reading_summary(list(books_tuple), num_read, list(currently_reading), style=style, length=length)

@st.cache_data(ttl=3600, show_spinner=False)
def cached_genre_and_personality(books_tuple: tuple) -> dict:
    """Runs genre analysis and personality card in parallel. Returns both as plain dicts."""
    result = get_genre_and_personality(list(books_tuple))
    return {
        "genres": [g.model_dump() for g in result["genres"].genres],
        "personality": result["personality"].model_dump()
    }

@st.cache_data(ttl=3600, show_spinner=False)
def cached_review_analysis(reviews_tuple: tuple):
    return get_review_analysis(list(reviews_tuple)).model_dump()

@st.cache_data(ttl=3600, show_spinner=False)
def cached_recommendations(books_tuple: tuple):
    result = get_recommendations(list(books_tuple))
    return [r.model_dump() for r in result.recommendations]

st.set_page_config(page_title="Book Analyzer", page_icon="📚", initial_sidebar_state="expanded")

st.title("📚 Book Analyzer")
st.caption("Enter a Goodreads profile link to analyze your reading personality.")
st.caption("If you don't have one and are just trying out this website, you can use this sample profile: https://www.goodreads.com/user/show/142334643-suryam-gupta")

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
            for key in ["personality", "genre_result", "review", "recs", "chat_history"]:
                st.session_state.pop(key, None)
            with st.spinner("Fetching your books..."):
                st.session_state.user_data = cached_fetch_user_books(gr_id)
            st.session_state.gr_id = gr_id

user_data = st.session_state.get("user_data")

if user_data:
    st.success(f"Found {user_data['num_read_books']} books!")

    # ── Quick debug view ──────────────────────────────────
    with st.expander("📖 All the books you have read!"):
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

    # ── Personality Card + Genre Analysis ────────────────
    st.subheader("🧠📊 Your Reader Personality & Top Genres")
    if st.button("Generate Personality & Genres"):
        try:
            with st.spinner("Analysing personality & genres in parallel..."):
                combined = cached_genre_and_personality(tuple(user_data["read_titles"]))
                st.session_state.personality = combined["personality"]
                st.session_state.genre_result = combined["genres"]
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

    if st.session_state.get("genre_result"):
        st.markdown("#### Top Genres")
        for genre in st.session_state.genre_result:
            with st.expander(f"**{genre['genre']}** — {len(genre['books'])} books"):
                st.caption(genre['reason'])
                for book in genre['books']:
                    st.markdown(f"- {book}")

    st.divider()

    # ── Review Analysis ───────────────────────────────────
    st.subheader("📝 What Your Reviews Reveal")
    if not user_data["books_with_reviews"]:
        st.info("✍️ Looks like you're more of a silent reader — no reviews yet. The books have opinions about you too, you know. Try leaving one sometime.")
    else:
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
            with st.spinner("Finding your next reads based on your top genres..."):
                st.session_state.recs = cached_recommendations(tuple(user_data["read_titles"]))
        except OutputParserException:
            traceback.print_exc()
            st.error("Parsing error — try again.")

    if st.session_state.get("recs"):
        for rec in st.session_state.recs:
            with st.expander(f"**{rec['title']}** by {rec['author']} — *{rec['mood']}*"):
                st.write(rec['reason'])
                st.caption(f"Similar to: {rec['similar_to']}")


# ── Sidebar Chat ─────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.markdown("### 💬 Book Bot")
    _user_data = st.session_state.get("user_data")
    if not _user_data:
        st.caption("Load a Goodreads profile first.")
    else:
        st.caption(f"Chatting about {_user_data['num_read_books']} books.")

        with st.container(height=400, border=False):
            if not st.session_state.chat_history:
                st.caption("💡 Ask me anything about your reading history!")
                st.caption("*Try asking:*")
                st.caption("• Which books did I give 5 stars?")
                st.caption("• Who is my most-read author?")
                st.caption("• What did I write in my review of [book]?")
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

        if st.button("🗑️ Clear", key="chat_clear"):
            st.session_state.chat_history = []
            st.rerun()

        if user_msg := st.chat_input("Ask about your books…", key="sidebar_chat_input"):
            history_so_far = st.session_state.chat_history.copy()
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            with st.spinner("..."):
                response = get_chat_response(user_msg, history_so_far, _user_data)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()