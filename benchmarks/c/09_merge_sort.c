#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>

void merge(int *arr, int l, int m, int r) {
    int i, j, k;
    int n1 = m - l + 1;
    int n2 = r - m;

    int *L = (int*)malloc(n1 * sizeof(int));
    int *R = (int*)malloc(n2 * sizeof(int));

    for (i = 0; i < n1; i++) L[i] = arr[l + i];
    for (j = 0; j < n2; j++) R[j] = arr[m + 1 + j];

    i = 0; 
    j = 0; 
    k = l; 
    while (i < n1 && j < n2) {
        if (L[i] <= R[j]) arr[k++] = L[i++];
        else arr[k++] = R[j++];
    }

    while (i < n1) arr[k++] = L[i++];
    while (j < n2) arr[k++] = R[j++];
    
    free(L);
    free(R);
}

void merge_sort(int *arr, int l, int r) {
    if (l < r) {
        int m = l + (r - l) / 2;

        merge_sort(arr, l, m);
        merge_sort(arr, m + 1, r);

        merge(arr, l, m, r);
    }
}

int main() {
    int n = 500000;
    int *arr = (int*)malloc(n * sizeof(int));
    
    srand(42);
    for(int i=0; i<n; i++) arr[i] = rand() % n;
    
    printf("Sorting %d elements with Merge Sort...\n", n);
    clock_t start = clock();
    
    merge_sort(arr, 0, n - 1);
    
    clock_t end = clock();
    double time_spent = (double)(end - start) / CLOCKS_PER_SEC;
    
    printf("Elapsed: %.2fs\n", time_spent);
    
    int sorted = 1;
    for(int i=0; i<n-1; i++) {
        if(arr[i] > arr[i+1]) { sorted = 0; break; }
    }
    printf("Sorted: %s\n", sorted ? "YES" : "NO");
    
    free(arr);
    return 0;
}
