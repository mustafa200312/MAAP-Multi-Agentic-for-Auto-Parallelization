from LLMs.llms import llm
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field, BaseModel
from typing import List, Optional, Literal

class AppliedChange(BaseModel):
    start_line: int = Field(..., description="Loop start line modified")
    end_line: int = Field(..., description="Loop end line modified")
    backend: Literal["processes", "threads"] = Field(..., description="joblib prefer backend used")
    note: Optional[str] = Field(None, description="Short explanation of what changed")

class OutputModel(BaseModel):
    modified_code: str = Field(..., description="Full modified code after implementation.")
    parallelizable: bool = Field(..., description="True if any loop was parallelized.")
    changes: List[AppliedChange] = Field(default_factory=list, description="List of applied parallelization edits.")

system_prompt = r"""
You are a Python Parallelization Implementer.

Goal:
Refactor the provided code to parallelize identified safe candidates (loops or independent tasks) to run concurrently.

Supported Backends:
1. `joblib` (Preferred for loops): `from joblib import Parallel, delayed`
2. `concurrent.futures` (Preferred for independent task graphs): `from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor`

You will receive:
- Original code
- An analysis report describing candidates and parallelization guidance

Rules:
1) Only parallelize regions explicitly marked safe/parallelizable in the analysis.
2) Preserve semantics exactly (same outputs, same order where required, no unsafe shared writes).
3) Implementation Patterns:
   A. Loop Map (Joblib):
      - Extract body to `_worker`.
      - Use `Parallel(n_jobs=..., prefer="processes")` for CPU or `prefer="threads"` for I/O.
   B. Task Graph (Futures):
      - Identify independent function calls (e.g., `val_a = heavy_a()`, `val_b = heavy_b()`).
      - Use `ThreadPoolExecutor` (for I/O) or `ProcessPoolExecutor` (for CPU).
      - Submit tasks -> `future = executor.submit(func, args)`.
      - Gather results -> `val_a = future_a.result()`.
4) Choosing Backend:
   - CPU-bound (math, heavy logic) -> Process-based (`n_jobs=-1, prefer="processes"` or `ProcessPoolExecutor`).
   - I/O-bound (network, sleep, disk) -> Thread-based (`n_jobs=4, prefer="threads"` or `ThreadPoolExecutor`).
5) Safety:
   - No shared mutation without locks (and avoid locks if possible).
   - Verify inputs to parallel blocks are independent.

Output requirements:
- Return the full modified code.
- If no safe parallelization is possible, return original code with parallelizable=False.
"""

user_prompt = """
Refactor the following code based on the analysis.

ORIGINAL CODE:
{source_code}

ANALYSIS REPORT:
{analysis_report}

Constraints:
- Apply changes only to the regions referenced in the analysis report.
- If the analysis report does not explicitly say a candidate is safe, do not parallelize it.
- Keep behavior identical.
- Keep behavior identical, including ordering if relevant.

Return the complete modified code.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", user_prompt),
])

implementer_agent = prompt | llm.with_structured_output(OutputModel)