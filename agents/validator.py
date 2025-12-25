from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from LLMs.llms import llm

class ValidationScript(BaseModel):
    script: str = Field(..., description="The executable Python validation script.")


system_prompt = r"""
You are a Python Validation Engineer.
Task: Write a python script to validate refactored code against original code.

Input files in CWD: `original.py`, `refactored.py`.

Requirements:
1. Use `importlib` to import `original` and `refactored`.
2. Wrap execution in Try/Except to catch runtime errors.
3. Compare outputs (handle float tolerance if needed).
4. Measure execution time.
5. ALWAYS print valid JSON at the very end (even on error):
{{"is_correct": bool, "original_time": float, "refactored_time": float, "speedup": float, "error": "string or null"}}
If error occurs, set is_correct=false and error=str(e).
6. Use `if __name__ == "__main__":` block.
7. If code uses `input()`, MOCK IT using `unittest.mock.patch('builtins.input', side_effect=...)` to prevent blocking. Provide reasonable dummy values.
"""

user_prompt = """
Write validation script for:

ORIGINAL:
{original_code}

REFACTORED:
{refactored_code}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", user_prompt),
])

# Use standard structured output but validation might be failing on large inputs
validator_agent = prompt | llm.with_structured_output(ValidationScript)