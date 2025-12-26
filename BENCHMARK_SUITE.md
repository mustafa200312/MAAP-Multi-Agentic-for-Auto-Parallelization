# MAAP Benchmark Suite Documentation

This document describes the benchmark suite designed to evaluate the Multi-Agentic Auto-Parallelization (MAAP) system. The suite contains 20 distinct workloads (10 Python, 10 C) covering a wide spectrum of parallel patterns, difficulty levels, and algorithmic challenges.

## Directory Structure
- `benchmarks/python/`: Python workloads targeting `joblib`, `concurrent.futures`, and `multiprocessing`.
- `benchmarks/c/`: C workloads targeting OpenMP directives (`#pragma omp`).

---

## Python Benchmarks (`benchmarks/python/`)

| ID | Filename | Difficulty | Pattern | Description | Challenge |
|:---|:---|:---|:---|:---|:---|
| 01 | `01_cpu_loop.py` | Basic | Loop Map | Independent CPU-bound mathematical operations in a loop. | Correctly identifying `joblib` or `pool.map` as the strategy. |
| 02 | `02_reduction.py` | Basic | Reduction | Calculating Sum, Min, Max, and Product of a list. | Identifying valid shared variable updates (accumulators). |
| 03 | `03_io_batch.py` | Basic | I/O Batch | Fetching data from simulated URLs with latency. | Choosing `ThreadPoolExecutor` instead of `ProcessPoolExecutor` for I/O. |
| 04 | `04_task_graph.py` | Basic | Task Graph | Three independent, heavy function calls. | Wrapping distinct function calls in a `Future` or `delayed` object. |
| 05 | `05_vectorize.py` | Basic | Vectorize | Dense element-wise array arithmetic. | Identifying NumPy broadcasting opportunities. |
| 06 | `06_pipeline.py` | Basic | Pipelining | Read → Process → Write stages. | Chaining processing stages efficiently. |
| 07 | `07_monte_carlo_pi.py` | Famous | Map/Reduce | Estimating Pi using random sampling. | Managing random state and reducing partial counters. |
| 08 | `08_matrix_multiplication.py` | Famous | Nested Loop | Naïve O(N³) matrix multiplication. | Identifying the outermost independent loop for parallelization. |
| 09 | `09_nbody_simulation.py` | Hard | Nested/Dep | N-Body simulation (O(N²) interactions). | Handling complex nested loops where every particle interacts with every other. |
| 10 | `10_image_convolution.py` | Hard | Stencil | Applying a blur kernel to a grid. | Managing boundary conditions and preventing race conditions (Write-After-Read). |

---

## C Benchmarks (`benchmarks/c/`)

| ID | Filename | Difficulty | Pattern | Description | Challenge |
|:---|:---|:---|:---|:---|:---|
| 01 | `01_simple_loop.c` | Basic | Loop Map | Math heavy independent loop. | Applying standard `#pragma omp parallel for`. |
| 02 | `02_reduction.c` | Basic | Reduction | Summing array elements. | Adding `reduction(+:variable)` clause correctly. |
| 03 | `03_tasks.c` | Basic | Task Graph | Two independent heavy function calls. | Using `#pragma omp sections` or `task`. |
| 04 | `04_vector.c` | Basic | Vectorize | Arithmetic on arrays. | Utilizing `#pragma omp simd`. |
| 05 | `05_monte_carlo_pi.c` | Famous | Reduction | Monte Carlo Pi estimation. | **Hidden State**: Handling `rand()` which is not thread-safe (requires `rand_r` or thread-local seeds). |
| 06 | `06_matrix_multiplication.c` | Famous | Nested Loop | Classic O(N³) matrix mult. | Parallelizing the outer loop while keeping inner loops sequential. |
| 07 | `07_nbody_simulation.c` | Hard | Nested | N-Body physics step. | Recognizing the data vs. calculation independence in the inner loop. |
| 08 | `08_image_convolution.c` | Hard | Stencil | convolution filter. | **Buffer Management**: Ensuring output is written to a separate buffer to avoid reading stale data. |
| 09 | `09_merge_sort.c` | Medium | Recursion | Recursive Divide & Conquer. | Standard loops fail here; must use `#pragma omp task` for recursive calls. |
| 10 | `10_prime_sieve.c` | Medium | Load Imbalance | Counting primes up to N. | **Scheduling**: Inner loop cost varies wildly; requires `schedule(dynamic)`. |

## Usage
To evaluate the MAAP system against any benchmark:

```bash
python main.py benchmarks/python/09_nbody_simulation.py
python main.py benchmarks/c/10_prime_sieve.c
```
