async def worker_logic(bar_id: int, progress: MultiProgress):
    # The user just focuses on their own work and calls .update()
    for i in range(1, 101):
        await asyncio.sleep(0.05)
        progress.update(bar_id, i)


async def main():
    # Concurrency management is fully absorbed by your library here:
    async with MultiProgress(total_bars=3) as progress:
        # The user just runs their own workers parallelly
        await asyncio.gather(
            worker_logic(0, progress),
            worker_logic(1, progress),
            worker_logic(2, progress),
        )


if __name__ == "__main__":
    asyncio.run(main())
