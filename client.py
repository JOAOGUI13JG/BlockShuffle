import asyncio
import websockets
import pickle
from colorama import Fore, init

# corzinha
init(autoreset=True)

def is_valid_move(move: str) -> bool:
    """validar a formatação do movimento"""
    parts = move.split()
    if len(parts) != 2:
        return False
    
    for part in parts:
        if len(part) != 2:
            return False
        if part[0].upper() not in 'ABCDEF':
            return False
        if not part[1].isdigit() or int(part[1]) not in range(1, 7):
            return False
    
    return True

def print_board(board):
    """Peças coloridas"""
    print("\n  1 2 3 4 5 6")
    letters = ['A', 'B', 'C', 'D', 'E', 'F']
    colors = {
        'O': Fore.RED,
        'X': Fore.GREEN,
        'Y': Fore.YELLOW,
        'Z': Fore.BLUE
    }
    
    for i, row in enumerate(board):
        colored_row = [colors.get(cell, Fore.WHITE) + cell for cell in row]
        print(f"{letters[i]} {' '.join(colored_row)}")

async def play_game():
    async with websockets.connect("ws://localhost:8765") as websocket:
        print(Fore.CYAN + "Conectando ao servidor..." + Fore.RESET)
        
        # conexão inicial e fase de waiting
        init_data = pickle.loads(await websocket.recv())
        player_id = init_data["player_id"]
        max_moves = init_data["max_moves"]
        moves_left = max_moves
        
        if init_data.get("waiting", True):
            print(Fore.YELLOW + "\nAguardando outro jogador conectar..." + Fore.RESET)
            while True:
                data = pickle.loads(await websocket.recv())
                if data["type"] == "game_start":
                    break
                elif data["type"] == "player_left":
                    print(Fore.RED + "\nO outro jogador desconectou. Encerrando..." + Fore.RESET)
                    await websocket.close()
                    return

        print(Fore.GREEN + f"\nVocê é o {player_id}" + Fore.RESET)
        print("\nSeu tabuleiro inicial:")
        print_board(init_data["board"])
        print(Fore.CYAN + f"\nTotal de jogadas permitidas: {max_moves}" + Fore.RESET)

        # Main game loop
        while True:
            try:
                # pula input de movimentos se o jogador não tem mais nenhum movimento
                if moves_left <= 0:
                    await asyncio.sleep(0.5)  # Small delay to prevent busy waiting
                    continue
                    
                # Get input de movimento válido
                while True:
                    move = input("\nDigite seu movimento (ex: A1 B2) ou 'sair': ").strip()
                    if move.lower() == 'sair':
                        await websocket.send(pickle.dumps({"type": "quit"}))
                        await websocket.close()
                        return
                    
                    parts = move.split()
                    if len(parts) == 2:
                        formatted_move = f"{parts[0].upper()} {parts[1].upper()}"
                        if is_valid_move(formatted_move):
                            break
                    
                    print(Fore.RED + "Formato inválido! Use ex: A1 B2 (letras A-F, números 1-6)" + Fore.RESET)

                # Manda movimento
                await websocket.send(pickle.dumps({
                    "type": "move",
                    "move": formatted_move
                }))

                # Processa resposta do sv
                data = pickle.loads(await websocket.recv())
                
                if data["type"] == "board_update":
                    moves_left = data["moves_left"]
                    print(Fore.GREEN + f"\n{data.get('message', 'Movimento válido!')}" + Fore.RESET)
                    print(Fore.YELLOW + f"Pontuação: {data['score']}" + Fore.RESET)
                    print(f"Jogadas restantes: {moves_left}")
                    print_board(data["board"])
                
                elif data["type"] == "turn_complete":
                    moves_left = 0
                    print(Fore.YELLOW + f"\n{data['message']}" + Fore.RESET)
                    print(Fore.CYAN + f"Pontuação final: {data['score']}" + Fore.RESET)
                    print_board(data["board"])
                
                elif data["type"] == "waiting":
                    print(Fore.BLUE + f"\n⌛ {data['message']}" + Fore.RESET)
                
                elif data["type"] == "move_error":
                    print(Fore.RED + f"\nERRO: {data['message']}" + Fore.RESET)
                    if "Aguardando" in data["message"]:
                        moves_left = 0
                
                elif data["type"] == "game_over":
                    print(Fore.MAGENTA + "\n--- FIM DE JOGO ---" + Fore.RESET)
                    print("Placar final:")
                    for player, score in data["scores"].items():
                        color = Fore.GREEN if player == data["winner"] else Fore.WHITE
                        print(color + f"{player}: {score} pontos" + Fore.RESET)
                    print(Fore.CYAN + f"\nVencedor: {data['winner']}!" + Fore.RESET)
                    break

            except (websockets.exceptions.ConnectionClosed, ConnectionResetError):
                print(Fore.RED + "\nConexão com o servidor perdida." + Fore.RESET)
                break
            except Exception as e:
                print(Fore.RED + f"\nErro: {str(e)}" + Fore.RESET)
                break

if __name__ == "__main__":
    try:
        asyncio.run(play_game())
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nJogo encerrado pelo usuário." + Fore.RESET)
