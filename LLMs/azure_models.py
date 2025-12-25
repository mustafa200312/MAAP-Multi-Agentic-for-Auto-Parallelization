from langchain_mistralai import ChatMistralAI
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatMistralAI(
    model=os.getenv("model"), 
    api_key=os.getenv("api_key"),
    max_retries=3,
    timeout=300
)

gpt_oss_llm = llm
