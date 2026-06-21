import time

start = time.monotonic_ns()
time.sleep(0.1)
end = time.monotonic_ns()

diff = end - start
print(f"Raw diff for 0.1s sleep: {diff:,} ns")
print(f"Expected around:          100,000,000 ns")
