import csv
import glob
import os
import re
import statistics
 
import matplotlib
matplotlib.use("Agg")  # salva em arquivo, sem abrir janela
import matplotlib.pyplot as plt
 
PASTA_SAIDA = "graficos"
os.makedirs(PASTA_SAIDA, exist_ok=True)
plt.rcParams.update({"font.size": 11, "axes.grid": True, "grid.alpha": 0.3})
 
 
# ---------- leitura ----------
def ler_csv(caminho):
    with open(caminho, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))
 
 
def num(valor):
    """Converte texto em float; vazio vira None. Aceita virgula decimal."""
    valor = (valor or "").strip().replace(",", ".")
    return float(valor) if valor else None
 
 
def numero_do_param(texto):
    """'1105 bytes/msg' -> 1105 ; '5 clientes' -> 5"""
    return int(re.search(r"\d+", texto).group())
 
 
def salvar(nome):
    caminho = os.path.join(PASTA_SAIDA, nome)
    plt.tight_layout()
    plt.savefig(caminho, dpi=200)
    plt.close()
    print("gerado:", caminho)
 
 
# ---------- carregar dados ----------
resultados = {}  # condicao -> lista de linhas
for arq in sorted(glob.glob("resultados_*.csv")):
    for linha in ler_csv(arq):
        resultados.setdefault(linha["condicao"], []).append(linha)
 
rtt_bruto = {}  # condicao -> lista de RTTs
for arq in sorted(glob.glob("rtt_bruto_*.csv")):
    cond = os.path.basename(arq)[len("rtt_bruto_"):-len(".csv")]
    rtt_bruto[cond] = [num(l["rtt_ms"]) for l in ler_csv(arq)]
 
if not resultados:
    raise SystemExit("Nenhum resultados_*.csv encontrado nesta pasta.")
 
 
def linhas(cond, exp):
    return [l for l in resultados.get(cond, []) if l["exp"] == exp]
 
 
# ---------- Experimento A: RTT ----------
for cond, rtts in rtt_bruto.items():
    n = len(rtts)
    media = statistics.mean(rtts)
    mediana = statistics.median(rtts)
    desvio = statistics.stdev(rtts)
 
    # A1: RTT medicao a medicao
    plt.figure(figsize=(8, 4.2))
    plt.plot(range(1, n + 1), rtts, marker="o", markersize=3, linewidth=1,
             label="RTT medido")
    plt.axhline(media, color="tab:red", linestyle="--", label=f"média = {media:.1f} ms")
    plt.axhline(mediana, color="tab:green", linestyle=":", label=f"mediana = {mediana:.1f} ms")
    plt.title(f"RTT por medição (condição: {cond}, n = {n})")
    plt.xlabel("Medição")
    plt.ylabel("RTT (ms)")
    plt.legend()
    salvar(f"A1_rtt_por_medicao_{cond}.png")
 
    # A2: histograma
    plt.figure(figsize=(7, 4.2))
    plt.hist(rtts, bins=20, edgecolor="black")
    plt.axvline(media, color="tab:red", linestyle="--", label=f"média = {media:.1f} ms")
    plt.axvline(mediana, color="tab:green", linestyle=":", label=f"mediana = {mediana:.1f} ms")
    plt.title(f"Distribuição do RTT (condição: {cond}, n = {n})")
    plt.xlabel("RTT (ms)")
    plt.ylabel("Frequência (nº de medições)")
    plt.legend()
    salvar(f"A2_histograma_rtt_{cond}.png")
 
    print(f"[{cond}] n={n} média={media:.3f} mediana={mediana:.3f} "
          f"desvio={desvio:.3f} min={min(rtts):.3f} max={max(rtts):.3f} ms")
 
# A3: comparacao entre condicoes (so aparece se houver mais de uma)
if len(rtt_bruto) > 1:
    conds = list(rtt_bruto)
    medias = [statistics.mean(rtt_bruto[c]) for c in conds]
    medianas = [statistics.median(rtt_bruto[c]) for c in conds]
    desvios = [statistics.stdev(rtt_bruto[c]) for c in conds]
    x = range(len(conds))
    larg = 0.27
    plt.figure(figsize=(7.5, 4.2))
    plt.bar([i - larg for i in x], medias, larg, label="Média")
    plt.bar(list(x), medianas, larg, label="Mediana")
    plt.bar([i + larg for i in x], desvios, larg, label="Desvio-padrão")
    plt.xticks(list(x), conds)
    plt.title("RTT por condição de rede")
    plt.xlabel("Condição")
    plt.ylabel("Tempo (ms)")
    plt.legend()
    salvar("A3_rtt_comparacao_condicoes.png")
 
# ---------- Experimento B: throughput ----------
for cond in resultados:
    b = linhas(cond, "B_throughput")
    if not b:
        continue
    b.sort(key=lambda l: numero_do_param(l["param"]))
    tamanhos = [numero_do_param(l["param"]) for l in b]
    mbps = [num(l["mbps"]) for l in b]
    tempo = [num(l["media_ms"]) for l in b]
    rotulos = [str(t) for t in tamanhos]
 
    # B1: vazao util por tamanho
    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    barras = ax.bar(rotulos, mbps, color="tab:blue")
    ax.set_yscale("log")
    ax.set_title(f"Vazão útil por tamanho de mensagem (condição: {cond})")
    ax.set_xlabel("Tamanho da mensagem (bytes)")
    ax.set_ylabel("Vazão útil (Mbit/s, escala log)")
    for barra, v in zip(barras, mbps):
        ax.annotate(f"{v:g}", (barra.get_x() + barra.get_width() / 2, v),
                    ha="center", va="bottom", fontsize=9)
    salvar(f"B1_vazao_por_tamanho_{cond}.png")
 
    # B2: vazao (barras) + tempo de resposta (linha, eixo secundario)
    fig, ax1 = plt.subplots(figsize=(7.5, 4.4))
    ax1.bar(rotulos, mbps, color="tab:blue", alpha=0.8, label="Vazão (Mbit/s)")
    ax1.set_yscale("log")
    ax1.set_xlabel("Tamanho da mensagem (bytes)")
    ax1.set_ylabel("Vazão útil (Mbit/s, escala log)")
    ax2 = ax1.twinx()
    ax2.plot(rotulos, tempo, color="tab:red", marker="o", label="Tempo de resposta médio (ms)")
    ax2.set_ylabel("Tempo de resposta médio (ms)")
    ax2.set_ylim(0, max(tempo) * 1.4)
    ax2.grid(False)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left")
    ax1.set_title(f"Vazão e tempo de resposta por tamanho (condição: {cond})")
    salvar(f"B2_vazao_e_tempo_{cond}.png")
 
# ---------- Experimento C: concorrencia ----------
for cond in resultados:
    c = linhas(cond, "C_concorrencia")
    if not c:
        continue
    c.sort(key=lambda l: numero_do_param(l["param"]))
    clientes = [str(numero_do_param(l["param"])) for l in c]
    atraso = [num(l["media_ms"]) for l in c]
    desvio = [num(l["desvio_ms"]) for l in c]
    taxa = [num(l["msgs_por_s"]) for l in c]
 
    # C1: atraso medio (com desvio como barra de erro)
    plt.figure(figsize=(6.5, 4.2))
    barras = plt.bar(clientes, atraso, yerr=desvio, capsize=4, color="tab:orange")
    for barra, v in zip(barras, atraso):
        plt.annotate(f"{v:.1f}", (barra.get_x() + barra.get_width() / 2, v),
                     ha="center", va="bottom", fontsize=9)
    plt.title(f"Atraso médio por nº de clientes (condição: {cond})")
    plt.xlabel("Clientes simultâneos")
    plt.ylabel("Atraso médio (ms)")
    salvar(f"C1_atraso_por_clientes_{cond}.png")
 
    # C2: taxa de mensagens
    plt.figure(figsize=(6.5, 4.2))
    barras = plt.bar(clientes, taxa, color="tab:green")
    for barra, v in zip(barras, taxa):
        plt.annotate(f"{v:.1f}", (barra.get_x() + barra.get_width() / 2, v),
                     ha="center", va="bottom", fontsize=9)
    plt.title(f"Taxa total de mensagens por nº de clientes (condição: {cond})")
    plt.xlabel("Clientes simultâneos")
    plt.ylabel("Mensagens por segundo")
    salvar(f"C2_taxa_por_clientes_{cond}.png")
 
print("\nPronto! Veja a pasta:", os.path.abspath(PASTA_SAIDA))