import asyncio


async def main():
    print("Hello, World!")
    await asyncio.sleep(1)
    print("Goodbye, World!")


if __name__ == "__main__":
    asyncio.run(main())
