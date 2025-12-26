import time
import math

def stage_read(items):
    return [x for x in items]

def stage_process(items):
    results = []
    for x in items:
        val = x
        for _ in range(500):
            val = math.sin(val) * math.cos(val) + x
        results.append(val)
    return results

def stage_write(results):
    return len(results)

def pipeline_flow(data):
    raw = stage_read(data)
    processed = stage_process(raw)
    count = stage_write(processed)
    return count

if __name__ == "__main__":
    data = list(range(1000))
    start = time.time()
    pipeline_flow(data)
    print(f"Elapsed: {time.time() - start:.2f}s")
