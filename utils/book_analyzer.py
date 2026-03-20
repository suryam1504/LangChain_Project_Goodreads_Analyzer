from llm import get_llm
# from langchain.prompts import ChatPromptTemplate

print(2+2)

llm = get_llm(temperature=0.7, max_completion_tokens=1024)

llm.invoke("What is the capital of France?")