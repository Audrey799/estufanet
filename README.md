# EstufaNet

Sistema distribuído de monitoramento em tempo real de sensores simulados (temperatura e umidade),
com servidor central, painel web, banco de dados, alertas por limiar e avaliação experimental da
comunicação em rede.

Projeto 1 (2026) da disciplina CIC0124 - Redes de Computadores, Universidade de Brasília,
Departamento de Ciência da Computação, Profa. Priscila Solís.

## Integrantes


| [Audrey Coutinho Soares]               | [232020994] | [Audrey799]                |
| [Isabele Sandra Gontijo dos Santos]    | [232026871] | [isabelesandragontijo-rgb] |


## Vídeo de demonstração

[link do video] 

## Relatório

O relatório técnico em PDF (arquitetura, protocolo, implementação, experimentos, capturas do Wireshark
e discussão) está em: [link do PDF]

## Visão geral

```
[sensor1] ─┐
[sensor2] ─┼── WebSocket /ws ────►  [server.py]  ──► SQLite (estufanet.db)
[sensorN] ─┘     (JSON)           FastAPI + Uvicorn
                                  porta TCP 8000
[painel web] ◄── WebSocket /ws/painel (tempo real) ──┘
[painel web] ──── HTTP (histórico, alertas, limiar) ──►
```

- **Modelo:** cliente-servidor centralizado. O servidor escuta na porta TCP 8000 e atende vários
  clientes simultâneos, identificados por `device_id`.
- **HTTP** para consulta, cadastro e configuração (histórico, alertas, limiar).
- **WebSocket** para o fluxo contínuo de leituras. Justificativa: mantém uma única conexão TCP aberta
  e bidirecional, evitando o custo de uma nova requisição HTTP por leitura e permitindo que o servidor
  envie dados ao painel sem ser consultado.
- **SQLite** para persistência, sem necessidade de configuração.

## Funcionalidades

- Servidor FastAPI com rotas HTTP e dois canais WebSocket (sensores e painel).
- Dois ou mais sensores simultâneos, cada um com `device_id` e token próprios.
- Painel web com gráfico em tempo real (Chart.js), lista de alertas e ajuste do limiar.
- Banco SQLite com histórico de leituras e de alertas, consultável por HTTP.
- Alertas automáticos quando a temperatura ultrapassa o limiar (padrão 30 °C, alterável).
- Autenticação simples por token por dispositivo e validação das mensagens (erros 400, 401 e 422).
- Logs com timestamp (console e arquivo `estufanet.log`).
- Tratamento de desconexões: o servidor registra a saída do cliente e o sensor reconecta sozinho.
- Medição de RTT da aplicação em cada leitura (o sensor mede o tempo até o `ack`).

## Requisitos

- Python 3.10 ou superior
- Dependências: `fastapi`, `uvicorn`, `websockets` (ver `requirements.txt`)
- Para os gráficos dos experimentos (opcional): `matplotlib`
- Para as capturas e a rede degradada (opcional): Wireshark com Npcap e Clumsy (Windows)

## Instalação

```
pip install -r requirements.txt
```

No Thonny, as mesmas bibliotecas podem ser instaladas em *Ferramentas → Gerenciar pacotes*.

## Como executar

Rode sempre a partir da pasta onde estão `server.py` e `index.html`, porque o servidor entrega o
painel lendo o `index.html` da pasta atual.

1. **Servidor:**

```
python server.py
```

Deve aparecer `Uvicorn running on http://0.0.0.0:8000`. Confira em http://localhost:8000
(resposta: `{"status": "EstufaNet no ar"}`).

2. **Sensores**, cada um em um terminal (ou janela do Thonny) separado, com um nome diferente:

```
python sensor.py sensor1
python sensor.py sensor2
```

Os nomes válidos são `sensor1` a `sensor5`. O token de cada um é `tk-` seguido do nome (ex.: `tk-sensor1`)
e já é montado pelo `sensor.py`. No Thonny, que roda um script por vez por janela, abra uma janela
do Thonny para cada processo.

3. **Painel web:** http://localhost:8000/painel

4. **Documentação automática da API (FastAPI):** http://localhost:8000/docs

O sensor se conecta a `127.0.0.1`. Para testar em outra máquina da mesma rede, troque esse endereço no
`sensor.py` pelo IP do computador do servidor (ex.: `192.168.0.15`). O servidor já aceita conexões
externas (`host="0.0.0.0"`).

O banco (`estufanet.db`) e o log (`estufanet.log`) são criados automaticamente ao rodar o servidor e não
fazem parte do repositório (estão no `.gitignore`).

## Interfaces

|    Tipo   |              Endereço           |                      Função                        |
|    ---    |                ---              |                          ---                       |
| WebSocket | `/ws`                           | Sensores enviam leituras e recebem `ack` ou `erro` |
| WebSocket | `/ws/painel`                    | Painel recebe leituras em tempo real               |
| GET       | `/`                             | Status do servidor                                 |
| GET       | `/painel`                       | Página do painel                                   |
| GET       | `/historico?device_id=&limite=` | Histórico de leituras                              |
| GET       | `/alertas?limite=`              | Alertas gravados                                   |
| GET       | `/limiar`                       | Limiar vigente                                     |
| PUT       | `/limiar`                       | Altera o limiar (corpo: `{"valor": 25}`)           |

Exemplo de leitura enviada pelo sensor:

```json
{"tipo": "leitura", "device_id": "sensor1", "token": "tk-sensor1", "temp": 27.3, "umid": 61.2}
```

Resposta do servidor: `{"tipo": "ack", "status": "ok", "alerta": false, "ts": "2026-11-03T12:36:22"}`.

O formato completo das mensagens, os campos, a sequência de operações, os códigos de erro e os exemplos
estão documentados no protocolo de aplicação: [`protocolo.tex`](protocolo.tex) (seção do relatório).

## Experimentos de rede

Todos os experimentos usam a aplicação em loopback (processos independentes na mesma máquina).

|     Experimento   |                              O que mede                           |            Como executar                     |
|         ---       |                               ---                                 |                    ---                       |
| A: RTT            | 100 medições por condição, com média, mediana e dispersão         | `experimentos.py`                            |
| B: Throughput     | Mensagens de ~0,1; 1; 10 e 100 KB, com volume útil por tempo      | `experimentos.py`                            |
| C: Concorrência   | 1, 2 e 5 clientes simultâneos, com atraso e mensagens por segundo | `experimentos.py`                            |
| D: TCP vs UDP     | 1000 mensagens de ~100 B em cada protocolo, na porta 9000         | `microteste.py`                              |
| E: Rede degradada | Os mesmos testes com atraso e perda simulados (Clumsy)            | `experimentos.py` com a condição `degradada` |

**Experimentos A, B, C e E:** com o servidor rodando, execute `experimentos.py`. O script pergunta o endereço do
servidor (Enter para `127.0.0.1`) e o nome da condição (`local` ou `degradada`), e grava
`resultados_<condição>.csv` e `rtt_bruto_<condição>.csv` na pasta de execução.

**Experimento D:** abra duas janelas e rode `microteste.py` em cada uma. Na primeira digite `servidor`, na
segunda `cliente`. O servidor imprime recebidos, perdidos e fora de ordem para TCP e UDP.

**Rede degradada (Experimento E e Captura 2 e 3b):** Clumsy executado como administrador, com Lag de 100 ms e Drop de 5%.
Filtros: `tcp.DstPort == 8000 or tcp.SrcPort == 8000` (aplicação) e `udp.DstPort == 9000 or tcp.DstPort == 9000` (microteste).
[ajustar se os parâmetros usados forem outros]

**Gráficos:** `gerar_graficos.py` lê os CSVs e gera as figuras do relatório.

### Resumo dos resultados da camada de transporte

|                   Cenário             |                              Resultado                                        |
|                     ---               |                                ---                                            |
| Microteste, rede normal               | TCP 1000/1000 e UDP 1000/1000 mensagens entregues                             |
| Microteste, rede degradada            | TCP 1000/1000 e UDP 931/1000 (69 perdidos, 6,9%), sem mensagens fora de ordem |
| Aplicação, rede degradada (Captura 2) | 98 retransmissões TCP em 14.826 pacotes (0,7%) na porta 8000                  |

Os valores de RTT, throughput e concorrência (tabelas e gráficos) estão no relatório: [ver relatório].

## Capturas do Wireshark

Capturas feitas no *Npcap Loopback Adapter*, sem filtro de captura. Cada pasta tem o `.pcapng`, os prints
e a ficha com data, filtros, cenário e observações.

| Captura |                       Cenário                        | Principais evidências                                                                                  |
|    ---  |                     ---                              |                                                 ---                                                    |
|    1    | 1 sensor, rede normal                                | Handshake TCP, `GET /ws` com `101 Switching Protocols`, frames WebSocket mascarados, RTT de transporte |
|    2    | Experimentos com Clumsy ligado (Lag 100 ms, Drop 5%) | Retransmissões TCP e RTT elevado com picos                                                             |
|    3    | Microteste TCP vs UDP (3a normal, 3b degradada)      | TCP em 5 segmentos de dados, UDP com um datagrama por mensagem, 931 de 1000 datagramas                 |

## Limitações conhecidas

- Os clientes rodam como processos independentes na mesma máquina, então o tráfego em loopback não passa por
  uma rede física: o RTT é muito baixo e quase não há perdas sem degradação simulada.
- O tráfego não é cifrado (`ws://` e `http://`, sem TLS) e os tokens são fixos no código. Isso é adequado
  para o escopo da disciplina, mas não para produção.
- As rotas HTTP não exigem autenticação.
- O servidor é único (ponto único de falha) e o banco é local. O limiar de alerta fica em memória e volta
  ao padrão quando o servidor reinicia.
- Os dados dos sensores são simulados com distribuição uniforme entre 20 e 35 °C (temperatura) e 40 e 80%
  (umidade).

## Ferramentas, bibliotecas e uso de IA

- **Bibliotecas:** FastAPI, Uvicorn, websockets, SQLite (módulo `sqlite3` do Python), Chart.js (via CDN no painel),
  matplotlib (gráficos).
- **Ferramentas:** Python, Thonny, Git e GitHub Desktop, Wireshark (Npcap), Clumsy, Excel, Overleaf.
- **Inteligência artificial:** foi usado um assistente de IA (Claude, da Anthropic) como apoio para explicar
  conceitos de redes, gerar versões iniciais do código e dos scripts de experimento, e revisar textos. O grupo
  executou, testou e adaptou todo o código, realizou os experimentos e as capturas, e analisou os resultados.
  [ajustar a descrição ao uso real de cada integrante]


## Referências

- Documentação do FastAPI: https://fastapi.tiangolo.com
- Documentação da biblioteca websockets: https://websockets.readthedocs.io
- RFC 6455, The WebSocket Protocol: https://www.rfc-editor.org/rfc/rfc6455
- Documentação do Chart.js: https://www.chartjs.org
- Documentação do Wireshark: https://www.wireshark.org/docs
- Clumsy: https://jagt.github.io/clumsy
-  Python Software Foundation. *asyncio: Asynchronous I/O*. Python Documentation. https://docs.python.org/3/library/asyncio.html
-  SQLite. *SQLite Documentation*. https://www.sqlite.org/docs.html 
- J. F. Kurose e K. W. Ross. *Redes de Computadores e a Internet: Uma Abordagem Top-Down*. 8. ed. São Paulo: Pearson, 2021.
- A. S. Tanenbaum e D. J. Wetherall. *Redes de Computadores*. 5. ed. São Paulo: Pearson, 2011.
- R. Fielding, M. Nottingham e J. Reschke. *HTTP Semantics*. IETF, RFC 9110, 2022. https://www.rfc-editor.org/rfc/rfc9110
- I. Fette e A. Melnikov. *The WebSocket Protocol*. IETF, RFC 6455, 2011. https://www.rfc-editor.org/rfc/rfc6455
- W. Eddy. *Transmission Control Protocol (TCP)*. IETF, RFC 9293, 2022. https://www.rfc-editor.org/rfc/rfc9293
- J. Postel. *User Datagram Protocol*. IETF, RFC 768, 1980. https://www.rfc-editor.org/rfc/rfc768
- V. Paxson, M. Allman, J. Chu e M. Sargent. *Computing TCP's Retransmission Timer*. IETF, RFC 6298, 2011. https://www.rfc-editor.org/rfc/rfc6298
- T. Bray. *The JavaScript Object Notation (JSON) Data Interchange Format*. IETF, RFC 8259, 2017. https://www.rfc-editor.org/rfc/rfc8259
-  C. Sanders. *Practical Packet Analysis: Using Wireshark to Solve Real-World Network Problems*. 3. ed. San Francisco: No Starch Press, 2017.
  - jagt. *clumsy: network condition simulator for Windows*. https://jagt.github.io/clumsy/ (acesso em 3 nov. 2026).
