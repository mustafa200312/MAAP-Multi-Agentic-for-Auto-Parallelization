import time
import math
import random

def nbody_step(positions, velocities, masses, dt, n):
    forces_x = [0.0] * n
    forces_y = [0.0] * n
    
    for i in range(n):
        fx = 0.0
        fy = 0.0
        for j in range(n):
            if i != j:
                dx = positions[j][0] - positions[i][0]
                dy = positions[j][1] - positions[i][1]
                dist = math.sqrt(dx*dx + dy*dy) + 1e-9
                f = (masses[i] * masses[j]) / (dist * dist)
                fx += f * dx / dist
                fy += f * dy / dist
        forces_x[i] = fx
        forces_y[i] = fy

    for i in range(n):
        velocities[i][0] += forces_x[i] * dt / masses[i]
        velocities[i][1] += forces_y[i] * dt / masses[i]
        positions[i][0] += velocities[i][0] * dt
        positions[i][1] += velocities[i][1] * dt

if __name__ == "__main__":
    N = 500
    positions = [[random.random()*100, random.random()*100] for _ in range(N)]
    velocities = [[0.0, 0.0] for _ in range(N)]
    masses = [random.random() for _ in range(N)]
    
    print(f"Simulating {N} bodies for 10 steps...")
    start = time.time()
    
    for _ in range(10):
        nbody_step(positions, velocities, masses, 0.01, N)
        
    print(f"Elapsed: {time.time() - start:.2f}s")
