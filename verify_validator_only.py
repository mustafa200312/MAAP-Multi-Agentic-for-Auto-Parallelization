import os
import sys
import subprocess
from agents.c_validator_deterministic import c_validator_agent

# Mock State
state = {
    "source_code": "", # Not used by deterministic agent
    "modified_code": "" # Not used by deterministic agent
}

def check_validation(name, orig_code, para_code, expected_pass):
    print(f"--- Testing {name} ---")
    
    # 1. Invoke Agent
    result = c_validator_agent.invoke(state)
    script = result.validation_script_code
    
    # 2. Setup Environment
    print(f"Script generated (len={len(script)})")
    
    TEMP_DIR = f"test_env_{name}"
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    with open(os.path.join(TEMP_DIR, "original.c"), "w") as f:
        f.write(orig_code)
    with open(os.path.join(TEMP_DIR, "parallel.c"), "w") as f:
        f.write(para_code)
    with open(os.path.join(TEMP_DIR, "validation_script.py"), "w") as f:
        f.write(script)
        
    # 3. Run Script
    print("Running validation script...")
    res = subprocess.run([sys.executable, "validation_script.py"], cwd=TEMP_DIR, capture_output=True, text=True)
    
    output = res.stdout + res.stderr
    passed = "Validation Passed" in output
    print(f"Output:\n{output}")
    
    if passed == expected_pass:
        print(f"SUCCESS: {name} result matches expected ({expected_pass})")
    else:
        print(f"FAILURE: {name} result {passed} != expected {expected_pass}")
        sys.exit(1)

# Test Cases
ORIGINAL_C = r"""
#include <stdio.h>
int main() { printf("Hello\nWorld\n"); return 0; }
"""

PARALLEL_GOOD_C = r"""
#include <stdio.h>
#include <omp.h>
int main() { 
    // Just print same thing, maybe different order?
    // Actually for this test, same order is fine.
    printf("World\n"); 
    printf("Hello\n"); 
    return 0; 
}
""" # Note: "World\nHello" sorted is "Hello\nWorld", so this should PASS if sorted.

PARALLEL_BAD_C = r"""
#include <stdio.h>
int main() { printf("Hello\nWrong\n"); return 0; }
"""

if __name__ == "__main__":
    check_validation("correctness_reordered", ORIGINAL_C, PARALLEL_GOOD_C, True)
    check_validation("incorrectness", ORIGINAL_C, PARALLEL_BAD_C, False)
    print("\nALL TESTS PASSED")
