"""
C Code Analyzer Agent for OpenMP parallelization.
Analyzes C code to identify loops suitable for OpenMP parallelization.
"""

from LLMs.llms import llm
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field, BaseModel


class CAnalyzerOutput(BaseModel):
    output: str = Field(..., description="Detailed analysis of parallelization opportunities (loops and sections) in the C code.")
    parallelizable_loops: int = Field(..., description="Number of loops that can be parallelized.")
    parallelizable_sections: int = Field(False, description="Number of independent sections groups that can be parallelized.")


system_prompt = r"""You are an expert C Code Analyzer for OpenMP.
Identify parallelization opportunities in C code and categorize them into:

1. **loop_map** (Data Parallelism):
   - Strategy: `#pragma omp parallel for`
   - Target: `for` loops with independent iterations. Check for reductions (e.g., `sum += ...`) or private variables.

2. **task_graph** (Task Parallelism):
   - Strategy: `#pragma omp parallel sections`
   - Target: Independent code blocks or function calls that can run concurrently.

3. **vectorize** (SIMD):
   - Strategy: `#pragma omp simd`
   - Target: Small inner loops or element-wise operations on arrays.

For each, analyze dependencies/conflicts and suggest the specific OpenMP pragmas.
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

# c_dependencies_detector_agent = prompt | gpt_oss_llm.with_structured_output(CAnalyzerOutput)

from langchain_core.runnables import RunnableLambda

def extract_analysis(msg):
    # Extract loops and sections count from the text if possible, else default to 0
    content = msg.content
    
    # Simple heuristic to find counts in the text
    loops = content.count("#pragma omp parallel for")
    sections = content.count("#pragma omp parallel sections")
    
    return CAnalyzerOutput(
        output=content,
        parallelizable_loops=loops,
        parallelizable_sections=sections
    )

c_dependencies_detector_agent = prompt | llm | RunnableLambda(extract_analysis)
