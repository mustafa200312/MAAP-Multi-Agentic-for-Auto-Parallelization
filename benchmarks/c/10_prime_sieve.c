#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

int is_prime(int n) {
    if (n <= 1) return 0;
    if (n <= 3) return 1;
    if (n % 2 == 0 || n % 3 == 0) return 0;
    
    for (int i = 5; i * i <= n; i = i + 6) {
        if (n % i == 0 || n % (i + 2) == 0) return 0;
    }
    return 1;
}

int count_primes(int start, int end) {
    int count = 0;
    
    for (int i = start; i < end; i++) {
        if (is_prime(i)) {
            count++;
        }
    }
    return count;
}

int main() {
    int limit = 500000;
    
    printf("Counting primes up to %d...\n", limit);
    clock_t start = clock();
    
    int result = count_primes(0, limit);
    
    clock_t end = clock();
    double time_spent = (double)(end - start) / CLOCKS_PER_SEC;
    
    printf("Found %d primes.\n", result);
    printf("Elapsed: %.2fs\n", time_spent);
    return 0;
}
