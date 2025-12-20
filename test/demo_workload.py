import time
import math

def expensive_function(n):
    """Simulates a heavy computation."""
    time.sleep(0.1) # Simulate I/O or processing delay
    return math.factorial(n % 50)

def main():
    print("Starting heavy workload...")
    start_time = time.time()
    
    data = list(range(20))
    results = []
    
    # This loop is independent and slow -> ideal for parallelization
    for item in data:
        results.append(expensive_function(item))
        
    end_time = time.time()
    print(f"Workload finished in {end_time - start_time:.4f} seconds")
    print(f"First 5 results: {results[:5]}")

if __name__ == "__main__":
    main()
