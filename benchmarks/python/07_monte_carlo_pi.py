import time
import random

def monte_carlo_pi_part(n):
    count = 0
    for _ in range(n):
        x = random.random()
        y = random.random()
        if x*x + y*y <= 1.0:
            count += 1
    return count

def estimate_pi(total_samples):
    print(f"Estimating Pi using {total_samples} Monte Carlo samples...")
    
    chunks = 10
    samples_per_chunk = total_samples // chunks
    
    total_inside = 0
    for _ in range(chunks):
        total_inside += monte_carlo_pi_part(samples_per_chunk)
        
    pi_estimate = 4.0 * total_inside / total_samples
    return pi_estimate

if __name__ == "__main__":
    start = time.time()
    pi = estimate_pi(5000000)
    print(f"Pi Estimate: {pi}")
    print(f"Elapsed: {time.time() - start:.2f}s")
