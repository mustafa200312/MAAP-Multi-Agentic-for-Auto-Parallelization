
#include <stdio.h>
#include <omp.h>
int main() { 
    // Just print same thing, maybe different order?
    // Actually for this test, same order is fine.
    printf("World\n"); 
    printf("Hello\n"); 
    return 0; 
}
