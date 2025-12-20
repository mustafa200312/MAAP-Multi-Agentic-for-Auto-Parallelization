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

# Check environment variables
REQUIRED_VARS = ["GPT_OSS_DEPLOYMENT_NAME", "AZURE_OPENAI_API_VERSION", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY"]
missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
if missing:
    logger.error(f"Missing environment variables: {missing}")
    sys.exit(1)

# Import graph after env check (in case module loading depends on env)
try:
    from graphs.workflow import app
except ImportError as e:
    logger.error(f"Failed to import workflow: {e}")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="MAAP: Multi-Agentic for Auto Parallelization")
    parser.add_argument("input_file", help="Path to the Python file to optimize")
    parser.add_argument("--output", "-o", help="Path to save the optimized code. Defaults to <input>_optimized.py", default=None)
    
    args = parser.parse_args()
    file_path = args.input_file

    if not os.path.exists(file_path):
        logger.error(f"Input file not found: {file_path}")
        sys.exit(1)

    # Determine output file
    if args.output:
        output_path = args.output
    else:
        base, ext = os.path.splitext(file_path)
        output_path = f"{base}_optimized{ext}"

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
        "iterations": 0,
        "messages": []
    }
    
    # Create temp environment
    TEMP_DIR = "temp_env"
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)
    logger.info(f"Created temporary environment at {TEMP_DIR}")
    
    # Run the graph
    try:
        try:
            result = app.invoke(initial_state)
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            sys.exit(1)
        
        logger.info("=== FINAL RESULT ===")
        
        if result.get("is_valid"):
            logger.info("SUCCESS! Code parallelized and validated.")
            
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result["modified_code"])
                logger.info(f"Modified code saved to '{output_path}'")
            except IOError as e:
                logger.error(f"Failed to save optimized code: {e}")
                
            print("\n--- Validation Output ---")
            print(result.get("validation_output", "No output captured."))
        else:
            logger.warning("FAILED to verify parallelization.")
            logger.warning("Last Validation Output:")
            print(result.get("validation_output", "No output captured."))
            
            # Optionally save the modified code anyway for inspection
            failed_output = f"{output_path}.failed"
            with open(failed_output, "w", encoding="utf-8") as f:
                 f.write(result.get("modified_code", ""))
            logger.info(f"Saved unverified code to {failed_output} for inspection.")
            
    finally:
        # Cleanup
        if os.path.exists(TEMP_DIR):
            logger.info(f"Cleaning up temporary environment: {TEMP_DIR}")
            try:
                # shutil.rmtree(TEMP_DIR) 
                # User asked to "put created files" there AND "automatic deletion".
                # But sometimes deletion fails on Windows if processes (like the validator) are still holding files.
                # Adding a small retry or ignore errors might be safer, or just standard rmtree.
                shutil.rmtree(TEMP_DIR, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp dir: {e}")

if __name__ == "__main__":
    main()
