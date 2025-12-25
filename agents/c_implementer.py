"""
C Code Implementer Agent for OpenMP parallelization.
Transforms C code to use OpenMP pragmas for parallel execution.
"""

from LLMs.azure_models import gpt_oss_llm
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field, BaseModel


class CImplementerOutput(BaseModel):
    modified_output: str = Field(..., description="The complete modified C code with OpenMP pragmas added.")
    parallelizable: bool = Field(..., description="Indicates if the code was successfully parallelized.")
    changes_summary: str = Field(..., description="Summary of the OpenMP changes made to the code.")


system_prompt = r"""You are a C/OpenMP Parallelization Expert.
Refactor the provided C code to use OpenMP for parallel execution based on the analysis report.

Guidelines:
1. Include `#include <omp.h>`.
2. Use `#pragma omp parallel for` for loops.
3. Use `#pragma omp parallel sections` for independent task blocks.
4. Ensure code is syntactically correct and compilable.
5. Preserve original logic and results.

Output ONLY the complete C code. Do NOT include explanations or markdown formatting in the code itself.
"""

user_prompt = """
Refactor the following C code to use OpenMP based on the analysis:

Original Code:
```c
{source_code}
```

Analysis Report:
{analysis_report}

Apply OpenMP parallelization to the identified loops. Return the COMPLETE modified C code.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", user_prompt),
])

# c_implementer_agent = prompt | gpt_oss_llm.with_structured_output(CImplementerOutput)

# Simple wrapper for compatibility with the graph caller which expects .modified_output
from langchain_core.runnables import RunnableLambda

def extract_code(msg):
    # Extract code from between ```c and ``` if present, otherwise take raw
    content = msg.content
    if "```c" in content:
        code = content.split("```c")[1].split("```")[0].strip()
    elif "```" in content:
        code = content.split("```")[1].split("```")[0].strip()
    else:
        code = content.strip()
    
    return CImplementerOutput(
        modified_output=code,
        parallelizable=True,
        changes_summary="OpenMP parallelization applied."
    )

c_implementer_agent = prompt | gpt_oss_llm | RunnableLambda(extract_code)
