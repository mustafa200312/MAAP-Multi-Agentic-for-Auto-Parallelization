import time
import random

def apply_convolution(input_grid, rows, cols):
    output_grid = [[0.0] * cols for _ in range(rows)]
    
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            val = 0.0
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    val += input_grid[r + dr][c + dc]
            output_grid[r][c] = val / 9.0
            
    return output_grid

if __name__ == "__main__":
    R, C = 200, 200
    grid = [[random.random() for _ in range(C)] for _ in range(R)]
    
    print(f"Applying convolution to {R}x{C} image...")
    start = time.time()
    
    for i in range(10):
        grid = apply_convolution(grid, R, C)
        
    print(f"Elapsed: {time.time() - start:.2f}s")
    print(f"Center pixel: {grid[R//2][C//2]:.4f}")
