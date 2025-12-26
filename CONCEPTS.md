# Parallel Programming Concepts in MAAP

This document explains all parallelization concepts, patterns, and candidate types used in the MAAP (Multi-Agentic Auto-Parallelization) system.

---

## Table of Contents

1. [Fundamentals](#fundamentals)
2. [Python Candidate Types](#python-candidate-types)
3. [C/OpenMP Candidate Types](#copenmp-candidate-types)
4. [Comparison: Python vs C](#comparison-python-vs-c)

---

## Fundamentals

### What is Parallelism?

**Parallelism** is executing multiple computations simultaneously to reduce total execution time.

```
SEQUENTIAL:
Task 1: ████████
Task 2:         ████████
Task 3:                 ████████
Total: ═══════════════════════════► 24 time units

PARALLEL (3 cores):
Task 1: ████████
Task 2: ████████
Task 3: ████████
Total: ═════════► 8 time units (3x speedup!)
```

### Types of Parallelism

| Type | Description | Example |
|------|-------------|---------|
| **Data Parallelism** | Same operation on different data | Processing each pixel in an image |
| **Task Parallelism** | Different operations running concurrently | Reading file while processing previous file |
| **Pipeline Parallelism** | Data flows through stages | Read → Transform → Write |

### CPU-bound vs I/O-bound

| Type | Bottleneck | Example | Best Solution |
|------|------------|---------|---------------|
| **CPU-bound** | Computation | Math, image processing, encryption | Multi-core parallelism |
| **I/O-bound** | Waiting | Network requests, file reads, database | Threads or async |

---

## Python Candidate Types

Python has **6 candidate types** detected by the analyzer.

### 1. `loop_map` — Independent Iterations

**Definition:** A loop where each iteration is completely independent and produces a per-item output.

**Before:**
```python
results = []
for item in data:
    result = heavy_computation(item)  # CPU-bound
    results.append(result)
```

**After (joblib):**
```python
from joblib import Parallel, delayed

def worker(item):
    return heavy_computation(item)

results = Parallel(n_jobs=-1, prefer="processes")(
    delayed(worker)(item) for item in data
)
```

**How it works:**
```
┌─────────────────────────────────────────────────────────────────┐
│  Data: [item1, item2, item3, item4, item5, item6, item7, item8] │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐              │
│         ▼                    ▼                    ▼              │
│    ┌─────────┐          ┌─────────┐          ┌─────────┐        │
│    │ Core 0  │          │ Core 1  │          │ Core 2  │        │
│    │item1,4,7│          │item2,5,8│          │item3,6  │        │
│    └─────────┘          └─────────┘          └─────────┘        │
│         │                    │                    │              │
│         └────────────────────┼────────────────────┘              │
│                              ▼                                   │
│                    [result1, result2, ...]                       │
└─────────────────────────────────────────────────────────────────┘
```

**When to use:**
- ✅ Each iteration is independent
- ✅ No shared mutable state
- ✅ Heavy CPU computation per item
- ❌ Not for simple operations (overhead > benefit)

---

### 2. `reduction` — Accumulator Pattern

**Definition:** A loop that accumulates a result using an operation like `+`, `*`, `max`, `min`.

**Before:**
```python
total = 0
for item in data:
    total += expensive_calculation(item)
```

**After (chunked reduction):**
```python
from joblib import Parallel, delayed
import numpy as np

def process_chunk(chunk):
    return sum(expensive_calculation(item) for item in chunk)

# Split into chunks
chunks = np.array_split(data, n_jobs)

# Process chunks in parallel
partial_sums = Parallel(n_jobs=-1)(
    delayed(process_chunk)(chunk) for chunk in chunks
)

# Combine results
total = sum(partial_sums)
```

**How it works:**
```
┌─────────────────────────────────────────────────────────────────┐
│                     Original: sum = 0                            │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐              │
│         ▼                    ▼                    ▼              │
│    ┌─────────┐          ┌─────────┐          ┌─────────┐        │
│    │ Chunk 1 │          │ Chunk 2 │          │ Chunk 3 │        │
│    │ sum: 100│          │ sum: 150│          │ sum: 120│        │
│    └─────────┘          └─────────┘          └─────────┘        │
│         │                    │                    │              │
│         └────────────────────┼────────────────────┘              │
│                              ▼                                   │
│                   COMBINE: 100 + 150 + 120 = 370                 │
└─────────────────────────────────────────────────────────────────┘
```

**When to use:**
- ✅ Accumulating with associative operations (`+`, `*`, `max`, `min`)
- ✅ Heavy computation per item
- ❌ Non-associative operations (order matters)

---

### 3. `io_batch` — Concurrent I/O Operations

**Definition:** Many independent I/O operations that spend most time waiting.

**Before:**
```python
results = []
for url in urls:
    response = requests.get(url)  # Waits 200ms each
    results.append(response.json())
# 100 URLs × 200ms = 20 seconds
```

**After (ThreadPoolExecutor):**
```python
from concurrent.futures import ThreadPoolExecutor

def fetch(url):
    return requests.get(url).json()

with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(fetch, urls))
# 100 URLs ÷ 10 threads = 2 seconds
```

**How it works:**
```
┌─────────────────────────────────────────────────────────────────┐
│  SEQUENTIAL:                                                     │
│  Request 1: ████░░░░░░░░░░░░ (waiting for response)             │
│  Request 2:                 ████░░░░░░░░░░░░                    │
│  Request 3:                                 ████░░░░░░░░░░░░    │
│                                                                 │
│  PARALLEL (ThreadPoolExecutor):                                 │
│  Thread 1: ████░░░░░░░░░░░░                                     │
│  Thread 2: ████░░░░░░░░░░░░                                     │
│  Thread 3: ████░░░░░░░░░░░░                                     │
│  (All waiting at the same time!)                                │
└─────────────────────────────────────────────────────────────────┘
```

**Why Threads (not Processes)?**
- Python's GIL is released during I/O operations
- Threads are lightweight (shared memory)
- No serialization overhead

**When to use:**
- ✅ Network requests (HTTP, database, APIs)
- ✅ File I/O operations
- ✅ Any blocking I/O
- ❌ CPU-bound work (use processes instead)

---

### 4. `task_graph` — Independent Functions

**Definition:** Multiple independent function calls that don't depend on each other's immediate results.

**Before:**
```python
# These are independent!
result_a = compute_a()  # Takes 3 seconds
result_b = compute_b()  # Takes 2 seconds
result_c = compute_c()  # Takes 4 seconds
# Total: 9 seconds
```

**After (concurrent.futures):**
```python
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor() as executor:
    future_a = executor.submit(compute_a)
    future_b = executor.submit(compute_b)
    future_c = executor.submit(compute_c)
    
    result_a = future_a.result()
    result_b = future_b.result()
    result_c = future_c.result()
# Total: max(3, 2, 4) = 4 seconds
```

**How it works:**
```
┌─────────────────────────────────────────────────────────────────┐
│  SEQUENTIAL:                                                     │
│                                                                 │
│  compute_a: ████████████                                        │
│  compute_b:             ████████                                │
│  compute_c:                     ████████████████                │
│  Time: ═══════════════════════════════════════►                 │
│                                                                 │
│  PARALLEL:                                                      │
│                                                                 │
│  compute_a: ████████████                                        │
│  compute_b: ████████                                            │
│  compute_c: ████████████████                                    │
│  Time: ════════════════►                                        │
└─────────────────────────────────────────────────────────────────┘
```

**When to use:**
- ✅ Multiple independent computations
- ✅ No data dependencies between tasks
- ✅ Each task is substantial (worth the overhead)

---

### 5. `pipeline_stage` — Producer-Consumer

**Definition:** Data flows through multiple processing stages that can overlap.

**Before:**
```python
for file in files:
    data = read_file(file)       # 100ms (I/O)
    processed = transform(data)   # 200ms (CPU)
    write_result(processed)       # 100ms (I/O)
# Per file: 400ms
```

**After (pipeline with queues):**
```python
from queue import Queue
from threading import Thread

def reader(files, output_queue):
    for file in files:
        data = read_file(file)
        output_queue.put(data)
    output_queue.put(None)

def processor(input_queue, output_queue):
    while (data := input_queue.get()) is not None:
        output_queue.put(transform(data))
    output_queue.put(None)

def writer(input_queue):
    while (data := input_queue.get()) is not None:
        write_result(data)

q1, q2 = Queue(), Queue()
Thread(target=reader, args=(files, q1)).start()
Thread(target=processor, args=(q1, q2)).start()
Thread(target=writer, args=(q2,)).start()
```

**How it works:**
```
┌─────────────────────────────────────────────────────────────────┐
│  Time:    0    100   200   300   400   500   600                │
│           │     │     │     │     │     │     │                 │
│  Reader:  [R1]─[R2]─[R3]─[R4]─►                                 │
│               ↓    ↓    ↓                                       │
│  Process:    [P1]──[P2]──[P3]──[P4]─►                           │
│                   ↓    ↓    ↓                                   │
│  Writer:        [W1]─[W2]─[W3]─[W4]─►                           │
│                                                                 │
│  All 3 stages working simultaneously!                           │
│  Throughput: 1 file every 200ms (bottleneck stage)              │
└─────────────────────────────────────────────────────────────────┘
```

**When to use:**
- ✅ Multi-step processing (ETL)
- ✅ Different stages have different speeds
- ✅ Stages are I/O and CPU mixed

---

### 6. `vectorize_candidate` — NumPy/Numba

**Definition:** Element-wise numeric operations that can be replaced with NumPy or accelerated with Numba.

**Before:**
```python
result = []
for i in range(len(a)):
    result.append(a[i] * b[i] + c[i])
```

**After (NumPy):**
```python
import numpy as np
a = np.array(a)
b = np.array(b)
c = np.array(c)
result = a * b + c  # Vectorized!
```

**After (Numba for complex ops):**
```python
from numba import njit

@njit
def compute(a, b, c):
    result = np.empty_like(a)
    for i in range(len(a)):
        result[i] = a[i] * b[i] + c[i]
    return result
```

**Why it's fast:**
- NumPy operations are implemented in C
- Uses SIMD instructions internally
- No Python loop overhead

**When to use:**
- ✅ Numeric arrays
- ✅ Element-wise operations
- ✅ Mathematical transformations
- ❌ Complex logic with branches

---

## C/OpenMP Candidate Types

C has **4 candidate types** that map to OpenMP directives.

### 1. `loop_map` — `#pragma omp parallel for`

**Definition:** A for loop with independent iterations.

**Before:**
```c
for(int i = 0; i < N; i++) {
    result[i] = compute(data[i]);
}
```

**After:**
```c
#pragma omp parallel for
for(int i = 0; i < N; i++) {
    result[i] = compute(data[i]);
}
```

**How it works:**
- OpenMP automatically divides iterations among threads
- Each thread gets a portion: Thread 0 → i=0..N/4, Thread 1 → i=N/4..N/2, etc.

---

### 2. `reduction` — `#pragma omp parallel for reduction(...)`

**Definition:** A loop with an accumulator variable.

**Before:**
```c
double sum = 0;
for(int i = 0; i < N; i++) {
    sum += data[i];
}
```

**After:**
```c
double sum = 0;
#pragma omp parallel for reduction(+:sum)
for(int i = 0; i < N; i++) {
    sum += data[i];
}
```

**How it works:**
```
┌─────────────────────────────────────────────────────────────────┐
│  1. Each thread gets private copy: sum_thread = 0               │
│  2. Each thread accumulates its portion                         │
│  3. OpenMP combines: sum = sum_t0 + sum_t1 + sum_t2 + sum_t3   │
└─────────────────────────────────────────────────────────────────┘
```

**Supported operators:** `+`, `-`, `*`, `&`, `|`, `^`, `&&`, `||`, `max`, `min`

---

### 3. `task_graph` — `#pragma omp parallel sections`

**Definition:** Independent code blocks that can run concurrently.

**Before:**
```c
double a = compute_a();
double b = compute_b();
double c = compute_c();
```

**After:**
```c
double a, b, c;
#pragma omp parallel sections
{
    #pragma omp section
    { a = compute_a(); }
    
    #pragma omp section
    { b = compute_b(); }
    
    #pragma omp section
    { c = compute_c(); }
}
```

---

### 4. `vectorize` — `#pragma omp simd`

**Definition:** Inner loops suitable for SIMD (Single Instruction, Multiple Data).

**Before:**
```c
for(int i = 0; i < N; i++) {
    a[i] = b[i] * c[i];
}
```

**After:**
```c
#pragma omp simd
for(int i = 0; i < N; i++) {
    a[i] = b[i] * c[i];
}
```

**How it works:**
```
┌─────────────────────────────────────────────────────────────────┐
│  SCALAR: Process 1 element per instruction                      │
│  a[0]=b[0]*c[0], a[1]=b[1]*c[1], a[2]=b[2]*c[2], a[3]=b[3]*c[3] │
│  4 instructions                                                 │
│                                                                 │
│  SIMD (AVX): Process 8 elements per instruction                 │
│  ┌────┬────┬────┬────┬────┬────┬────┬────┐                      │
│  │a[0]│a[1]│a[2]│a[3]│a[4]│a[5]│a[6]│a[7]│  = 1 instruction!   │
│  └────┴────┴────┴────┴────┴────┴────┴────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Comparison: Python vs C

| Pattern | Python | C/OpenMP |
|---------|--------|----------|
| **Independent loops** | `joblib.Parallel` | `#pragma omp parallel for` |
| **Reduction** | Chunked + combine | `reduction(+:sum)` |
| **Task parallelism** | `concurrent.futures` | `#pragma omp sections` |
| **Vectorization** | NumPy/Numba | `#pragma omp simd` |
| **I/O concurrency** | `ThreadPoolExecutor` | Same as CPU (no GIL) |
| **Pipeline** | `Queue` + threads | Manual (not in OpenMP) |

### Key Differences

| Aspect | Python | C |
|--------|--------|---|
| **GIL** | Exists (use processes) | No GIL |
| **Overhead** | High (process spawn) | Low (threads) |
| **Memory** | Separate per process | Shared |
| **Best for** | I/O, high-level tasks | CPU-intensive, low-level |

---

## Quick Reference

### When to use which pattern:

```
┌─────────────────────────────────────────────────────────────────┐
│  Q: Is it a loop?                                               │
│  ├─ YES: Is each iteration independent?                        │
│  │       ├─ YES: Does it accumulate (sum, max)?                │
│  │       │       ├─ YES → reduction                            │
│  │       │       └─ NO  → loop_map                             │
│  │       └─ NO: Is it a small inner loop?                      │
│  │               ├─ YES → vectorize                            │
│  │               └─ NO  → probably not parallelizable          │
│  └─ NO: Are there multiple independent functions?              │
│         ├─ YES → task_graph                                    │
│         └─ NO: Is it I/O operations?                           │
│                 ├─ YES → io_batch                              │
│                 └─ NO: Is it staged processing?                │
│                         ├─ YES → pipeline_stage                │
│                         └─ NO  → probably not parallelizable   │
└─────────────────────────────────────────────────────────────────┘
```
