from typing import TypedDict, Annotated, List, Literal
from langgraph.graph import StateGraph, END
import subprocess
import os
import sys
import platform

# Import Python agents
from agents.analyser import dependencies_detector_agent
from agents.implementer import implementer_agent
from agents.validator import validator_agent
from agents.orchestrator import orchestrator_agent
from agents.ast_utils import analyze_code_ast

# Import C agents
from agents.c_analyser import c_dependencies_detector_agent
from agents.c_implementer import c_implementer_agent
from agents.c_validator import c_validator_agent
from agents.c_ast_utils import analyze_c_code_ast


class AgentState(TypedDict):
    source_code: str
    language: Literal["python", "c"]  # Language of the source code
    analysis_report: str
    modified_code: str
    validation_script: str
    validation_output: str
    is_valid: bool
    iterations: int
    messages: List[str]


# ============================================
# PYTHON WORKFLOW NODES
# ============================================

def py_analyzer_node(state: AgentState):
    """Analyze Python code for parallelization opportunities using joblib."""
    print("--- [PYTHON] DETECTING DEPENDENCIES (AST + LLM) ---")
    ast_report = analyze_code_ast(state["source_code"])
    result = dependencies_detector_agent.invoke({
        "source_code": state["source_code"],
        "ast_report": ast_report
    })
    return {"analysis_report": f"AST Report:\n{ast_report}\n\nAgent Analysis:\n{result.output}"}


def py_implementer_node(state: AgentState):
    """Implement Python parallelization using joblib."""
    print("--- [PYTHON] IMPLEMENTING PARALLELISM (joblib) ---")
    result = implementer_agent.invoke({
        "source_code": state["source_code"], 
        "analysis_report": state["analysis_report"]
    })
    return {"modified_code": result.modified_output}


def py_validator_node(state: AgentState):
    """Validate Python parallelization by running comparison tests."""
    print("--- [PYTHON] VALIDATING IMPLEMENTATION ---")
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
    
    TEMP_DIR = "temp_env"
    os.makedirs(TEMP_DIR, exist_ok=True)

    with open(os.path.join(TEMP_DIR, "original.py"), "w", encoding="utf-8") as f:
        f.write(state["source_code"])
        
    with open(os.path.join(TEMP_DIR, "refactored.py"), "w", encoding="utf-8") as f:
        f.write(state["modified_code"])

    script_path = os.path.join(TEMP_DIR, "validation_script.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)
    
    try:
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


# ============================================
# C WORKFLOW NODES
# ============================================

def c_analyzer_node(state: AgentState):
    """Analyze C code for OpenMP parallelization opportunities."""
    print("--- [C] DETECTING DEPENDENCIES (AST + LLM) ---")
    ast_report = analyze_c_code_ast(state["source_code"])
    result = c_dependencies_detector_agent.invoke({
        "source_code": state["source_code"],
        "ast_report": ast_report
    })
    return {"analysis_report": f"AST Report:\n{ast_report}\n\nAgent Analysis:\n{result.output}"}


def c_implementer_node(state: AgentState):
    """Implement C parallelization using OpenMP pragmas."""
    print("--- [C] IMPLEMENTING PARALLELISM (OpenMP) ---")
    result = c_implementer_agent.invoke({
        "source_code": state["source_code"], 
        "analysis_report": state["analysis_report"]
    })
    return {"modified_code": result.modified_output}


def c_validator_node(state: AgentState):
    """Validate C/OpenMP parallelization by compiling and running comparison tests."""
    print("--- [C] VALIDATING IMPLEMENTATION ---")
    result = c_validator_agent.invoke({
        "source_code": state["source_code"],
        "modified_code": state["modified_code"]
    })
    
    script_content = result.validation_script_code
    # Basic cleanup if markdown is included
    if "```python" in script_content:
        script_content = script_content.split("```python")[1].split("```")[0]
    elif "```" in script_content:
        script_content = script_content.split("```")[1].split("```")[0]
    
    TEMP_DIR = "temp_env_c"
    os.makedirs(TEMP_DIR, exist_ok=True)

    # Save C source files
    with open(os.path.join(TEMP_DIR, "original.c"), "w", encoding="utf-8") as f:
        f.write(state["source_code"])
        
    with open(os.path.join(TEMP_DIR, "parallel.c"), "w", encoding="utf-8") as f:
        f.write(state["modified_code"])

    # Save validation script
    script_path = os.path.join(TEMP_DIR, "validation_script.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)
    
    try:
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
            timeout=60  # Longer timeout for compilation
        )
        output = proc.stdout + "\n" + proc.stderr
        is_valid = "Validation Passed" in output
    except Exception as e:
        output = str(e)
        is_valid = False
        
    return {"validation_output": output, "is_valid": is_valid, "iterations": state.get("iterations", 0) + 1}


# ============================================
# ROUTING LOGIC
# ============================================

def language_router(state: AgentState):
    """Route to appropriate analyzer based on language."""
    language = state.get("language", "python")
    if language == "c":
        return "c_analyzer"
    return "py_analyzer"


def py_validation_router(state: AgentState):
    """Route after Python validation."""
    if state.get("is_valid"):
        return "end"
    if state.get("iterations", 0) > 3:
        return "end"
    return "py_implementer"


def c_validation_router(state: AgentState):
    """Route after C validation."""
    if state.get("is_valid"):
        return "end"
    if state.get("iterations", 0) > 3:
        return "end"
    return "c_implementer"


def orchestrator_node(state: AgentState):
    """Orchestrator node (placeholder for future enhancements)."""
    return {}


# ============================================
# BUILD WORKFLOW GRAPH
# ============================================

workflow = StateGraph(AgentState)

# Add Python nodes
workflow.add_node("py_analyzer", py_analyzer_node)
workflow.add_node("py_implementer", py_implementer_node)
workflow.add_node("py_validator", py_validator_node)

# Add C nodes
workflow.add_node("c_analyzer", c_analyzer_node)
workflow.add_node("c_implementer", c_implementer_node)
workflow.add_node("c_validator", c_validator_node)

# Set entry point with language routing
workflow.set_conditional_entry_point(
    language_router,
    {
        "py_analyzer": "py_analyzer",
        "c_analyzer": "c_analyzer"
    }
)

# Python workflow edges
workflow.add_edge("py_analyzer", "py_implementer")
workflow.add_edge("py_implementer", "py_validator")
workflow.add_conditional_edges(
    "py_validator",
    py_validation_router,
    {
        "py_implementer": "py_implementer",
        "end": END
    }
)

# C workflow edges
workflow.add_edge("c_analyzer", "c_implementer")
workflow.add_edge("c_implementer", "c_validator")
workflow.add_conditional_edges(
    "c_validator",
    c_validation_router,
    {
        "c_implementer": "c_implementer",
        "end": END
    }
)

app = workflow.compile()
