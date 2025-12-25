"""
C Code Analyzer Agent for OpenMP parallelization.
Analyzes C code to identify loops suitable for OpenMP parallelization.
Uses the same structured output format as the Python analyzer.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from LLMs.llms import llm

# Shared types with Python analyzer (adapted for C/OpenMP)
CandidateType = Literal[
    "loop_map",       # #pragma omp parallel for
    "reduction",      # #pragma omp parallel for reduction(...)
    "task_graph",     # #pragma omp parallel sections
    "vectorize",      # #pragma omp simd
]

Parallelizable = Literal["yes", "maybe", "no"]

class CCandidate(BaseModel):
    id: str = Field(..., description="Unique id like C001")
    type: CandidateType = Field(..., description="Parallelization pattern classification")
    start_line: int = Field(..., description="1-indexed start line in source")
    end_line: int = Field(..., description="1-indexed end line in source")
    parallelizable: Parallelizable = Field(..., description="yes/maybe/no safety decision")
    reason: str = Field(..., description="Short explanation of the decision")
    blockers: List[str] = Field(default_factory=list, description="Concrete reasons preventing parallelization")
    recommendation: Optional[str] = Field(
        None,
        description="OpenMP pragma: parallel_for | parallel_for_reduction | parallel_sections | simd | none"
    )
    validation_checks: List[str] = Field(default_factory=list, description="Checks for validation agent")

class CAnalysisOutput(BaseModel):
    summary: str = Field(..., description="1-3 sentences summarizing main opportunities")
    candidates: List[CCandidate] = Field(default_factory=list, description="Detected candidate regions")


system_prompt = r"""You are an expert C Code Analyzer for OpenMP parallelization.

Goal:
Given C source code and an AST loop report with line ranges, identify code regions that can benefit from OpenMP parallelism.

You must output structured candidates with:
- location (start_line, end_line)
- type (loop_map | reduction | task_graph | vectorize)
- parallelizable (yes/maybe/no)
- reason, blockers
- recommendation label (parallel_for | parallel_for_reduction | parallel_sections | simd | none)
- validation_checks (2-5 items)

────────────────────────────────────────────────────────
1) What to detect (candidate types)

A) loop_map
Definition: a for loop where iterations are independent.
OpenMP: `#pragma omp parallel for`
Example:
  for(int i=0; i<N; i++) {{
      result[i] = compute(data[i]);
  }}

B) reduction
Definition: loop with carried state/accumulator updated each iteration.
OpenMP: `#pragma omp parallel for reduction(+:sum)`
Example:
  double sum = 0;
  for(int i=0; i<N; i++) {{
      sum += data[i];
  }}

C) task_graph
Definition: multiple independent code blocks that can run concurrently.
OpenMP: `#pragma omp parallel sections`
Example:
  #pragma omp parallel sections
  {{
      #pragma omp section
      compute_a();
      #pragma omp section
      compute_b();
  }}

D) vectorize
Definition: small inner loops or element-wise operations suitable for SIMD.
OpenMP: `#pragma omp simd`
Example:
  #pragma omp simd
  for(int i=0; i<N; i++) {{
      a[i] = b[i] * c[i];
  }}

────────────────────────────────────────────────────────
2) Decide if it is parallelizable

- yes: safe and straightforward
- maybe: possible after refactor (e.g., remove shared mutation)
- no: not safe (true dependency, required ordering)

Common blockers to list explicitly:
- loop-carried dependency: value from previous iteration used
- shared mutable state: writing to same memory location
- function calls with side effects: printf, file I/O, etc.
- pointer aliasing: uncertain memory access patterns

────────────────────────────────────────────────────────
3) Recommendation label (MUST choose one)

- parallel_for: independent iterations, use #pragma omp parallel for
- parallel_for_reduction: accumulator pattern, use reduction clause
- parallel_sections: independent blocks, use #pragma omp parallel sections  
- simd: inner loop vectorization, use #pragma omp simd
- none: no meaningful parallelism

────────────────────────────────────────────────────────
4) Output requirements

For each candidate region:
- Use AST report line numbers for loops when available.
- Provide: id, type, start_line, end_line, parallelizable, reason, blockers, recommendation, validation_checks.
- validation_checks must be concrete (e.g., "compare output with sequential", "verify no data races").

Do NOT write code. Output only structured data matching the schema.
"""

user_prompt = """
Analyze the following C code for OpenMP parallelization opportunities.

SOURCE CODE:
```c
{source_code}
```

Static Analysis Report (AST):
{ast_report}

Use the AST report to locate exact line numbers of loops.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", user_prompt),
])

c_dependencies_detector_agent = prompt | llm.with_structured_output(CAnalysisOutput)
