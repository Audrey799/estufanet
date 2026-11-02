import asyncio, json, random, sys, websockets

device_id = sys.argv[1] if len(sys.argv) > 1 else "sensor1"

async def main():
    async with websockets.connect("ws://127.0.0.1:8000/ws") as ws:
        while True:
            leitura = {
                "device_id": device_id,
                "temp": round(random.uniform(20, 35), 1),
                "umid": round(random.uniform(40, 80), 1),
            }
            await ws.send(json.dumps(leitura))
            await asyncio.sleep(1)

asyncio.run(main())