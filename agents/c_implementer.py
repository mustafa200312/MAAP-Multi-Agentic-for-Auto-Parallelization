"""
C Code Implementer Agent for OpenMP parallelization.
Transforms C code to use OpenMP pragmas for parallel execution.
Uses the same structured output format as the Python implementer.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from LLMs.llms import llm

# Structured change tracking (mirrors Python's AppliedChange)
class CAppliedChange(BaseModel):
    start_line: int = Field(..., description="Loop start line modified")
    end_line: int = Field(..., description="Loop end line modified")
    pragma: Literal["parallel_for", "parallel_for_reduction", "parallel_sections", "simd"] = Field(
        ..., description="OpenMP pragma applied"
    )
    note: Optional[str] = Field(None, description="Short explanation of what changed")

class CImplementerOutput(BaseModel):
    modified_code: str = Field(..., description="Full modified C code after implementation.")
    parallelizable: bool = Field(..., description="True if any loop was parallelized.")
    changes: List[CAppliedChange] = Field(default_factory=list, description="List of applied parallelization edits.")


system_prompt = r"""You are a C/OpenMP Parallelization Implementer.

Goal:
Refactor the provided C code to parallelize identified safe candidates using OpenMP pragmas.

Supported Pragmas:
1. `#pragma omp parallel for` - For independent loop iterations
2. `#pragma omp parallel for reduction(op:var)` - For accumulator patterns
3. `#pragma omp parallel sections` - For independent code blocks
4. `#pragma omp simd` - For SIMD vectorization of inner loops

You will receive:
- Original C code
- An analysis report describing candidates and parallelization guidance

Rules:
1) Only parallelize regions explicitly marked safe/parallelizable in the analysis.
2) Preserve semantics exactly (same outputs, same order where required).
3) Implementation Patterns:
   A. Loop Map:
      - Add `#pragma omp parallel for` before the for loop.
      - Do NOT use `private()` for variables declared inside the loop.
   B. Reduction:
      - Add `#pragma omp parallel for reduction(+:sum)` for accumulator patterns.
   C. Task Graph:
      - Wrap in `#pragma omp parallel sections` with `#pragma omp section` for each block.
   D. Vectorization:
      - Add `#pragma omp simd` for inner loops suitable for SIMD.
4) Always add `#include <omp.h>` at the top.
5) Safety:
   - Do NOT use `private()` clauses for loop-local variables.
   - Variables declared inside the loop are automatically private.

Output requirements:
- Return the full modified C code.
- If no safe parallelization is possible, return original code with parallelizable=False.
"""

user_prompt = """
Refactor the following C code based on the analysis.

ORIGINAL CODE:
```c
{source_code}
```

ANALYSIS REPORT:
{analysis_report}

Constraints:
- Apply changes only to the regions referenced in the analysis report.
- If the analysis report does not explicitly say a candidate is safe, do not parallelize it.
- Keep behavior identical.

Return the complete modified C code.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", user_prompt),
])

# Use structured output with the LLM
c_implementer_agent = prompt | llm.with_structured_output(CImplementerOutput)
