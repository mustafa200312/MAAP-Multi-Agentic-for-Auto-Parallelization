from LLMs.azure_models import gpt_oss_llm
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field, BaseModel

class output_model(BaseModel):
    output: str = Field(..., description="The output response to the user request.")

system_prompt = r"""
"""

user_prompt = """
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", user_prompt),
])

agent = prompt | gpt_oss_llm.with_structured_output(output_model)