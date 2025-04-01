import asyncio
import websockets
#import pickle
import sys
import json
import traceback
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
        self.move_timeout = 300
        self.health_check_task = asyncio.create_task(self.run_health_checks())

    async def check_inactivity(self, websocket):
        """Desconecta jogador inativo se exceder o tempo limite"""
        while True:
            await asyncio.sleep(600)  # Verifica a cada 10 minutos
            if websocket in self.players:
                elapsed = asyncio.get_event_loop().time() - self.last_move_time[websocket]
                if elapsed > self.inactivity_timeout:
                    player_id = self.players[websocket]["id"]
                    print(f"Jogador {player_id} desconectado por inatividade")
                    
                    # Marca como completado se desconectar sem jogar
                    if player_id not in self.moves_count:
                        self.moves_count[player_id] = 0
                    
                    await websocket.close()
                    break
    
    async def run_health_checks(self):
        """Verifica periodicamente se o jogo está travado"""
        while True:
            await asyncio.sleep(10)
            if self.game_started:
                all_idle = all(
                    self.moves_count.get(p["id"], 0) >= self.max_moves
                    for p in self.players.values()
                )
                if all_idle:
                    await self.check_game_completion()
    
    async def check_move_timeout(self):
        """Encerra o jogo se algum jogador não completar no tempo"""
        await asyncio.sleep(self.move_timeout)
        if not await self.check_game_completion():
            # Força término do jogo com o jogador com maior pontuação
            if self.scores:
                winner = max(self.scores.items(), key=lambda x: x[1])
                await self.broadcast("game_over", {
                    "winner": winner[0],
                    "scores": dict(self.scores),
                    "message": "Tempo esgotado!"
                })


    async def broadcast(self, message_type, data=None, exclude=None):
        data = data or {}
        for ws, player_info in list(self.players.items()):
            if exclude and ws == exclude:
                continue
            try:
                message = {
                    "type": message_type,
                    "game_id": self.game_id,
                    **data,
                    **player_info
                }
                await ws.send(json.dumps(message))
            except (websockets.exceptions.ConnectionClosed, ConnectionResetError) as e:
                print(f"Erro ao enviar mensagem: {e}")
                self.handle_disconnect(ws)
            except Exception as e:
                print(f"Erro inesperado: {traceback.format_exc()}")

    def handle_disconnect(self, websocket):
        """Remove jogador desconectado"""
        if websocket in self.players:
            player_id = self.players[websocket]["id"]
            print(f"{player_id} desconectou")
            
            # Marca como tendo "desistido" (0 movimentos)
            if player_id not in self.moves_count:
                self.moves_count[player_id] = 0
            
            del self.players[websocket]
            del self.last_move_time[websocket]
            
            # Se restar apenas 1 jogador, encerra o jogo
            if len(self.players) == 1:
                remaining_player = next(iter(self.players.values()))["id"]
                asyncio.create_task(self.broadcast("game_over", {
                    "winner": remaining_player,
                    "scores": {remaining_player: self.scores.get(remaining_player, 0)}
                }))
            else:
                # Verifica se o jogo pode terminar normalmente
                asyncio.create_task(self.check_game_completion())

    async def handle_move(self, websocket, move_data):
        """Processa movimento válido"""
        if not self.game_started:
            await websocket.send(json.dumps({
                "type": "move_error",
                "message": "O jogo ainda não começou"
            }))
            return False
        player_id = self.players[websocket]["id"]
        self.last_move_time[websocket] = asyncio.get_event_loop().time()

        # Validação básica do movimento
        try:
            parts = move_data["move"].split()
            if len(parts) != 2:
                raise ValueError("Formato inválido")
            
            # Extrai coordenadas
            coord1, coord2 = parts
            row1 = ord(coord1[0].upper()) - ord('A')
            col1 = int(coord1[1]) - 1
            row2 = ord(coord2[0].upper()) - ord('A')
            col2 = int(coord2[1]) - 1

            # Verificação de limites
            if not all(0 <= x < 6 for x in [row1, col1, row2, col2]):
                await websocket.send(json.dumps({
                    "type": "move_error",
                    "message": "Coordenadas fora dos limites do tabuleiro!"
                }))
                return False
            result = process_move(self.boards[player_id], move_data["move"])
        
            if result["valid"]:
                # Envia cada etapa para o cliente
                for step in result["steps"]:
                    await websocket.send(json.dumps({
                        "type": "board_update",
                        "board": step["board"],
                        "score": self.scores[player_id] + step["points"],
                        "moves_left": self.max_moves - self.moves_count[player_id],
                        "message": step["message"]
                    }))
                    await asyncio.sleep(1.0)  # Pausa entre etapas
                
                # Atualiza estado final
                self.boards[player_id] = result["board"]
                self.scores[player_id] += result["points"]
                self.moves_count[player_id] += 1
                
                # Garante envio da mensagem final mesmo se não houver steps
                final_message = {
                    "type": "turn_complete",
                    "board": self.boards[player_id],
                    "score": self.scores[player_id],
                    "moves_left": self.max_moves - self.moves_count[player_id],
                    "message": "Turno completo!" if self.moves_count[player_id] >= self.max_moves 
                            else "Movimento concluído!"
                }
                await websocket.send(json.dumps(final_message))
                
                # Verifica imediatamente se o jogo terminou
                await self.check_game_completion()
    
        except Exception as e:
            print(f"Erro ao processar movimento: {traceback.format_exc()}")
            await websocket.send(json.dumps({
                "type": "move_error",
                "message": "Erro no processamento do movimento"
            }))
    
    async def check_game_completion(self):
        """Verifica se o jogo deve terminar"""
        if len(self.players) < 2:
            return False
            
        # Verifica se todos os jogadores completaram seus movimentos
        all_completed = all(self.moves_count.get(p["id"], 0) >= self.max_moves 
                        for p in self.players.values())
        
        if all_completed:
            try:
                if not self.scores:  # Caso não haja pontuações registradas
                    self.scores = {p["id"]: 0 for p in self.players.values()}
                
                winner = max(self.scores.items(), key=lambda x: x[1])
                await self.broadcast("game_over", {
                    "winner": winner[0],
                    "scores": dict(self.scores)
                })
                return True
            except ValueError:
                print("Erro ao determinar vencedor - scores vazios")
                return False
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
            "score": 0,
            "ready": False  # Novo campo para controlar prontidão
        }
        game.boards[player_id] = generate_board()
        game.last_move_time[websocket] = asyncio.get_event_loop().time()
        
        print(f"Jogador {player_id} conectado")

        # Inicia verificação de inatividade
        inactivity_task = asyncio.create_task(game.check_inactivity(websocket))

        try:
            # Envia dados iniciais
            await websocket.send(json.dumps({
                "type": "init",
                "player_id": player_id,
                "board": game.boards[player_id],
                "max_moves": game.max_moves,
                "waiting": len(game.players) < 2
            }))

            # Espera ambos jogadores conectarem
            while len(game.players) < 2:
                await asyncio.sleep(0.1)

            # Marca jogador como pronto
            game.players[websocket]["ready"] = True
            
            # Só inicia quando ambos estiverem prontos
            while not all(p["ready"] for p in game.players.values()):
                await asyncio.sleep(0.1)

            game.game_started = True
            await game.broadcast("game_start")
            print("Jogo iniciado com ambos jogadores conectados!")

            # Processa mensagens do jogador
            async for message in websocket:
                game.last_move_time[websocket] = asyncio.get_event_loop().time()
                data = json.loads(message)
                
                # Bloqueia movimentos antes do jogo começar
                if data["type"] == "move" and game.game_started:
                    await game.handle_move(websocket, data)
                elif data["type"] == "move":
                    await websocket.send(json.dumps({
                        "type": "move_error",
                        "message": "Aguardando outro jogador conectar"
                    }))

        except (websockets.exceptions.ConnectionClosed, ConnectionResetError):
            print(f"{player_id} desconectou abruptamente")
        finally:
            inactivity_task.cancel()
            game.handle_disconnect(websocket)
            if len(game.players) == 0:
                self.waiting_game = None

async def main():
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        game_manager = GameManager()
        server = await websockets.serve(game_manager.handle_connection, "0.0.0.0", 8765)
        print("Servidor rodando na porta 8765 - Aguardando jogadores...")
        
        # Mantém o servidor rodando até Ctrl+C
        await asyncio.get_event_loop().create_future()
        
    except asyncio.CancelledError:
        print("\nServidor encerrado normalmente")
    except Exception as e:
        print(f"Erro no servidor: {traceback.format_exc()}")
    finally:
        server.close()
        await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
