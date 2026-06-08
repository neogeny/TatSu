import asyncio
import concurrent.futures
from pathlib import Path


def heavy_computation(x: int):
    # This runs in a separate process, bypassing the GIL
    return sum(i * i for i in range(10**7)) + x


async def main():
    loop = asyncio.get_running_loop()

    # We use a ProcessPoolExecutor for true parallel execution
    with concurrent.futures.ProcessPoolExecutor() as pool:
        # Create a list of tasks
        tasks = [loop.run_in_executor(pool, heavy_computation, i) for i in range(4)]

        # Await all parallel processes
        results = await asyncio.gather(*tasks)
        print(f"Results: {results}")


if __name__ == "__main__":
    asyncio.run(main())
