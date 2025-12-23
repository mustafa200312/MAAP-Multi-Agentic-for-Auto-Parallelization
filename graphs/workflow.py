from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import subprocess
import os
import sys

# Import agents
from agents.analyser import dependencies_detector_agent
from agents.implementer import implementer_agent
from agents.validator import validator_agent
from agents.orchestrator import orchestrator_agent
from agents.ast_utils import analyze_code_ast

class AgentState(TypedDict):
    source_code: str
    analysis_report: str
    modified_code: str
    validation_script: str
    validation_output: str
    is_valid: bool
    iterations: int
    messages: List[str]

def analyzer_node(state: AgentState):
    print("--- DETECTING DEPENDENCIES (AST + LLM) ---")
    ast_report = analyze_code_ast(state["source_code"])
    result = dependencies_detector_agent.invoke({
        "source_code": state["source_code"],
        "ast_report": ast_report
    })
    return {"analysis_report": f"AST Report:\n{ast_report}\n\nAgent Analysis:\n{result.output}"}

def implementer_node(state: AgentState):
    print("--- IMPLEMENTING PARALLELISM ---")
    result = implementer_agent.invoke({
        "source_code": state["source_code"], 
        "analysis_report": state["analysis_report"]
    })
    return {"modified_code": result.modified_output}

def validator_node(state: AgentState):
    print("--- VALIDATING IMPLEMENTATION ---")
    # 1. Generate validation script
    result = validator_agent.invoke({
        "source_code": state["source_code"],
        "modified_code": state["modified_code"]
    })
    
    script_content = result.validation_script_code
    # Basic cleanup if markdown is included
    if "```python" in script_content:
        script_content = script_content.split("```python")[1].split("```")[0]
    elif "```" in script_content:
        script_content = script_content.split("```")[1].split("```")[0]
    
    # Create temp dir if it doesn't exist (just in case)
    TEMP_DIR = "temp_env"
    os.makedirs(TEMP_DIR, exist_ok=True)

    # Write source and modified code to temp files expected by the script
    with open(os.path.join(TEMP_DIR, "original.py"), "w", encoding="utf-8") as f:
        f.write(state["source_code"])
        
    with open(os.path.join(TEMP_DIR, "refactored.py"), "w", encoding="utf-8") as f:
        f.write(state["modified_code"])

    # Write script to file
    script_path = os.path.join(TEMP_DIR, "validation_script.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)
    
    # Execute script
    try:
        # Run inside the TEMP_DIR so imports work naturally
        # Force UTF-8 encoding for subprocess output to avoid cp1252 errors on Windows
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        proc = subprocess.run(
            [sys.executable, "validation_script.py"], 
            cwd=TEMP_DIR,
            capture_output=True, 
            text=True, 
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=30
        )
        output = proc.stdout + "\n" + proc.stderr
        is_valid = "Validation Passed" in output
    except Exception as e:
        output = str(e)
        is_valid = False
        
    return {"validation_output": output, "is_valid": is_valid, "iterations": state.get("iterations", 0) + 1}

def orchestrator_node(state: AgentState):
    # Determine next step
    # This node might be redundant if we use conditional edges directly, 
    # but strictly following the prompt plan:
    return {}

def router(state: AgentState):
    if state.get("is_valid"):
        return "end"
    if state.get("iterations", 0) > 3:
        return "end"
    return "implementer"

workflow = StateGraph(AgentState)

workflow.add_node("analyzer", analyzer_node)
workflow.add_node("implementer", implementer_node)
workflow.add_node("validator", validator_node)

workflow.set_entry_point("analyzer")
workflow.add_edge("analyzer", "implementer")
workflow.add_edge("implementer", "validator")

workflow.add_conditional_edges(
    "validator",
    router,
    {
        "implementer": "implementer",
        "end": END
    }
)

app = workflow.compile()
