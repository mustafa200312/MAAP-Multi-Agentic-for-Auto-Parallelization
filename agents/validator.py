from LLMs.azure_models import gpt_oss_llm
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field, BaseModel

class output_model(BaseModel):
    validation_script_code: str = Field(..., description="The executable Python code for the validation script.")
    explanation: str = Field(..., description="Explanation of the validation strategy.")

system_prompt = r"""You are a Code Validation Specialist.
Your task is to create a validation script that compares the execution of the original code and the refactored parallel code.
The validation script should:
1. Import necessary functions from both versions (or run them if they are scripts).
2. Measure the execution time of both.
3. Compare the outputs to ensure they are identical.
4. Print "Validation Passed" or "Validation Failed" along with timing results.
5. Use ONLY standard ASCII characters in your print statements. Do not use non-breaking hyphens or other special symbols.

You are NOT running the code, only WRITING the test script that will be run by the system.
"""

user_prompt = """
Generate a validation script for:

Original Code:
{source_code}

Refactored Code:
{modified_code}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", user_prompt),
])

validator_agent = prompt | gpt_oss_llm.with_structured_output(output_model)