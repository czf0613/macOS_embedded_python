import asyncio


async def main():
    print("test...")
    await asyncio.sleep(1)
    print("asyncio success!")


if __name__ == "__main__":
    asyncio.run(main())
