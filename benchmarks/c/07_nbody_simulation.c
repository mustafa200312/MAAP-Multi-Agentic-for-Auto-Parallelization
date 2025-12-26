#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

void nbody_step(double *pos_x, double *pos_y, double *vel_x, double *vel_y, double *mass, double dt, int n) {
    double *forces_x = (double*)malloc(n * sizeof(double));
    double *forces_y = (double*)malloc(n * sizeof(double));
    
    for (int i = 0; i < n; i++) {
        double fx = 0.0;
        double fy = 0.0;
        for (int j = 0; j < n; j++) {
            if (i != j) {
                double dx = pos_x[j] - pos_x[i];
                double dy = pos_y[j] - pos_y[i];
                double dist = sqrt(dx*dx + dy*dy) + 1e-9;
                double f = (mass[i] * mass[j]) / (dist * dist);
                fx += f * dx / dist;
                fy += f * dy / dist;
            }
        }
        forces_x[i] = fx;
        forces_y[i] = fy;
    }
    
    for (int i = 0; i < n; i++) {
        vel_x[i] += forces_x[i] * dt / mass[i];
        vel_y[i] += forces_y[i] * dt / mass[i];
        pos_x[i] += vel_x[i] * dt;
        pos_y[i] += vel_y[i] * dt;
    }
    
    free(forces_x);
    free(forces_y);
}

int main() {
    int N = 2000;
    double *pos_x = (double*)malloc(N * sizeof(double));
    double *pos_y = (double*)malloc(N * sizeof(double));
    double *vel_x = (double*)malloc(N * sizeof(double));
    double *vel_y = (double*)malloc(N * sizeof(double));
    double *mass = (double*)malloc(N * sizeof(double));
    
    for(int i=0; i<N; i++) {
        pos_x[i] = (double)(i % 100);
        pos_y[i] = (double)((i*2) % 100);
        vel_x[i] = 0.0;
        vel_y[i] = 0.0;
        mass[i] = 1.0;
    }
    
    printf("Simulating %d bodies...\n", N);
    clock_t start = clock();
    
    for(int s=0; s<5; s++) {
        nbody_step(pos_x, pos_y, vel_x, vel_y, mass, 0.01, N);
    }
    
    clock_t end = clock();
    printf("Elapsed: %.2fs\n", (double)(end - start) / CLOCKS_PER_SEC);
    
    free(pos_x); free(pos_y); free(vel_x); free(vel_y); free(mass);
    return 0;
}
