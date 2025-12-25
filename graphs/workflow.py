from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import subprocess
import os
import sys
from agents.validator import validator_agent
import json
from agents.analyser import dependencies_detector_agent
from agents.implementer import implementer_agent
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
    # result is now an AnalysisOutput pydantic object
    formatted_analysis = f"Analysis Summary: {result.summary}\n\nCandidates:\n"
    for cand in result.candidates:
        formatted_analysis += f"- [ID: {cand.id}] Type: {cand.type}, Lines: {cand.start_line}-{cand.end_line}, Parallelizable: {cand.parallelizable} ({cand.reason})\n"
        if cand.recommendation:
            formatted_analysis += f"  Recommendation: {cand.recommendation}\n"
    
    print("\n" + "="*50)
    print("ANALYSIS REPORT")
    print("="*50)
    print(formatted_analysis)
    print("="*50 + "\n")

    return {"analysis_report": f"AST Report:\n{ast_report}\n\nAgent Analysis:\n{formatted_analysis}"}

def implementer_node(state: AgentState):
    print("--- IMPLEMENTING PARALLELISM ---")
    result = implementer_agent.invoke({
        "source_code": state["source_code"], 
        "analysis_report": state["analysis_report"]
    })
    # result is now OutputModel
    print("Implementer Changes:")
    for change in result.changes:
        print(f"  - Lines {change.start_line}-{change.end_line}: Backend={change.backend} ({change.note})")
        
    return {"modified_code": result.modified_code}

def validator_node(state: AgentState):
    print("--- VALIDATING IMPLEMENTATION ---")
    
    TEMP_DIR = "temp_env"
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Always write the source/refactored files first
    original_path = os.path.join(TEMP_DIR, "original.py")
    refactored_path = os.path.join(TEMP_DIR, "refactored.py")
    
    with open(original_path, "w", encoding="utf-8") as f:
        f.write(state["source_code"])
        
    with open(refactored_path, "w", encoding="utf-8") as f:
        f.write(state["modified_code"])

    # Path to the script we will execute
    execution_script = ""

    print("Generating validation script via LLM...")
    result = validator_agent.invoke({
        "original_code": state["source_code"],
        "refactored_code": state["modified_code"]
    })
    execution_script = os.path.join(TEMP_DIR, "validate_agentic.py")
    with open(execution_script, "w", encoding="utf-8") as f:
        # result.script is the code
        f.write(result.script)

    # --- EXECUTION ---
    output_log = ""
    is_valid = False
    
    # Run the agent-generated script
    # It expects original.py and refactored.py in CWD
    try:
        cmd = [sys.executable, "validate_agentic.py"]
        proc = subprocess.run(
            cmd,
            cwd=TEMP_DIR,
            capture_output=True,
            text=True,
            timeout=60
        ) 
        
        print(f"Agentic Validation Output:\n{proc.stdout}")
        if proc.stderr:
            print(f"Agentic Validation Errors:\n{proc.stderr}")
        
        # Parse JSON from last line
        lines = proc.stdout.strip().splitlines()
        if lines:
            try:
                last_line = lines[-1]
                metrics = json.loads(last_line)
                is_valid = metrics.get("is_correct", False)
                speedup = metrics.get("speedup", 0)
                t_orig = metrics.get("original_time", 0)
                t_ref = metrics.get("refactored_time", 0)
                
                output_log += f"Validation {'PASSED' if is_valid else 'FAILED'}\n"
                output_log += f"Original Time:  {t_orig:.4f}s\n"
                output_log += f"Refactored Time: {t_ref:.4f}s\n"
                output_log += f"Speedup:        {speedup:.2f}x\n"
                if not is_valid:
                     output_log += f"Error: {metrics.get('error', 'Unknown error')}\n"
                     
            except json.JSONDecodeError:
                output_log += "Failed to parse JSON metrics from validator script.\n"
                output_log += f"Raw Output: {proc.stdout}\n"
        else:
            output_log += "No output from validation script.\n"

    except subprocess.TimeoutExpired:
        output_log += "Validation script timed out.\n"
    except Exception as e:
        output_log += f"Execution error: {e}\n"

    print(output_log)
    return {"validation_output": output_log, "is_valid": is_valid, "iterations": state.get("iterations", 0) + 1}

def orchestrator_node(state: AgentState):
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