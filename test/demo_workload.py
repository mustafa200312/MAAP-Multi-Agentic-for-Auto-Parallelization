import time
import math
import random

def complex_feature_engineering(row_data):
    """
    Simulates a heavy CPU-bound transformation on a row of data.
    Think of this as applying complex mathematical models or data augmentation.
    """
    # 1. Simulate I/O or variable delay (e.g. network latency or disk read)
    time.sleep(0.05 + random.random() * 0.05) 
    
    # 2. Heavy Math Computation (CPU bound)
    result = 0
    for val in row_data:
        # Some arbitrary complex calculation
        result += math.sin(val) * math.tan(math.cos(val)) + math.log(abs(val) + 1)
        result = math.pow(result % 100, 1.01)
    
    return result

def main():
    # Generate a dataset: 50 rows, each with 2000 "features"
    print("Generating synthetic dataset (50 rows x 2000 features)...")
    dataset = [
        [random.uniform(-1000, 1000) for _ in range(2000)] 
        for _ in range(50)
    ]
    
    print("Starting sequential processing...")
    start_time = time.time()
    
    transformed_data = []
    
    # INDEPENDENT LOOP: Ideal for parallelization
    for i, row in enumerate(dataset):
        processed_val = complex_feature_engineering(row)
        transformed_data.append(processed_val)
        print(f"Propcessed row {i+1}/{len(dataset)}", end="\r")
        
    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.4f} seconds")
    print(f"Sample results: {transformed_data[:3]}")

if __name__ == "__main__":
    main()
