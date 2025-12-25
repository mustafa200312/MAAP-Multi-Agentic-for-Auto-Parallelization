"""
Deterministic C Code Validator Agent for OpenMP parallelization.
Replaces the LLM-based validator with a robust, pre-written Python script template.
"""

from typing import Any, Dict
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableLambda

class CValidatorOutput(BaseModel):
    validation_script_code: str = Field(..., description="A Python script that compiles and runs both C versions.")
    explanation: str = Field(default="Deterministic validation strategy.", description="Explanation of the validation strategy.")

# This script is injected into the workflow to be run in the temp environment
UNIVERSAL_VALIDATOR_SCRIPT = r"""
import subprocess
import sys
import os
import time
import json
import shlex

def compile_code(source_file, output_exec, flags):
    cmd = ["gcc"] + flags + ["-o", output_exec, source_file, "-lm"]
    print(f"Compiling: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Compilation Failed for {source_file}:")
            print(result.stderr)
            return False
        return True
    except FileNotFoundError:
        print("Error: 'gcc' not found. Please ensure GCC is installed and in your PATH.")
        return False
    except Exception as e:
        print(f"Compilation Error: {e}")
        return False


def run_code(exec_name):
    # Handle platform-specific extensions (Windows needs .exe)
    if os.name == 'nt' and not exec_name.endswith('.exe'):
        exec_path = exec_name + ".exe"
    else:
        exec_path = exec_name
        
    # Ensure it starts with ./ if not absolute, though subprocess often handles this.
    # actually better to just pass the full path or relative path clearly.
    if not os.path.exists(exec_path) and os.path.exists(f"./{exec_path}"):
        exec_path = f"./{exec_path}"
        
    start_time = time.perf_counter()
    try:
        # TIMEOUT set to 30 seconds to prevent infinite loops in bad parallel code
        result = subprocess.run([os.path.abspath(exec_path)], capture_output=True, text=True, timeout=30)
        end_time = time.perf_counter()
        return result.stdout, result.stderr, end_time - start_time, result.returncode
    except subprocess.TimeoutExpired:
        print(f"Execution timed out for {exec_path}")
        return None, "TIMEOUT", 0, -1
    except Exception as e:
        print(f"Execution failed for {exec_path}: {e}")
        return None, str(e), 0, -1

def validate():
    # 1. Compile Original
    if not compile_code("original.c", "original", ["-O2"]):
        print("Validation Failed: Original compilation error")
        return

    # 2. Compile Parallel
    if not compile_code("parallel.c", "parallel", ["-O2", "-fopenmp"]):
        print("Validation Failed: Parallel compilation error")
        return

    # 3. Run Original
    print("Running original code...")
    orig_out, orig_err, orig_time, orig_ret = run_code("original")
    if orig_ret != 0:
        print(f"Original execution failed: {orig_err}")
        print("Validation Failed")
        return

    # 4. Run Parallel
    print("Running parallel code...")
    par_out, par_err, par_time, par_ret = run_code("parallel")
    if par_ret != 0:
        print(f"Parallel execution failed: {par_err}")
        print("Validation Failed")
        return

    # 5. Compare Results (ignoring order for parallel correctness)
    # We strip whitespace and split by lines
    orig_lines = sorted([line.strip() for line in orig_out.strip().splitlines() if line.strip()])
    par_lines = sorted([line.strip() for line in par_out.strip().splitlines() if line.strip()])

    if orig_lines == par_lines:
        print("\nValidation Passed")
        
        # Calculate speedup
        speedup = 0.0
        if par_time > 0:
            speedup = orig_time / par_time
            
        metrics = {
            "original_time": orig_time,
            "parallel_time": par_time,
            "speedup": speedup
        }
        # strict JSON format for parsing
        print(f"METRICS: {json.dumps(metrics)}")
    else:
        print("\nValidation Failed: Output mismatch")
        print("--- Original Output (First 10 lines sorted) ---")
        print("\n".join(orig_lines[:10]))
        print("--- Parallel Output (First 10 lines sorted) ---")
        print("\n".join(par_lines[:10]))

if __name__ == "__main__":
    validate()
"""

def _get_validator_output(input_dict: Dict[str, Any]) -> CValidatorOutput:
    """
    Returns the fixed validator script regardless of the input code.
    The script itself handles the recompilation and execution of 'original.c' 
    and 'parallel.c' which are expected to exist in the working directory.
    """
    return CValidatorOutput(
        validation_script_code=UNIVERSAL_VALIDATOR_SCRIPT,
        explanation="Using deterministic Universal Validator Script that sorts outputs to verify correctness."
    )

# The agent runnable
c_validator_agent = RunnableLambda(_get_validator_output)
