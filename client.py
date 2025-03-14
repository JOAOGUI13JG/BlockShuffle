import asyncio
import websockets
import pickle

# Função para imprimir o tabuleiro
def print_board(board):
    letters = ['A', 'B', 'C', 'D', 'E', 'F']
    print("  1 2 3 4 5 6")
    for i, row in enumerate(board):
        print(f"{letters[i]} {' '.join(row)}")
    print()

# Função para receber e exibir o estado do jogo
async def receive_game_state():
    uri = "ws://localhost:8765"  # Substitua pelo IP do servidor
    print("Conectando ao servidor...")  # Log de conexão
    async with websockets.connect(uri) as websocket:
        print("Conectado ao servidor!")  # Log de conexão bem-sucedida
        while True:
            try:
                # Receber o estado do jogo
                game_state = pickle.loads(await websocket.recv())
                print("Estado do jogo recebido:")  # Log de recebimento

                # Mostrar o estado atual do jogo (tabuleiro, pontuação, etc.)
                print("Tabuleiro:")
                print_board(game_state["board"])
                print(f"Pontuação: {game_state['score']}")
                print(f"Vez do jogador: {game_state['turn'] % 2 + 1}")  # Alterna entre os jogadores 1 e 2
                print(f"Movimentos restantes: {game_state['moves_left']}")

                # Verifica se o jogo acabou
                if game_state.get("game_over", False):
                    print("O jogo terminou!")
                    break

                # Pedir ao jogador para fazer um movimento (se for a vez dele)
                if game_state['turn'] % 2 + 1 == 1:  # Jogador 1
                    move = input("Jogador 1, digite seu movimento (ex: A1 B5): ")
                else:  # Jogador 2
                    move = input("Jogador 2, digite seu movimento (ex: A1 B5): ")

                print(f"Movimento enviado: {move}")  # Log do movimento enviado
                await websocket.send(pickle.dumps(move))  # Envia o movimento para o servidor

            except websockets.exceptions.ConnectionClosedError:
                print("Erro na conexão com o servidor.")  # Log de erro
                break
            except Exception as e:
                print(f"Ocorreu um erro: {e}")  # Log de erro
                break

# Iniciar o cliente
asyncio.run(receive_game_state())
