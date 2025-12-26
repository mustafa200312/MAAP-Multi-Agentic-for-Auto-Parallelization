import time
import random

def calculate_stats(data):
    print(f"Calculating stats for {len(data)} items...")
    
    total = 0
    max_val = float('-inf')
    min_val = float('inf')
    product = 1.0
    
    for x in data:
        total += x
        if x > max_val:
            max_val = x
        if x < min_val:
            min_val = x
        product *= (1.0 + x * 0.000001) 
        
    return total, max_val, min_val

if __name__ == "__main__":
    data = [random.random() for _ in range(1000000)]
    start = time.time()
    stats = calculate_stats(data)
    print(f"Stats: {stats}")
    print(f"Elapsed: {time.time() - start:.2f}s")
