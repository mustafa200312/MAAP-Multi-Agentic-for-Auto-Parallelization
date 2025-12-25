#include <stdio.h>
#include <unistd.h>

// Mock computationally heavy functions
void heavy_task_1() {
    int sum = 0;
    for(int i=0; i<1000000; i++) sum += i;
    printf("Task 1 Done\n");
}

void heavy_task_2() {
    int prod = 1;
    for(int i=1; i<1000; i++) prod *= i;
    printf("Task 2 Done\n");
}

int main() {
    // These two tasks are independent and should be parallelized into sections
    heavy_task_1();
    heavy_task_2();
    
    return 0;
}
