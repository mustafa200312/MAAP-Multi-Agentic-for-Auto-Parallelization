import time
import math

def cpu_heavy(n):
    results = []
    print(f"Starting CPU loop with {n} iterations...")
    for i in range(n):
        val = math.sin(i) * math.cos(i) + math.tan(i) if i % 100 != 0 else 0
        for _ in range(100):
            val = math.sqrt(abs(val) + 1.0)
        results.append(val)
    return len(results)

if __name__ == "__main__":
    start = time.time()
    cpu_heavy(5000)
    print(f"Elapsed: {time.time() - start:.2f}s")
