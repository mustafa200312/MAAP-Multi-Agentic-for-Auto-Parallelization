"""
C Code Analyzer Agent for OpenMP parallelization.
Analyzes C code to identify loops suitable for OpenMP parallelization.
"""

from LLMs.azure_models import gpt_oss_llm
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field, BaseModel


class CAnalyzerOutput(BaseModel):
    output: str = Field(..., description="Detailed analysis of parallelization opportunities in the C code.")
    parallelizable_loops: int = Field(..., description="Number of loops that can be parallelized.")


system_prompt = r"""You are an expert C Code Analyzer specializing in OpenMP parallelization.
Your goal is to identify for-loops and potentially parallelizable sections in the provided C code.

For each loop, analyze:
1. Loop bounds and iteration pattern (is it countable/predictable?).
2. Data dependencies between iterations:
   - Read-after-write (RAW) dependencies
   - Write-after-read (WAR) dependencies  
   - Write-after-write (WAW) dependencies
3. Reduction operations (sum, product, min, max, etc.).
4. Variables that should be private vs shared.
5. Array access patterns (are indices independent?).
6. Function calls within the loop (are they thread-safe?).

OpenMP-specific considerations:
- Identify loops suitable for `#pragma omp parallel for`
- Suggest appropriate clauses: `reduction()`, `private()`, `shared()`, `schedule()`
- Flag potential race conditions or data dependencies that prevent parallelization
- Consider loop nesting and whether to use `collapse()` clause

Output your findings in a structured format with specific recommendations.
"""

user_prompt = """
Analyze the following C code for OpenMP parallelization opportunities:

```c
{source_code}
```

Static Analysis Report (AST):
{ast_report}

Use the AST report to validate your findings and provide specific OpenMP pragma suggestions.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", user_prompt),
])

c_dependencies_detector_agent = prompt | gpt_oss_llm.with_structured_output(CAnalyzerOutput)
