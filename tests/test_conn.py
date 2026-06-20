import asyncio
import websockets


async def main():

    async with websockets.connect("ws://localhost:8765"):

        print("Connected!")

        await asyncio.sleep(5)


for i in range(5):
    asyncio.run(main())
