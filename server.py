import asyncio
import websockets
import pickle
from board import generate_board, process_player_move, print_board

# Estado do jogo (tabuleiro e pontuação)
game_state = {"board": generate_board(), "score": 0, "turn": 0, "moves_left": 5}

# Lista para manter os clientes conectados
connected_clients = []

# Função para enviar o estado do jogo para todos os clientes
async def broadcast_game_state():
    print("Enviando estado do jogo para os clientes...")  # Log de envio
    for client in connected_clients:
        try:
            await client.send(pickle.dumps(game_state))
        except websockets.exceptions.ConnectionClosedError:
            print("Erro na conexão com um dos clientes.")
            connected_clients.remove(client)  # Remove o cliente desconectado

# Função para processar o movimento de um cliente
async def process_move(move, websocket):
    global game_state

    # Verifica de quem é a vez
    current_player = game_state["turn"] % 2 + 1
    print(f"Vez do jogador {current_player}")

    # Simula o movimento
    if move:
        print(f"Movimento recebido do jogador {current_player}: {move}")  # Log do movimento

        # Atualiza o tabuleiro com o movimento do jogador
        new_board = process_player_move(game_state["board"], move)
        if new_board != game_state["board"]:  # Se o movimento for válido
            game_state["board"] = new_board
            game_state["turn"] += 1  # Alterna os turnos entre os jogadores
        else:
            print("Movimento inválido! Nenhuma combinação encontrada.")

    # Envia o estado atualizado do jogo para todos os clientes
    await broadcast_game_state()

# Função para tratar as conexões dos jogadores
async def handler(websocket):
    print("Novo cliente conectado!")  # Log de conexão
    connected_clients.append(websocket)  # Adiciona o cliente à lista de clientes conectados

    try:
        while True:
            # Recebe a jogada do cliente
            move = await websocket.recv()  
            move = pickle.loads(move)

            # Processa a jogada e envia o estado atualizado
            await process_move(move, websocket)
    except websockets.exceptions.ConnectionClosed:
        print("Conexão fechada")  # Log de desconexão
    finally:
        # Remove o cliente desconectado
        connected_clients.remove(websocket)

# Função principal para iniciar o servidor WebSocket
async def start_server():
    # Inicia o servidor
    server = await websockets.serve(handler, "0.0.0.0", 8765)  
    print("Servidor WebSocket iniciado na porta 8765")
    await server.wait_closed()

# Iniciar o servidor
asyncio.run(start_server())
