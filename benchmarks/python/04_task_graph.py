import time
import math

def heavy_task_a():
    print("Task A started...")
    result = 0
    for i in range(1000000):
        result += math.sin(i)
    return result

def heavy_task_b():
    print("Task B started...")
    result = 0
    for i in range(1000000):
        result += math.cos(i)
    return result

def heavy_task_c():
    print("Task C started...")
    result = 0
    for i in range(1000000):
        result += math.tan(i) if i % 100 != 0 else 0
    return result

def run_tasks():
    res_a = heavy_task_a()
    res_b = heavy_task_b()
    res_c = heavy_task_c()
    
    return res_a + res_b + res_c

if __name__ == "__main__":
    start = time.time()
    total = run_tasks()
    print(f"Total: {total:.2f}")
    print(f"Elapsed: {time.time() - start:.2f}s")
