from LLMs.azure_models import gpt_oss_llm
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field, BaseModel

class output_model(BaseModel):
    next_agent: str = Field(..., description="The name of the next agent to handle the task.")
    next_steps: dict[str,bool] = Field(..., description="""A dictionary indicating the next steps to be taken. and
                                    whether they implement those steps or not.""")
    message: str = Field(..., description="A message providing context or instructions for the next agent.")

system_prompt = r"""You are the Orchestrator of the Auto-Parallelization System.
Your job is to determine the next step in the workflow based on the current state and results.

States:
- START: Go to 'analyzer' to analyze the code.
- ANALYZED: If parallelizable, go to 'implementer'. Else, 'finish'.
- IMPLEMENTED: Go to 'validator' to verify the changes.
- VALIDATED: If validation passed, 'finish'. If failed, go back to 'implementer' with feedback (or 'finish' if stuck).
"""

user_prompt = """
Determine the next agent.
Current State:
{state}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", user_prompt),
])

orchestrator_agent = prompt | gpt_oss_llm.with_structured_output(output_model)