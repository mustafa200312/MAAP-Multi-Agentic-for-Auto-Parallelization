from langchain_openai import AzureChatOpenAI
import os

gpt_oss_llm = AzureChatOpenAI(
    azure_deployment=os.getenv("GPT_OSS_DEPLOYMENT_NAME"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    timeout=300,
    max_retries=3,
)