"""
C Code Implementer Agent for OpenMP parallelization.
Transforms C code to use OpenMP pragmas for parallel execution.
"""

from LLMs.llms import llm
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field, BaseModel


class CImplementerOutput(BaseModel):
    modified_output: str = Field(..., description="The complete modified C code with OpenMP pragmas added.")
    parallelizable: bool = Field(..., description="Indicates if the code was successfully parallelized.")
    changes_summary: str = Field(..., description="Summary of the OpenMP changes made to the code.")


system_prompt = r"""You are a C/OpenMP Parallelization Expert.
Refactor the provided C code to use OpenMP for parallel execution based on the analysis report.

Implementation Strategies:
1. **loop_map**: Use `#pragma omp parallel for`.
   - Handle reductions: `reduction(op:var)`
   - Ensure `schedule(dynamic)` if workload is uneven.

2. **task_graph**: Use `#pragma omp parallel sections`.
   - Wrap independent blocks in `#pragma omp section`.

3. **vectorize**: Use `#pragma omp simd`.
   - For small inner loops without dependencies.

Guidelines:
1. Include `#include <omp.h>`.
2. Ensure code is syntactically correct and compilable.
3. Preserve original logic and results.
4. **CRITICAL**: Do NOT use `private(...)` clauses. Variables declared inside the loop (like `for(int i=0; ...)` or `double val = ...;`) are automatically private in OpenMP. Adding `private()` for these causes compilation errors.

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

c_implementer_agent = prompt | llm | RunnableLambda(extract_code)
