from LLMs.azure_models import gpt_oss_llm
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field, BaseModel

class output_model(BaseModel):
    output: str = Field(..., description="The output response to the user request.")

system_prompt = r"""You are an expert Python Code Analyzer. 
Your goal is to identify loops and potentially parallelizable sections in the provided code.
Look for:
1. `for` loops that iterate over a large range or collection.
2. Iterations that are independent of each other (no carried state).
3. Computationally intensive operations within the loop.

Output your findings clearly.
"""

user_prompt = """
Analyze the following Python code for parallelization opportunities:
{source_code}

Static Analysis Report (AST):
{ast_report}

Use the AST report to locate exact line numbers of loops.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", user_prompt),
])

dependencies_detector_agent = prompt | gpt_oss_llm.with_structured_output(output_model)