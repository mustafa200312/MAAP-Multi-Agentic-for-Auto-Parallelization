import os
import sys
import shutil
import argparse
import logging
from dotenv import load_dotenv
sys.dont_write_bytecode = True

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress noisy HTTP logs from libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

# Load env before imports that use it
load_dotenv()


# Import graph after env check (in case module loading depends on env)
try:
    from graphs.workflow import app
except ImportError as e:
    logger.error(f"Failed to import workflow: {e}")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="MAAP: Multi-Agentic for Auto Parallelization")
    parser.add_argument("input_file", help="Path to the Python file to optimize")
    
    args = parser.parse_args()
    file_path = args.input_file

    if not os.path.exists(file_path):
        logger.error(f"Input file not found: {file_path}")
        sys.exit(1)

    # Structured Output Directory
    source_basename = os.path.splitext(os.path.basename(file_path))[0]
    output_dir = os.path.join("output", source_basename)
    os.makedirs(output_dir, exist_ok=True)
    
    optimized_path = os.path.join(output_dir, "optimized.py")
    report_path = os.path.join(output_dir, "report.txt")
    validation_script_path = os.path.join(output_dir, "validation_script.py")

    logger.info(f"Reading source code from {file_path}...")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
    except Exception as e:
        logger.error(f"Failed to read input file: {e}")
        sys.exit(1)

    logger.info("Starting Auto-Parallelization Workflow...")
    
    initial_state = {
        "source_code": source_code,
        "source_filename": source_basename,
        "output_dir": output_dir,
        "iterations": 0,
        "messages": []
    }
    
    # Create temp environment
    TEMP_DIR = "temp_env"
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
    os.makedirs(TEMP_DIR)
    logger.info(f"Created temporary environment at {TEMP_DIR}")
    
    # Run the graph
    result = {}
    try:
        try:
            result = app.invoke(initial_state)
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            # Ensure we have a result object to write partial logs
            result = {"validation_output": f"Workflow failed with error: {e}", "is_valid": False}
        
        logger.info("=== FINAL RESULT ===")
        
        # Always save validation report
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(result.get("validation_output", "No validation output."))
        logger.info(f"Validation report saved to '{report_path}'")
        
        # Copy generated validation script if exists
        # It's in temp_env/validate_agentic.py (if agentic)
        gen_script = os.path.join(TEMP_DIR, "validate_agentic.py")
        if os.path.exists(gen_script):
            shutil.copy(gen_script, validation_script_path)
            logger.info(f"Validation script saved to '{validation_script_path}'")
        
        if result.get("is_valid"):
            logger.info("SUCCESS! Code parallelized and validated.")
            
            try:
                with open(optimized_path, "w", encoding="utf-8") as f:
                    f.write(result.get("modified_code", ""))
                logger.info(f"Optimized code saved to '{optimized_path}'")
            except IOError as e:
                logger.error(f"Failed to save optimized code: {e}")
                
            print("\n--- Validation Output ---")
            print(result.get("validation_output", "No output captured."))
        else:
            logger.warning("FAILED to verify parallelization.")
            logger.warning("Last Validation Output:")
            print(result.get("validation_output", "No output captured."))
            
            # Save the modified code anyway for inspection
            if "modified_code" in result:
                failed_path = os.path.join(output_dir, "optimized_FAILED.py")
                with open(failed_path, "w", encoding="utf-8") as f:
                     f.write(result.get("modified_code", ""))
                logger.info(f"Saved unverified code to {failed_path} for inspection.")
            
    finally:
        # Cleanup temp
        if os.path.exists(TEMP_DIR):
            logger.info(f"Cleaning up temporary environment: {TEMP_DIR}")
            shutil.rmtree(TEMP_DIR, ignore_errors=True)

if __name__ == "__main__":
    main()
