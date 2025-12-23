#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define SIZE 1000000

int main() {
    double *arr = (double*)malloc(SIZE * sizeof(double));
    double sum = 0.0;
    double max_val = 0.0;
    int i;
    
    // Initialize array - parallelizable (no dependencies)
    for (i = 0; i < SIZE; i++) {
        arr[i] = sin(i * 0.001) * cos(i * 0.002);
    }
    
    // Compute sum - reduction pattern
    for (i = 0; i < SIZE; i++) {
        sum += arr[i];
    }
    
    // Find maximum - reduction pattern  
    for (i = 0; i < SIZE; i++) {
        if (arr[i] > max_val) {
            max_val = arr[i];
        }
    }
    
    printf("Sum: %.6f\n", sum);
    printf("Max: %.6f\n", max_val);
    
    free(arr);
    return 0;
}
