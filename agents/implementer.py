from LLMs.azure_models import gpt_oss_llm
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field, BaseModel

class output_model(BaseModel):
    modified_output: str = Field(..., description="The modified code after implementation.")
    parallelizable: bool = Field(..., description="Indicates if the code can be parallelized.")

system_prompt = r"""You are a Python Parallelization Expert.
Your task is to refactor the provided code to use the `joblib` library for parallel execution.
Focus on the loops identified by the analysis.
Ensure:
1. The logic remains equivalent to the original sequential code.
2. Shared variables are handled correctly (or avoided).
3. Necessary imports (e.g., `from joblib import Parallel, delayed`) are added.
4. You verify that the changes are syntactically correct.
"""

user_prompt = """
Refactor the following code based on the analysis:
Original Code:
{source_code}

Analysis:
{analysis_report}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", user_prompt),
])

implementer_agent = prompt | gpt_oss_llm.with_structured_output(output_model)