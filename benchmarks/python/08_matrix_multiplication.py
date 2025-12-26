import time
import random

def create_matrix(rows, cols):
    return [[random.random() for _ in range(cols)] for _ in range(rows)]

def matrix_multiply(A, B):
    n = len(A)
    m = len(B[0])
    k = len(B)
    
    C = [[0] * m for _ in range(n)]
    
    print(f"Multiplying {n}x{k} and {k}x{m} matrices...")
    
    for i in range(n):
        for j in range(m):
            sum_val = 0
            for p in range(k):
                sum_val += A[i][p] * B[p][j]
            C[i][j] = sum_val
            
    return C

if __name__ == "__main__":
    N = 200
    A = create_matrix(N, N)
    B = create_matrix(N, N)
    
    start = time.time()
    C = matrix_multiply(A, B)
    print(f"Elapsed: {time.time() - start:.2f}s")
    print(f"C[0][0] = {C[0][0]:.2f}")
