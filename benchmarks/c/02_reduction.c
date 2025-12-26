#include <stdio.h>
#include <time.h>

#define N 1000000

double calculate_sum(double *data) {
    double total = 0.0;
    for (int i = 0; i < N; i++) {
        total += data[i];
    }
    return total;
}

int main() {
    static double data[N];
    for(int i=0; i<N; i++) data[i] = 1.0;
    
    clock_t start = clock();
    double sum = calculate_sum(data);
    clock_t end = clock();
    
    double time_spent = (double)(end - start) / CLOCKS_PER_SEC;
    printf("Sum: %.2f\n", sum);
    printf("Elapsed: %.2fs\n", time_spent);
    return 0;
}
