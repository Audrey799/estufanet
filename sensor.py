import asyncio, json, random, sys, time, websockets

device_id = sys.argv[1] if len(sys.argv) > 1 else "sensor1"
token = "tk-" + device_id          # mesmo padrão do servidor

async def main():
    while True:                    # se cair, tenta reconectar
        try:
            async with websockets.connect("ws://127.0.0.1:8000/ws") as ws:
                print(f"{device_id} conectado")
                while True:
                    leitura = {
                        "tipo": "leitura",
                        "device_id": device_id,
                        "token": token,
                        "temp": round(random.uniform(20, 35), 1),
                        "umid": round(random.uniform(40, 80), 1),
                    }
                    t0 = time.perf_counter()
                    await ws.send(json.dumps(leitura))
                    resposta = json.loads(await ws.recv())
                    rtt = (time.perf_counter() - t0) * 1000
                    print(f"temp={leitura['temp']} resposta={resposta} RTT={rtt:.2f} ms")
                    await asyncio.sleep(1)
        except (OSError, websockets.ConnectionClosed):
            print("Servidor indisponível, tentando de novo em 3 s...")
            await asyncio.sleep(3)

asyncio.run(main())
