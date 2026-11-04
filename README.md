# EstufaNet

Sistema de monitoramento em tempo real de sensores simulados
(temperatura e umidade) EstufaNet, desenvolvido para a disciplina CIC0124 - Redes de
Computadores (UnB), Projeto 1 - 2026/2.

## Integrantes

- [Audrey Coutinho Soares] - [232020994]
- [Isabele Sandra Gontijo dos Santos] - [232026871]


## Arquitetura

Modelo cliente-servidor centralizado:

- **Servidor** (`server.py`): FastAPI + Uvicorn. Escuta na porta TCP 8000.
  Recebe leituras dos sensores via WebSocket (`/ws`) e responde a consultas HTTP.
- **Sensores** (`sensor.py`): clientes que geram leituras aleatórias de
  temperatura e umidade e enviam ao servidor a cada 1 segundo. Cada sensor
  tem um `device_id` próprio.

## Requisitos

- Python 3.10 ou superior

## Instalação

```
pip install -r requirements.txt
```

## Como executar

1. Inicie o servidor:

```
python server.py
```

2. Confira no navegador: http://localhost:8000
   (deve aparecer `{"status": "EstufaNet no ar"}`).

3. Em outros terminais, inicie os sensores, cada um com um nome diferente:

```
python sensor.py sensor1
python sensor.py sensor2
```

As leituras aparecem no terminal do servidor com timestamp.

## Estrutura do repositório

```
estufanet/
├── server.py
├── sensor.py
├── requirements.txt
└── README.md
```

## Status

- [x] Servidor HTTP + WebSocket
- [x] Sensores simulados
- [ ] Banco de dados SQLite
- [ ] Alertas por limiar
- [ ] Autenticação por token
- [ ] Painel web
- [ ] Experimentos de rede e capturas Wireshark
- [ ] Relatório
