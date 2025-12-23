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
Your task is to refactor the provided C code to use OpenMP for parallel execution.

Follow these guidelines strictly:

1. **Header Inclusion**: Add `#include <omp.h>` at the top of the file if not already present.

2. **Parallel For Loops**: For parallelizable loops, add appropriate pragmas:
   ```c
   #pragma omp parallel for [clauses]
   for (int i = 0; i < n; i++) {{ ... }}
   ```

3. **Reduction Clauses**: For accumulation patterns, use reduction:
   - `reduction(+:sum)` for summation
   - `reduction(*:product)` for products
   - `reduction(max:maxval)` for maximum
   - `reduction(min:minval)` for minimum

4. **Variable Scoping**:
   - Use `private()` for variables that should be local to each thread
   - Use `shared()` for variables explicitly shared (arrays, global state)
   - Use `firstprivate()` for private copies initialized from original value
   - Use `lastprivate()` when the final iteration's value is needed after the loop

5. **Schedule Clauses**: Add scheduling hints when appropriate:
   - `schedule(static)` for uniform workload
   - `schedule(dynamic)` for variable workload
   - `schedule(guided)` for decreasing chunk sizes

6. **Nested Loops**: Consider using `collapse(n)` for perfectly nested loops.

7. **Critical Sections**: Use `#pragma omp critical` for unavoidable shared state updates.

8. **Code Correctness**: 
   - Preserve the original logic exactly
   - Ensure the parallelized version produces identical results
   - Do NOT parallelize loops with true data dependencies

Output ONLY the complete, compilable C code with OpenMP pragmas.
Do NOT include markdown code blocks or explanations in the modified_output field.
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

c_implementer_agent = prompt | gpt_oss_llm.with_structured_output(CImplementerOutput)
