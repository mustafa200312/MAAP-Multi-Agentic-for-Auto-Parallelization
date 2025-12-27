# MAAP: Multi-Agentic Auto-Parallelization System

**MAAP** is an advanced automated system that leverages **Large Language Models (LLMs)** combined with **static AST analysis** to transform sequential Python and C code into parallel implementations.

Built as part of the *CSCI465/ECEN433: Introduction to Parallel Computing* course (Fall 2025).

## 🚀 Key Features

*   **Hybrid Analysis**: Combines strict AST parsing (for exact loops/variables) with LLM reasoning (for semantic pattern matching).
*   **Multi-Agent Architecture**:
    *   **Analyzer**: Detects opportunities (`loop_map`, `reduction`, etc.).
    *   **Implementer**: Applies transformations (`joblib`, `OpenMP`).
    *   **Validator**: runs code, verifies correctness, and checks for **Performance Regression** (Speedup > 1.0x).
*   **Self-Correction**: If validation fails (compilation error, output mismatch), the error is fed back to the Implementer for auto-repair.
*   **Dual Language Support**:
    *   **C**: Auto-insertion of OpenMP directives (`#pragma omp parallel for`).
    *   **Python**: Auto-conversion to `joblib.Parallel` or `concurrent.futures`.

## 🏗 System Architecture

The system is orchestrated via **LangGraph**:

1.  **Input**: User provides a `.py` or `.c` file.
2.  **Analysis**: The appropriate Analyzer (Python/C) scans structure.
3.  **Implementation**: The Implementer Agent writes parallel code.
4.  **Validation**: A custom harness executes Original vs. Refactored code.
    *   *Pass*: Result saved to `output/`.
    *   *Fail*: Error sent back to Implementer (Retry Loop).

## 📊 Benchmark Results

We evaluated MAAP on 20 synthetic benchmarks.

### C / OpenMP (Success)
MAAP excels at C parallelization due to the low overhead of OpenMP.
*   **Vector Ops**: 3.61x Speedup
*   **Matrix Mul**: 2.90x Speedup
*   **Prime Sieve**: 2.35x Speedup

### Python / Multiprocessing (Challenges)
Python parallelization faces the **GIL** and **Process Spawning Overhead**.
*   **I/O Bound**: 3.78x Speedup (Success via Threading).
*   **CPU Bound**: Often fails regression checks (Speedup < 1.0x) because spawning processes takes longer than the small execution time of test scripts.

## 🛠 Usage

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run Auto-Parallelizer**:
    ```bash
    python main.py path/to/script.py
    # OR
    python main.py path/to/source.c
    ```

3.  **View Results**:
    Check the `output/{filename}/` directory for:
    *   `optimized.py` / `optimized.c`
    *   `report.txt` (Speedup metrics)

## 📄 Repository Structure

*   `agents/`: Definitions for Analyzer, Implementer, Validator.
*   `benchmarks/`: Suite of 20 test files (10 C, 10 Python).
*   `graphs/`: LangGraph workflow orchestration.
*   `paper/`: LaTeX source of the academic paper.
*   `output/`: Generated parallel code and reports.