from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json, datetime

app = FastAPI()

@app.get("/")
def raiz():
    return {"status": "EstufaNet no ar"}

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    print("Cliente conectado")
    try:
        while True:
            texto = await ws.receive_text()
            msg = json.loads(texto)
            agora = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"[{agora}] recebido: {msg}")
    except WebSocketDisconnect:
        print("Cliente desconectou")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)