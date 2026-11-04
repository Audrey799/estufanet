import socket, threading, time

#parde D

HOST, PORTA, N = "127.0.0.1", 9000, 1000
PAD = "x" * 100                      # mesma carga nos dois protocolos

def resumo(nome, seqs):
    perdidos = N - len(set(seqs))
    fora = sum(1 for a, b in zip(seqs, seqs[1:]) if b < a)
    print(f"{nome}: recebidos={len(seqs)} perdidos={perdidos} fora_de_ordem={fora}")

def servidor_tcp():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORTA)); s.listen(1)
    c, _ = s.accept()
    buf, seqs = b"", []
    while True:
        d = c.recv(4096)
        if not d:
            break
        buf += d
        *completas, buf = buf.split(b"\n")       # TCP é fluxo: separamos por \n
        seqs += [int(l.split(b"|")[0]) for l in completas]
    resumo("TCP", seqs)

def servidor_udp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((HOST, PORTA)); s.settimeout(3)
    seqs = []
    while True:
        try:
            d, _ = s.recvfrom(4096)              # cada datagrama é uma mensagem
            seqs.append(int(d.split(b"|")[0]))
        except socket.timeout:
            if seqs:
                break
    resumo("UDP", seqs)

modo = input("Digite servidor ou cliente: ").strip().lower()

if modo == "servidor":
    t1 = threading.Thread(target=servidor_tcp); t2 = threading.Thread(target=servidor_udp)
    t1.start(); t2.start(); t1.join(); t2.join()
else:
    t0 = time.perf_counter()
    c = socket.socket(); c.connect((HOST, PORTA))
    for i in range(N):
        c.sendall(f"{i}|{PAD}\n".encode())
    c.close()
    print(f"TCP enviou {N} msgs em {(time.perf_counter()-t0)*1000:.1f} ms")

    t0 = time.perf_counter()
    u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for i in range(N):
        u.sendto(f"{i}|{PAD}".encode(), (HOST, PORTA))
    print(f"UDP enviou {N} msgs em {(time.perf_counter()-t0)*1000:.1f} ms")