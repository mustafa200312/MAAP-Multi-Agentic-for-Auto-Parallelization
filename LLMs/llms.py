from langchain_mistralai import ChatMistralAI
import os

llm = ChatMistralAI(
    model=os.getenv("model"), 
    api_key=os.getenv("api_key"),
    max_retries=3,
    timeout=300,
    temperature=0.1
)