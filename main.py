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
# Check environment variables
REQUIRED_VARS = ["model", "api_key"]
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

# Supported languages and their file extensions
LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".c": "c",
    ".h": "c",  # Header files treated as C
}


def detect_language(file_path: str) -> str:
    """
    Detect the programming language based on file extension.
    
    Args:
        file_path: Path to the source file
        
    Returns:
        Language identifier ('python' or 'c')
        
    Raises:
        ValueError: If the file extension is not supported
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext not in LANGUAGE_EXTENSIONS:
        supported = ", ".join(LANGUAGE_EXTENSIONS.keys())
        raise ValueError(f"Unsupported file extension '{ext}'. Supported: {supported}")
    
    return LANGUAGE_EXTENSIONS[ext]


def get_output_path(input_path: str, language: str, custom_output: str = None) -> str:
    """
    Generate the output file path based on input and language.
    
    Args:
        input_path: Original input file path
        language: Detected language
        custom_output: Custom output path (optional)
        
    Returns:
        Output file path
    """
    if custom_output:
        return custom_output
    
    base, ext = os.path.splitext(input_path)
    
    if language == "c":
        return f"{base}_parallel{ext}"
    else:
        return f"{base}_optimized{ext}"


def get_temp_dir(language: str) -> str:
    """Get the appropriate temp directory based on language."""
    if language == "c":
        return "temp_env_c"
    return "temp_env"


def main():
    parser = argparse.ArgumentParser(
        description="Auto-Parallelization Agent System - Supports Python (joblib) and C (OpenMP)"
    )
    parser.add_argument(
        "input_file", 
        help="Path to the source file to optimize (.py for Python, .c for C)"
    )
    parser.add_argument(
        "--output", "-o", 
        help="Path to save the optimized code. Defaults to <input>_optimized.py or <input>_parallel.c",
        default=None
    )
    parser.add_argument(
        "--language", "-l",
        choices=["python", "c"],
        help="Force language (auto-detected from extension if not specified)",
        default=None
    )
    
    args = parser.parse_args()
    file_path = args.input_file

    if not os.path.exists(file_path):
        logger.error(f"Input file not found: {file_path}")
        sys.exit(1)

    # Detect or use specified language
    try:
        if args.language:
            language = args.language
            logger.info(f"Using specified language: {language}")
        else:
            language = detect_language(file_path)
            logger.info(f"Detected language: {language}")
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    # Determine output file
    output_path = get_output_path(file_path, language, args.output)

    logger.info(f"Reading source code from {file_path}...")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
    except Exception as e:
        logger.error(f"Failed to read input file: {e}")
        sys.exit(1)

    # Language-specific info
    if language == "c":
        logger.info("Starting Auto-Parallelization Workflow (C/OpenMP)...")
        logger.info("Note: Ensure GCC with OpenMP support is installed (gcc -fopenmp)")
    else:
        logger.info("Starting Auto-Parallelization Workflow (Python/joblib)...")
    
    initial_state = {
        "source_code": source_code,
        "language": language,
        "iterations": 0,
        "messages": []
    }
    
    # Create temp environment
    TEMP_DIR = get_temp_dir(language)
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
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
        logger.info("=== FINAL RESULT ===")
        
        if result.get("is_valid"):
            if language == "c":
                logger.info("SUCCESS! C code parallelized with OpenMP and validated.")
            else:
                logger.info("SUCCESS! Python code parallelized with joblib and validated.")
            
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result["modified_code"])
                logger.info(f"Modified code saved to '{output_path}'")
            except IOError as e:
                logger.error(f"Failed to save optimized code: {e}")
                
            print("\n--- Validation Output ---")
            validation_output = result.get("validation_output", "No output captured.")
            print(validation_output)

            # Performance Report Parsing
            import re
            import json
            metrics_match = re.search(r'METRICS: ({.*?})', validation_output)
            if metrics_match:
                try:
                    metrics = json.loads(metrics_match.group(1))
                    print("\n=== PERFORMANCE REPORT ===")
                    print(f"Original Time: {metrics.get('original_time', 0):.4f}s")
                    print(f"Parallel Time: {metrics.get('parallel_time', 0):.4f}s")
                    print(f"Speedup:      {metrics.get('speedup', 0):.2f}x")
                    print("==========================")
                except Exception as e:
                    logger.warning(f"Failed to parse performance metrics: {e}")
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
                shutil.rmtree(TEMP_DIR, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp dir: {e}")

if __name__ == "__main__":
    main()
