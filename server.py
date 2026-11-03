import json, sqlite3, logging
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel
from fastapi.responses import FileResponse

# ---------- LOGS (console + arquivo, sempre com timestamp) ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("estufanet.log", encoding="utf-8"),
              logging.StreamHandler()],
)
log = logging.getLogger("estufanet")

# ---------- CONFIGURAÇÃO ----------
# Cada dispositivo autorizado tem um token (autenticação simples).
TOKENS = {f"sensor{i}": f"tk-sensor{i}" for i in range(1, 6)}
limiar = {"temp": 30.0}      # alerta se temperatura > este valor
paineis = set()              # painéis web conectados (para repassar dados)

app = FastAPI()

# ---------- BANCO DE DADOS (SQLite) ----------
def db():
    con = sqlite3.connect("estufanet.db")
    con.row_factory = sqlite3.Row   # permite acessar colunas por nome
    return con

def iniciar_banco():
    con = db()
    con.execute("""CREATE TABLE IF NOT EXISTS leituras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT, temp REAL, umid REAL, ts TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS alertas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT, temp REAL, limiar REAL, ts TEXT)""")
    con.commit()
    con.close()

iniciar_banco()

# ---------- FUNÇÕES AUXILIARES ----------
def agora():
    return datetime.now().isoformat(timespec="seconds")

def eh_numero(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)

def validar(msg):
    """Devolve texto do problema, ou None se a mensagem está ok."""
    if msg.get("tipo") != "leitura":
        return "campo 'tipo' deve ser 'leitura'"
    if not eh_numero(msg.get("temp")) or not -40 <= msg["temp"] <= 80:
        return "'temp' deve ser número entre -40 e 80"
    if not eh_numero(msg.get("umid")) or not 0 <= msg["umid"] <= 100:
        return "'umid' deve ser número entre 0 e 100"
    return None

async def erro(ws, codigo, texto):
    log.warning(f"Erro {codigo}: {texto}")
    await ws.send_text(json.dumps(
        {"tipo": "erro", "codigo": codigo, "mensagem": texto}))

async def transmitir(dado):
    """Repassa um evento para todos os painéis conectados."""
    for p in list(paineis):
        try:
            await p.send_text(json.dumps(dado))
        except Exception:
            paineis.discard(p)

# ---------- HTTP ----------
@app.get("/")
def raiz():
    return {"status": "EstufaNet no ar"}

@app.get("/painel")
def painel():
    return FileResponse("index.html")

@app.get("/historico")
def historico(device_id: str | None = None,
              limite: int = Query(50, ge=1, le=1000)):
    con = db()
    if device_id:
        linhas = con.execute(
            "SELECT * FROM leituras WHERE device_id=? ORDER BY id DESC LIMIT ?",
            (device_id, limite)).fetchall()
    else:
        linhas = con.execute(
            "SELECT * FROM leituras ORDER BY id DESC LIMIT ?",
            (limite,)).fetchall()
    con.close()
    return [dict(l) for l in linhas]

@app.get("/alertas")
def listar_alertas(limite: int = Query(50, ge=1, le=1000)):
    con = db()
    linhas = con.execute(
        "SELECT * FROM alertas ORDER BY id DESC LIMIT ?", (limite,)).fetchall()
    con.close()
    return [dict(l) for l in linhas]

@app.get("/limiar")
def ver_limiar():
    return {"temp": limiar["temp"]}

class NovoLimiar(BaseModel):
    valor: float

@app.put("/limiar")
def mudar_limiar(corpo: NovoLimiar):
    limiar["temp"] = corpo.valor
    log.info(f"Limiar alterado para {corpo.valor}")
    return {"temp": limiar["temp"]}

# ---------- WEBSOCKET DOS SENSORES ----------
@app.websocket("/ws")
async def ws_sensor(ws: WebSocket):
    await ws.accept()
    device = "?"
    log.info("Conexão de sensor aberta")
    try:
        while True:
            texto = await ws.receive_text()

            # 1) JSON válido?
            try:
                msg = json.loads(texto)
            except json.JSONDecodeError:
                await erro(ws, 400, "mensagem não é JSON válido")
                continue
            if not isinstance(msg, dict):
                await erro(ws, 400, "mensagem deve ser um objeto JSON")
                continue

            # 2) Autenticação por token
            did = msg.get("device_id")
            if not isinstance(did, str) or TOKENS.get(did) != msg.get("token"):
                await erro(ws, 401, "device_id ou token inválido")
                continue
            device = did

            # 3) Validação dos campos
            problema = validar(msg)
            if problema:
                await erro(ws, 422, problema)
                continue

            # 4) Guardar no banco
            ts = agora()
            con = db()
            con.execute(
                "INSERT INTO leituras (device_id,temp,umid,ts) VALUES (?,?,?,?)",
                (device, msg["temp"], msg["umid"], ts))

            # 5) Alerta por limiar
            alerta = msg["temp"] > limiar["temp"]
            if alerta:
                con.execute(
                    "INSERT INTO alertas (device_id,temp,limiar,ts) VALUES (?,?,?,?)",
                    (device, msg["temp"], limiar["temp"], ts))
                log.warning(f"ALERTA {device}: temp {msg['temp']} > {limiar['temp']}")
            con.commit()
            con.close()

            log.info(f"{device}: temp={msg['temp']} umid={msg['umid']}")

            # 6) Repassar ao painel e responder ao sensor
            await transmitir({"tipo": "leitura", "device_id": device,
                              "temp": msg["temp"], "umid": msg["umid"],
                              "ts": ts, "alerta": alerta})
            await ws.send_text(json.dumps(
                {"tipo": "ack", "status": "ok", "alerta": alerta, "ts": ts}))

    except WebSocketDisconnect:
        log.info(f"Sensor {device} desconectou")

# ---------- WEBSOCKET DO PAINEL ----------
@app.websocket("/ws/painel")
async def ws_painel(ws: WebSocket):
    await ws.accept()
    paineis.add(ws)
    log.info("Painel conectado")
    try:
        while True:
            await ws.receive_text()   # só mantém a conexão aberta
    except WebSocketDisconnect:
        paineis.discard(ws)
        log.info("Painel desconectou")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
