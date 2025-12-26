import time
import random

def element_wise_ops(n):
    print(f"Processing {n} elements...")
    a = [random.random() for _ in range(n)]
    b = [random.random() for _ in range(n)]
    result = [0.0] * n
    
    for i in range(n):
        result[i] = a[i] * b[i] + (a[i] / (b[i] + 1.0))
        
    return result[0]

if __name__ == "__main__":
    start = time.time()
    element_wise_ops(1000000)
    print(f"Elapsed: {time.time() - start:.2f}s")
