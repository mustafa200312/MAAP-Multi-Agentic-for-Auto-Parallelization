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
1. Compiles the original C code (without OpenMP)
2. Compiles the parallelized C code (with OpenMP flags)
3. Runs both executables with the same inputs
4. Compares the outputs for correctness
5. Measures and compares execution times

The validation script should:
1. Save the original C code to `original.c`
2. Save the parallel C code to `parallel.c`
3. Compile using subprocess:
   - Original: `gcc -O2 -o original original.c -lm`
   - Parallel: `gcc -O2 -fopenmp -o parallel parallel.c -lm`
4. Run both executables and capture stdout
5. Compare outputs (handle floating-point tolerance if needed)
6. Print timing comparison
7. Print "Validation Passed" if outputs match, "Validation Failed" otherwise

Important:
- Handle compilation errors gracefully
- Set appropriate timeout for execution
- Use only standard ASCII characters in print statements
- The script will be executed in a temp directory
- On Windows, executable names should be `original.exe` and `parallel.exe`

You are NOT running the code, only WRITING the Python test script.
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

c_validator_agent = prompt | gpt_oss_llm.with_structured_output(CValidatorOutput)
