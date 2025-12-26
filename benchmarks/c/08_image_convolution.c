#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

void convolution(double *input, double *output, int rows, int cols) {
    for (int r = 1; r < rows - 1; r++) {
        for (int c = 1; c < cols - 1; c++) {
            double sum = 0.0;
            for (int dr = -1; dr <= 1; dr++) {
                for (int dc = -1; dc <= 1; dc++) {
                    sum += input[(r+dr)*cols + (c+dc)];
                }
            }
            output[r*cols + c] = sum / 9.0;
        }
    }
}

int main() {
    int R = 2000;
    int C = 2000;
    double *input = (double*)malloc(R * C * sizeof(double));
    double *output = (double*)malloc(R * C * sizeof(double));
    
    for(int i=0; i<R*C; i++) input[i] = (double)(i % 255);
    
    printf("Applying convolution to %dx%d image...\n", R, C);
    clock_t start = clock();
    
    for(int i=0; i<5; i++) {
        convolution(input, output, R, C);
        double *temp = input;
        input = output;
        output = temp;
    }
    
    clock_t end = clock();
    printf("Elapsed: %.2fs\n", (double)(end - start) / CLOCKS_PER_SEC);
    
    free(input); free(output);
    return 0;
}
