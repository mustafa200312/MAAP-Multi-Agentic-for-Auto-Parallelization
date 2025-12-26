#include <stdio.h>
#include <stdlib.h>
#include <time.h>

long monte_carlo_pi_part(long n) {
    long count = 0;
    unsigned int seed = (unsigned int)time(NULL); 
    
    for (long i = 0; i < n; i++) {
        double x = (double)rand_r(&seed) / RAND_MAX;
        double y = (double)rand_r(&seed) / RAND_MAX;
        if (x*x + y*y <= 1.0) {
            count++;
        }
    }
    return count;
}

int main() {
    long total_samples = 10000000;
    long count = 0;
    
    clock_t start = clock();
    
    for (long i = 0; i < total_samples; i++) {
        double x = (double)rand() / RAND_MAX;
        double y = (double)rand() / RAND_MAX;
        if (x*x + y*y <= 1.0) count++;
    }
    
    clock_t end = clock();
    double pi = 4.0 * count / total_samples;
    double time_spent = (double)(end - start) / CLOCKS_PER_SEC;
    
    printf("Pi Estimate: %.5f\n", pi);
    printf("Elapsed: %.2fs\n", time_spent);
    return 0;
}
