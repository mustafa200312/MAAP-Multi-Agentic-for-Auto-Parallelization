#include <stdio.h>
#include <time.h>
#include <math.h>

double task_a() {
    double res = 0;
    for(int i=0; i<100000; i++) res += sin(i);
    return res;
}

double task_b() {
    double res = 0;
    for(int i=0; i<100000; i++) res += cos(i);
    return res;
}

int main() {
    clock_t start = clock();
    
    double a = task_a();
    double b = task_b();
    
    clock_t end = clock();
    double time_spent = (double)(end - start) / CLOCKS_PER_SEC;
    
    printf("Result: %.2f\n", a + b);
    printf("Elapsed: %.2fs\n", time_spent);
    return 0;
}
