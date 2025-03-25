import asyncio
import websockets
import pickle
from board import generate_board, process_player_move

# Dicionário para armazenar o estado do jogo de cada cliente
game_states = {}

# Função para enviar o estado do jogo para um cliente específico
async def send_game_state(websocket, game_state):
    print(f"Enviando estado do jogo para o cliente: {game_state}")
    try:
        await websocket.send(pickle.dumps(game_state))
    except websockets.exceptions.ConnectionClosedError:
        print("Erro na conexão com o cliente.")
        if websocket in game_states:
            del game_states[websocket]  # Remove o cliente desconectado

# Função para processar o movimento de um cliente
async def process_move(move, websocket):
    if websocket not in game_states:
        # Se o cliente não tem um tabuleiro, cria um novo
        game_states[websocket] = {
            "board": generate_board(),
            "score": 0,
            "turn": 0,
            "moves_left": 5
        }
        print(f"Novo tabuleiro gerado para o cliente: {game_states[websocket]['board']}")

    game_state = game_states[websocket]

    # Simula o movimento
    if move:
        print(f"Movimento recebido do cliente: {move}")  # Log do movimento

        # Atualiza o tabuleiro com o movimento do jogador
        new_board = process_player_move(game_state["board"], move)
        if new_board != game_state["board"]:  # Se o movimento for válido
            game_state["board"] = new_board
            game_state["turn"] += 1  # Incrementa o turno
        else:
            print("Movimento inválido! Nenhuma combinação encontrada.")

    # Envia o estado atualizado do jogo para o cliente
    await send_game_state(websocket, game_state)

# Função para tratar as conexões dos jogadores
async def handler(websocket):
    print("Novo cliente conectado!")  # Log de conexão

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
        if websocket in game_states:
            del game_states[websocket]

# Função principal para iniciar o servidor WebSocket
async def start_server():
    # Inicia o servidor
    server = await websockets.serve(handler, "0.0.0.0", 8765)  # Use "0.0.0.0" para permitir conexões externas
    print("Servidor WebSocket iniciado na porta 8765")
    await server.wait_closed()

# Iniciar o servidor
asyncio.run(start_server())
