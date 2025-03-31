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

    # async def check_inactivity(self, websocket):
    #     """Desconecta jogador inativo se exceder o tempo limite"""
    #     while True:
    #         await asyncio.sleep(600)  # Verifica a cada 5 segundos
    #         if websocket in self.players and not self.game_started:
    #             elapsed = asyncio.get_event_loop().time() - self.last_move_time[websocket]
    #             if elapsed > self.inactivity_timeout:
    #                 print(f"Jogador {self.players[websocket]['id']} desconectado por inatividade")
    #                 await websocket.close()
    #                 break
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

    # async def broadcast(self, message_type, data=None, exclude=None):
    #     """Envia mensagem para todos os jogadores conectados"""
    #     data = data or {}
    #     for ws, player_info in list(self.players.items()):  # Usa lista para evitar RuntimeError
    #         if exclude and ws == exclude:
    #             continue
    #         try:
    #             message = {
    #                 "type": message_type,
    #                 "game_id": self.game_id,
    #                 **data,
    #                 **player_info
    #             }
    #             await ws.send(json.dumps(message))
    #         except (websockets.exceptions.ConnectionClosed, ConnectionResetError):
    #             self.handle_disconnect(ws)
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

    # def handle_disconnect(self, websocket):
    #     """Remove jogador desconectado"""
    #     if websocket in self.players:
    #         player_id = self.players[websocket]["id"]
    #         print(f"{player_id} desconectou")
    #         del self.players[websocket]
    #         del self.last_move_time[websocket]

    #         # Se desconectar antes do jogo começar, notifica o outro jogador
    #         if not self.game_started and len(self.players) == 1:
    #             remaining_player = next(iter(self.players.keys()))
    #             asyncio.create_task(self.players[remaining_player].send(json.dumps({
    #                 "type": "player_left",
    #                 "message": "O outro jogador desconectou"
    #             })))
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
            
            # Verifica se o jogo pode terminar
            asyncio.create_task(self.check_game_completion())

    # async def handle_move(self, websocket, move_data):
    #     """Processa movimento válido"""
    #     player_id = self.players[websocket]["id"]
    #     self.last_move_time[websocket] = asyncio.get_event_loop().time()

    #     # Verifica se o jogador já completou todos os movimentos
    #     if self.moves_count[player_id] >= self.max_moves:
    #         await websocket.send(json.dumps({
    #             "type": "move_error",
    #             "message": "Você já completou todas as jogadas! Aguardando oponente..."
    #         }))
            
    #         # Apenas verifica fim de jogo se ambos terminarem
    #         if all(count >= self.max_moves for count in self.moves_count.values()):
    #             winner = max(self.scores.items(), key=lambda x: x[1])
    #             await self.broadcast("game_over", {
    #                 "winner": winner[0],
    #                 "scores": dict(self.scores)
    #             })
    #             return True
    #         return False  # Continua o jogo para o outro jogador

    #     # Processa movimento normal
    #     result = process_move(self.boards[player_id], move_data["move"])
        
    #     if result["valid"]:
    #         self.boards[player_id] = result["board"]
    #         self.scores[player_id] += result["points"]
    #         self.moves_count[player_id] += 1
            
    #         # Mensagem de jogada normal ou de término
    #         if self.moves_count[player_id] >= self.max_moves:
    #             message_type = "turn_complete"
    #             message = "Você completou todas as jogadas! Aguardando oponente terminar..."
    #         else:
    #             message_type = "board_update"
    #             message = "Movimento válido!"

    #         await websocket.send(json.dumps({
    #             "type": message_type,
    #             "board": self.boards[player_id],
    #             "score": self.scores[player_id],
    #             "moves_left": self.max_moves - self.moves_count[player_id],
    #             "total_moves": self.moves_count[player_id],
    #             "message": message
    #         }))

    #         # Verifica fim de jogo APÓS atualizar o movimento
    #         if all(count >= self.max_moves for count in self.moves_count.values()):
    #             winner = max(self.scores.items(), key=lambda x: x[1])
    #             await self.broadcast("game_over", {
    #                 "winner": winner[0],
    #                 "scores": dict(self.scores)
    #             })
    #             return True
    #     else:
    #         await websocket.send(json.dumps({
    #             "type": "move_error",
    #             "message": "Movimento inválido! Não formou combinações de 3+ peças."
    #         }))
    #     return False

    async def handle_move(self, websocket, move_data):
        """Processa movimento válido"""
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

        except Exception as e:
            await websocket.send(json.dumps({
                "type": "move_error",
                "message": f"Erro no movimento: {str(e)}"
            }))
            return False

        result = process_move(self.boards[player_id], move_data["move"])
        
        if result["valid"]:
            # Atualiza estado do jogo
            self.boards[player_id] = result["board"]
            self.scores[player_id] += result["points"]
            self.moves_count[player_id] += 1
            
            
            # Mensagem de jogada normal ou de término
            if self.moves_count[player_id] >= self.max_moves:
                message_type = "turn_complete"
                message = "Você completou todas as jogadas! "
                "Aguardando oponente terminar..."
            else:
                message_type = "board_update"
                message = "Movimento válido!"

            await websocket.send(json.dumps({
                "type": message_type,
                "board": self.boards[player_id],
                "score": self.scores[player_id],
                "moves_left": self.max_moves - self.moves_count[player_id],
                "total_moves": self.moves_count[player_id],
                "message": message
            }))

            # Verifica se ambos completaram os movimentos
            if await self.check_game_completion():
                return True
        else:
            await websocket.send(json.dumps({
                "type": "move_error",
                "message": "Movimento inválido! Não formou combinações de 3+ peças."
            }))
        return False
    
    async def check_game_completion(self):
        """Verifica se o jogo deve terminar"""
        if not self.scores or len(self.scores) == 0:
            return False
            
        all_played = all(p["id"] in self.moves_count for p in self.players.values())
        all_completed = all(self.moves_count.get(p["id"], 0) >= self.max_moves 
                        for p in self.players.values())
        
        if all_played and all_completed:
            try:
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


        #     # Verifica fim de jogo APENAS se ambos jogadores completaram os movimentos
        #     if all(count >= self.max_moves for count in self.moves_count.values()):
        #         winner = max(self.scores.items(), key=lambda x: x[1])
        #         await self.broadcast("game_over", {
        #             "winner": winner[0],
        #             "scores": dict(self.scores)
        #         })
        #         return True
        # else:
        #     await websocket.send(json.dumps({
        #         "type": "move_error",
        #         "message": "Movimento inválido! Não formou combinações de 3+ peças."
        #     }))
        # return False

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
            await websocket.send(json.dumps({
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
                data = json.loads(message)
                if data["type"] == "move":
                    await game.handle_move(websocket, data)

        except (websockets.exceptions.ConnectionClosed, ConnectionResetError):
            print(f"{player_id} desconectou abruptamente")
        except Exception as e:
            print(f"Erro na conexão: {traceback.format_exc()}")
        finally:
            try:
                inactivity_task.cancel()
                game.handle_disconnect(websocket)
                if len(game.players) == 0:
                    self.waiting_game = None
            except:
                pass

# async def main():
#     if sys.platform == "win32":
#         asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
#     game_manager = GameManager()
#     async with websockets.serve(game_manager.handle_connection, "0.0.0.0", 8765):
#         print("Servidor rodando na porta 8765 - Aguardando jogadores...")
#         await asyncio.Future()

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
