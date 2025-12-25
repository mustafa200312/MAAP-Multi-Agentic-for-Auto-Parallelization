"""
C Code Validator Agent for OpenMP parallelization.
Creates validation scripts to verify that parallelized C code produces correct results.
"""

from LLMs.azure_models import gpt_oss_llm
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field, BaseModel


class CValidatorOutput(BaseModel):
    validation_script_code: str = Field(..., description="A Python script that compiles and runs both C versions, then compares results.")
    explanation: str = Field(..., description="Explanation of the validation strategy.")
    compile_flags_original: str = Field(default="gcc -o original original.c", description="Compilation command for original code.")
    compile_flags_parallel: str = Field(default="gcc -fopenmp -o parallel parallel.c", description="Compilation command for parallel code.")


system_prompt = r"""You are a C/OpenMP Code Validation Specialist.
Your task is to create a Python validation script that:
1. Compiles the original C code: `gcc -O2 -o original original.c -lm`
2. Compiles the parallelized C code: `gcc -O2 -fopenmp -o parallel parallel.c -lm`
3. Runs both and compares outputs.

**Crucial Logic for Parallelism**:
Parallel execution (especially `sections` or `tasks`) often changes the order of output lines. 
The validation script **MUST** treat the output as a collection of lines and verify that the same lines are present in both, OR sort the lines before comparison. 
Do NOT do a simple string comparison if the order might be non-deterministic.

4. Print "Validation Passed" if results match (ignoring order if appropriate), "Validation Failed" otherwise.

5. **Mandatory Metrics Reporting**: 
   If validation passes, the script MUST print exactly one line in this format:
   `METRICS: {{"original_time": <float>, "parallel_time": <float>, "speedup": <float>}}`
   Use `time.perf_counter()` to measure the wall-clock execution time of the executables.

Output ONLY the Python script inside ```python ... ``` blocks.
"""

user_prompt = """
Generate a Python validation script for the following C codes:

Original C Code:
```c
{source_code}
```

Parallelized C Code (with OpenMP):
```c
{modified_code}
```

Create a Python script that validates the parallel implementation produces correct results.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", user_prompt),
])

# c_validator_agent = prompt | gpt_oss_llm.with_structured_output(CValidatorOutput)

from langchain_core.runnables import RunnableLambda

def extract_validator(msg):
    content = msg.content
    if "```python" in content:
        script = content.split("```python")[1].split("```")[0].strip()
    elif "```" in content:
        script = content.split("```")[1].split("```")[0].strip()
    else:
        script = content.strip()
        
    return CValidatorOutput(
        validation_script_code=script,
        explanation="Custom validation script generated."
    )

c_validator_agent = prompt | gpt_oss_llm | RunnableLambda(extract_validator)
