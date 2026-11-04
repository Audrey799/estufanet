import asyncio, json, time, statistics, csv, websockets

HOST = input("Endereço do servidor (Enter = 127.0.0.1): ").strip() or "127.0.0.1"
COND = input("Condição (ex: local ou degradada): ").strip() or "local"
URL = f"ws://{HOST}:8000/ws"
linhas = []

def mensagem(dev, pad=0):
    m = {"tipo": "leitura", "device_id": dev, "token": "tk-" + dev,
         "temp": 20.0, "umid": 50.0}          # temp 20 para não gerar alerta
    if pad:
        m["pad"] = "x" * pad                  # enche a mensagem até o tamanho desejado
    return json.dumps(m)

async def cliente(dev, n, pad=0):
    """Envia n mensagens, uma por vez, esperando o ack. Devolve os RTTs (ms)."""
    texto = mensagem(dev, pad)
    rtts = []
    async with websockets.connect(URL, max_size=None) as ws:
        for _ in range(n):
            t0 = time.perf_counter()
            await ws.send(texto)
            await ws.recv()
            rtts.append((time.perf_counter() - t0) * 1000)
    return rtts, len(texto.encode())

def estat(v):
    return dict(n=len(v), media_ms=round(statistics.mean(v), 3),
                mediana_ms=round(statistics.median(v), 3),
                desvio_ms=round(statistics.stdev(v), 3) if len(v) > 1 else 0,
                min_ms=round(min(v), 3), max_ms=round(max(v), 3))

def registrar(exp, param, **dados):
    linha = dict(exp=exp, condicao=COND, param=param, **dados)
    linhas.append(linha)
    print(linha)

async def main():
    # ---- Experimento A: RTT (1 cliente, 100 medições) ----
    rtts, _ = await cliente("sensor1", 100)
    with open(f"rtt_bruto_{COND}.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["medicao", "rtt_ms"])
        for i, r in enumerate(rtts, 1):
            w.writerow([i, round(r, 3)])
    registrar("A_RTT", "1 cliente", **estat(rtts))

    # ---- Experimento B: throughput por tamanho de mensagem ----
    for pad in [0, 1000, 10000, 100000]:
        rtts, tam = await cliente("sensor1", 100, pad)
        tempo = sum(rtts) / 1000                     # segundos
        mbps = tam * len(rtts) * 8 / tempo / 1e6
        registrar("B_throughput", f"{tam} bytes/msg", **estat(rtts),
                  msgs_por_s=round(len(rtts) / tempo, 1), mbps=round(mbps, 3))

    # ---- Experimento C: concorrência (1, 2 e 5 clientes) ----
    for k in [1, 2, 5]:
        t0 = time.perf_counter()
        res = await asyncio.gather(*[cliente(f"sensor{i+1}", 200) for i in range(k)])
        dur = time.perf_counter() - t0
        todos = [r for rtts, _ in res for r in rtts]
        registrar("C_concorrencia", f"{k} clientes", **estat(todos),
                  msgs_por_s=round(len(todos) / dur, 1))

asyncio.run(main())

campos = ["exp", "condicao", "param", "n", "media_ms", "mediana_ms", "desvio_ms",
          "min_ms", "max_ms", "msgs_por_s", "mbps"]
with open(f"resultados_{COND}.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=campos, restval="")
    w.writeheader(); w.writerows(linhas)
print(f"\nPronto. Arquivos: resultados_{COND}.csv e rtt_bruto_{COND}.csv")