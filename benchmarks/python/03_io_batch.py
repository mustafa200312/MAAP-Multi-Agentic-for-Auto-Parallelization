import time
import random

def fetch_url(url_id):
    # Simulates network latency
    delay = random.uniform(0.1, 0.5)
    time.sleep(delay)
    return f"Data from {url_id} (latency: {delay:.2f}s)"

def download_all(urls):
    print(f"Downloading {len(urls)} URLs...")
    results = []
    for url in urls:
        data = fetch_url(url)
        results.append(data)
    return results

if __name__ == "__main__":
    urls = list(range(20))
    start = time.time()
    results = download_all(urls)
    print(f"Downloaded {len(results)} items")
    print(f"Elapsed: {time.time() - start:.2f}s")
