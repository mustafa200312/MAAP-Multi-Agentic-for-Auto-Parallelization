#include <stdio.h>
#include <math.h>
#include <time.h>

#define N 100000

void heavy_loop(double *data) {
    for (int i = 0; i < N; i++) {
        double val = sin(i * 0.01) * cos(i * 0.01);
        for (int j = 0; j < 100; j++) {
            val = sqrt(fabs(val) + 1.0);
        }
        data[i] = val;
    }
}

int main() {
    static double data[N];
    clock_t start = clock();
    
    printf("Starting C heavy loop...\n");
    heavy_loop(data);
    
    clock_t end = clock();
    double time_spent = (double)(end - start) / CLOCKS_PER_SEC;
    printf("Elapsed: %.2fs\n", time_spent);
    return 0;
}
