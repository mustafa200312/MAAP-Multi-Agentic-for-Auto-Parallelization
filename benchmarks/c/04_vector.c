#include <stdio.h>
#include <time.h>
#include <stdlib.h>

void vector_ops(double *a, double *b, double *c, int n) {
    for(int i=0; i<n; i++) {
        c[i] = a[i] * b[i] + (a[i] - b[i]);
    }
}

int main() {
    int n = 1000000;
    double *a = (double*)malloc(n * sizeof(double));
    double *b = (double*)malloc(n * sizeof(double));
    double *c = (double*)malloc(n * sizeof(double));
    
    for(int i=0; i<n; i++) {
        a[i] = (double)i;
        b[i] = (double)(n-i);
    }
    
    clock_t start = clock();
    vector_ops(a, b, c, n);
    clock_t end = clock();
    
    double time_spent = (double)(end - start) / CLOCKS_PER_SEC;
    printf("Result[0]: %.2f\n", c[0]);
    printf("Elapsed: %.2fs\n", time_spent);
    
    free(a); free(b); free(c);
    return 0;
}
