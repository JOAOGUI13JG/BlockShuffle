import asyncio
import websockets
import pickle
import sys
from collections import defaultdict
from board import generate_board, process_move

class Game:
    def __init__(self):
        self.players = {}
        self.boards = {}
        self.scores = defaultdict(int)
        self.moves_count = defaultdict(int)
        self.max_moves = 3  # Número reduzido de movimentos para teste
        self.game_id = id(self)
        self.game_started = False
        self.last_move_time = {}
        self.inactivity_timeout = 6000  # 6000 segundos de inatividade

    async def check_inactivity(self, websocket):
        """Desconecta jogador inativo se exceder o tempo limite"""
        while True:
            await asyncio.sleep(600)  # Verifica a cada 5 segundos
            if websocket in self.players and not self.game_started:
                elapsed = asyncio.get_event_loop().time() - self.last_move_time[websocket]
                if elapsed > self.inactivity_timeout:
                    print(f"Jogador {self.players[websocket]['id']} desconectado por inatividade")
                    await websocket.close()
                    break

    async def broadcast(self, message_type, data=None, exclude=None):
        """Envia mensagem para todos os jogadores conectados"""
        data = data or {}
        for ws, player_info in list(self.players.items()):  # Usa lista para evitar RuntimeError
            if exclude and ws == exclude:
                continue
            try:
                message = {
                    "type": message_type,
                    "game_id": self.game_id,
                    **data,
                    **player_info
                }
                await ws.send(pickle.dumps(message))
            except (websockets.exceptions.ConnectionClosed, ConnectionResetError):
                self.handle_disconnect(ws)

    def handle_disconnect(self, websocket):
        """Remove jogador desconectado"""
        if websocket in self.players:
            player_id = self.players[websocket]["id"]
            print(f"{player_id} desconectou")
            del self.players[websocket]
            del self.last_move_time[websocket]

            # Se desconectar antes do jogo começar, notifica o outro jogador
            if not self.game_started and len(self.players) == 1:
                remaining_player = next(iter(self.players.keys()))
                asyncio.create_task(self.players[remaining_player].send(pickle.dumps({
                    "type": "player_left",
                    "message": "O outro jogador desconectou"
                })))

    async def handle_move(self, websocket, move_data):
        """Processa movimento válido"""
        player_id = self.players[websocket]["id"]
        self.last_move_time[websocket] = asyncio.get_event_loop().time()

        # Verifica se o jogador já completou todos os movimentos
        if self.moves_count[player_id] >= self.max_moves:
            await websocket.send(pickle.dumps({
                "type": "move_error",
                "message": "Você já completou todas as jogadas! Aguardando oponente..."
            }))
            
            # Apenas verifica fim de jogo se ambos terminarem
            if all(count >= self.max_moves for count in self.moves_count.values()):
                winner = max(self.scores.items(), key=lambda x: x[1])
                await self.broadcast("game_over", {
                    "winner": winner[0],
                    "scores": dict(self.scores)
                })
                return True
            return False  # Continua o jogo para o outro jogador

        # Processa movimento normal
        result = process_move(self.boards[player_id], move_data["move"])
        
        if result["valid"]:
            self.boards[player_id] = result["board"]
            self.scores[player_id] += result["points"]
            self.moves_count[player_id] += 1
            
            # Mensagem de jogada normal ou de término
            if self.moves_count[player_id] >= self.max_moves:
                message_type = "turn_complete"
                message = "Você completou todas as jogadas! Aguardando oponente terminar..."
            else:
                message_type = "board_update"
                message = "Movimento válido!"

            await websocket.send(pickle.dumps({
                "type": message_type,
                "board": self.boards[player_id],
                "score": self.scores[player_id],
                "moves_left": self.max_moves - self.moves_count[player_id],
                "total_moves": self.moves_count[player_id],
                "message": message
            }))

            # Verifica fim de jogo APÓS atualizar o movimento
            if all(count >= self.max_moves for count in self.moves_count.values()):
                winner = max(self.scores.items(), key=lambda x: x[1])
                await self.broadcast("game_over", {
                    "winner": winner[0],
                    "scores": dict(self.scores)
                })
                return True
        else:
            await websocket.send(pickle.dumps({
                "type": "move_error",
                "message": "Movimento inválido! Não formou combinações de 3+ peças."
            }))
        return False

class GameManager:
    def __init__(self):
        self.waiting_game = None
    
    async def handle_connection(self, websocket):
        """Gerencia novas conexões de jogadores"""
        if self.waiting_game and len(self.waiting_game.players) < 2:
            game = self.waiting_game
        else:
            game = Game()
            self.waiting_game = game
        
        player_id = f"player{len(game.players) + 1}"
        game.players[websocket] = {
            "id": player_id,
            "score": 0
        }
        game.boards[player_id] = generate_board()
        game.last_move_time[websocket] = asyncio.get_event_loop().time()
        
        print(f"Jogador {player_id} conectado")

        # Inicia verificação de inatividade
        inactivity_task = asyncio.create_task(game.check_inactivity(websocket))

        try:
            # Envia dados iniciais
            await websocket.send(pickle.dumps({
                "type": "init",
                "player_id": player_id,
                "board": game.boards[player_id],
                "max_moves": game.max_moves,
                "waiting": len(game.players) < 2
            }))

            # Inicia jogo quando 2 jogadores conectarem
            if len(game.players) == 2:
                game.game_started = True
                await game.broadcast("game_start")
                print("Jogo iniciado com ambos jogadores conectados!")

            # Processa mensagens do jogador
            async for message in websocket:
                game.last_move_time[websocket] = asyncio.get_event_loop().time()
                data = pickle.loads(message)
                if data["type"] == "move":
                    await game.handle_move(websocket, data)

        except (websockets.exceptions.ConnectionClosed, ConnectionResetError):
            print(f"{player_id} desconectou abruptamente")
        except Exception as e:
            print(f"Erro com {player_id}: {str(e)}")
        finally:
            inactivity_task.cancel()
            game.handle_disconnect(websocket)
            if len(game.players) == 0:
                self.waiting_game = None

async def main():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    game_manager = GameManager()
    async with websockets.serve(game_manager.handle_connection, "0.0.0.0", 8765):
        print("Servidor rodando na porta 8765 - Aguardando jogadores...")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
