#include <stdio.h>
#include <stdlib.h>
#include <time.h>

void multiply_matrices(double *A, double *B, double *C, int N) {
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            double sum = 0.0;
            for (int k = 0; k < N; k++) {
                sum += A[i*N + k] * B[k*N + j];
            }
            C[i*N + j] = sum;
        }
    }
}

int main() {
    int N = 500;
    double *A = (double*)malloc(N * N * sizeof(double));
    double *B = (double*)malloc(N * N * sizeof(double));
    double *C = (double*)malloc(N * N * sizeof(double));
    
    for(int i=0; i<N*N; i++) {
        A[i] = (double)(i % 100);
        B[i] = (double)(i % 100);
    }
    
    clock_t start = clock();
    printf("Multiplying %dx%d matrices...\n", N, N);
    
    multiply_matrices(A, B, C, N);
    
    clock_t end = clock();
    double time_spent = (double)(end - start) / CLOCKS_PER_SEC;
    
    printf("Elapsed: %.2fs\n", time_spent);
    printf("C[0] = %.2f\n", C[0]);
    
    free(A); free(B); free(C);
    return 0;
}
