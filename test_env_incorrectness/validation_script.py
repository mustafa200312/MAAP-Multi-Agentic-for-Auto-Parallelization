
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
