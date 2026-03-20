from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()

def get_llm(temperature=0.7, max_tokens=1024):
    return ChatGroq(model="llama-3.3-70b-versatile", temperature=temperature, max_tokens=max_tokens)