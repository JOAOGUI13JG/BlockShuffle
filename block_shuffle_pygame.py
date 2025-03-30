import pygame
import sys
import asyncio
import websockets
import json
import math
import pickle
from pygame import gfxdraw

# Inicializa o Pygame
pygame.init()

# Configurações da tela
WIDTH, HEIGHT = 800, 600
BOARD_SIZE = 6
CELL_SIZE = 70
BOARD_OFFSET_X = 50
BOARD_OFFSET_Y = 50
PANEL_WIDTH = 250

# Cores
BACKGROUND_COLOR = (44, 62, 80)
BOARD_COLOR = (52, 73, 94)
CELL_COLORS = {
    'O': (231, 76, 60),
    'X': (46, 204, 113),
    'Y': (241, 196, 15),
    'Z': (52, 152, 219)
}
TEXT_COLOR = (255, 255, 255)
SELECTED_COLOR = (255, 255, 0)
STATUS_WAITING = (243, 156, 18)
STATUS_PLAYING = (46, 204, 113)
STATUS_GAMEOVER = (155, 89, 182)

# Configura a tela
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("BlockShuffle - Multiplayer")
clock = pygame.time.Clock()

# Fonte
font = pygame.font.SysFont('Arial', 24)
small_font = pygame.font.SysFont('Arial', 18)

class BlockShuffleGame:
    def __init__(self):
        self.websocket = None
        self.loop = asyncio.new_event_loop()
        self.player_id = None
        self.board = None
        self.selected_cell = None
        self.scores = {}
        self.max_moves = 0
        self.moves_left = 0
        self.status = "Conectando ao servidor..."
        self.status_color = STATUS_WAITING
        self.winner = None
        self.running = True
        self.connection_task = None
        
        #asyncio.get_event_loop().run_until_complete(self.connect_to_server())
    
    # async def connect_to_server(self):
    #     try:
    #         print("Tentando conectar ao servidor...")
    #         self.websocket = await websockets.connect('ws://localhost:8765')
    #         print("Conexão estabelecida com sucesso!")
            
    #         # Teste de mensagem inicial
    #         await self.websocket.send(json.dumps({"type": "hello"}))
    #         response = await self.websocket.recv()
    #         print("Resposta do servidor:", response)
            
    #     except Exception as e:
    #         print(f"Erro detalhado na conexão: {str(e)}")
    #         self.status = f"Erro: {str(e)}"
    #         self.running = False
    async def connect_to_server(self):
        try:
            print("Tentando conectar ao servidor...")
            self.websocket = await websockets.connect(
                'ws://localhost:8765',
                ping_interval=None,
                close_timeout=1
            )
            print("Conexão estabelecida com sucesso!")
            
            # Recebe mensagem inicial
            init_message = await self.websocket.recv()
            data = json.loads(init_message)
            
            if data.get("type") == "init":
                self.handle_message(data)
                self.status = "Conectado! Aguardando jogo..." if data.get("waiting") else "Jogo iniciado!"
                self.status_color = STATUS_WAITING if data.get("waiting") else STATUS_PLAYING
                
            # Inicia a tarefa de receber mensagens
            self.connection_task = asyncio.create_task(self.listen_to_server())
            return True
            
        except Exception as e:
            print(f"Erro detalhado na conexão: {str(e)}")
            self.status = f"Erro: {str(e)}"
            self.status_color = STATUS_GAMEOVER
            return False

    async def listen_to_server(self):
        """Escuta mensagens do servidor em segundo plano"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                self.handle_message(data)
        except Exception as e:
            print(f"Erro na conexão: {e}")
            self.status = "Conexão com o servidor perdida"
            self.running = False
    
    async def receive_messages(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)
                self.handle_message(data)
        except Exception as e:
            print(f"Erro na conexão: {e}")
            self.status = "Conexão com o servidor perdida"
            self.running = False
    
    def handle_message(self, data):
        if data['type'] == 'init':
            self.player_id = data['player_id']
            self.board = data['board']
            self.max_moves = data['max_moves']
            self.moves_left = data['max_moves']
            self.scores[self.player_id] = 0
            
            if data.get('waiting', True):
                self.status = "Aguardando outro jogador conectar..."
                self.status_color = STATUS_WAITING
        
        elif data['type'] == 'game_start':
            self.status = "Jogo iniciado! Faça seu movimento."
            self.status_color = STATUS_PLAYING
        
        elif data['type'] == 'board_update':
            self.board = data['board']
            self.scores[self.player_id] = data['score']
            self.moves_left = data['moves_left']
            
            if data.get('message'):
                self.status = data['message']
        
        elif data['type'] == 'turn_complete':
            self.board = data['board']
            self.scores[self.player_id] = data['score']
            self.moves_left = 0
            self.status = data['message']
            self.status_color = STATUS_WAITING
        
        elif data['type'] == 'game_over':
            self.scores = data['scores']
            self.winner = data['winner']
            self.status = f"Fim de jogo! Vencedor: {self.winner}"
            self.status_color = STATUS_GAMEOVER
        
        elif data['type'] == 'move_error':
            self.status = data['message']
            self.status_color = STATUS_WAITING
        
        elif data['type'] == 'waiting':
            self.status = data['message']
            self.status_color = STATUS_WAITING
        
        elif data['type'] == 'player_left':
            self.status = data['message']
            self.status_color = STATUS_GAMEOVER
    
    async def send_move(self, move):
        """Envia movimento para o servidor"""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps({"type": "move", "move": move}))
            except Exception as e:
                print(f"Erro ao enviar movimento: {e}")
                self.running = False
    
    def draw(self):
        # Fundo
        screen.fill(BACKGROUND_COLOR)
        
        # Desenha o tabuleiro
        pygame.draw.rect(screen, BOARD_COLOR, 
                         (BOARD_OFFSET_X, BOARD_OFFSET_Y, 
                          CELL_SIZE * BOARD_SIZE, CELL_SIZE * BOARD_SIZE))
        
        if self.board:
            for i in range(BOARD_SIZE):
                for j in range(BOARD_SIZE):
                    cell_x = BOARD_OFFSET_X + j * CELL_SIZE
                    cell_y = BOARD_OFFSET_Y + i * CELL_SIZE
                    
                    # Desenha a célula
                    color = CELL_COLORS.get(self.board[i][j], (255, 255, 255))
                    pygame.draw.rect(screen, color, 
                                     (cell_x, cell_y, CELL_SIZE, CELL_SIZE))
                    
                    # Desenha borda se selecionada
                    if self.selected_cell and self.selected_cell == (i, j):
                        pygame.draw.rect(screen, SELECTED_COLOR, 
                                         (cell_x, cell_y, CELL_SIZE, CELL_SIZE), 3)
                    
                    # Desenha o símbolo
                    text = font.render(self.board[i][j], True, TEXT_COLOR)
                    text_rect = text.get_rect(center=(cell_x + CELL_SIZE//2, cell_y + CELL_SIZE//2))
                    screen.blit(text, text_rect)
        
        # Painel de informações
        panel_x = BOARD_OFFSET_X + CELL_SIZE * BOARD_SIZE + 30
        pygame.draw.rect(screen, BOARD_COLOR, 
                         (panel_x, BOARD_OFFSET_Y, PANEL_WIDTH, 300))
        
        # Informações do jogador
        if self.player_id:
            player_text = font.render(f"Jogador: {self.player_id}", True, TEXT_COLOR)
            screen.blit(player_text, (panel_x + 10, BOARD_OFFSET_Y + 20))
            
            score_text = font.render(f"Pontuação: {self.scores.get(self.player_id, 0)}", True, TEXT_COLOR)
            screen.blit(score_text, (panel_x + 10, BOARD_OFFSET_Y + 50))
            
            moves_text = font.render(f"Jogadas: {self.moves_left}/{self.max_moves}", True, TEXT_COLOR)
            screen.blit(moves_text, (panel_x + 10, BOARD_OFFSET_Y + 80))
        
        # Placar
        scores_title = font.render("Placar:", True, TEXT_COLOR)
        screen.blit(scores_title, (panel_x + 10, BOARD_OFFSET_Y + 120))
        
        y_offset = 150
        for player, score in self.scores.items():
            color = TEXT_COLOR
            if self.winner and player == self.winner:
                color = (255, 215, 0)  # Dourado para o vencedor
            
            player_text = small_font.render(f"{player}: {score}", True, color)
            screen.blit(player_text, (panel_x + 20, BOARD_OFFSET_Y + y_offset))
            y_offset += 30
        
        # Status
        pygame.draw.rect(screen, self.status_color, 
                         (BOARD_OFFSET_X, BOARD_OFFSET_Y + CELL_SIZE * BOARD_SIZE + 20, 
                          CELL_SIZE * BOARD_SIZE, 40))
        
        status_text = font.render(self.status, True, TEXT_COLOR)
        status_rect = status_text.get_rect(center=(BOARD_OFFSET_X + CELL_SIZE * BOARD_SIZE // 2, 
                                                  BOARD_OFFSET_Y + CELL_SIZE * BOARD_SIZE + 40))
        screen.blit(status_text, status_rect)
        
        # Botão de sair
        pygame.draw.rect(screen, (231, 76, 60), (panel_x + 50, BOARD_OFFSET_Y + 250, 150, 40))
        quit_text = font.render("Sair", True, TEXT_COLOR)
        quit_rect = quit_text.get_rect(center=(panel_x + 125, BOARD_OFFSET_Y + 270))
        screen.blit(quit_text, quit_rect)
    
    def handle_click(self, pos):
        """Lida com cliques do mouse"""
        if (BOARD_OFFSET_X <= pos[0] <= BOARD_OFFSET_X + CELL_SIZE * BOARD_SIZE and
            BOARD_OFFSET_Y <= pos[1] <= BOARD_OFFSET_Y + CELL_SIZE * BOARD_SIZE and
            self.moves_left > 0):
            
            col = (pos[0] - BOARD_OFFSET_X) // CELL_SIZE
            row = (pos[1] - BOARD_OFFSET_Y) // CELL_SIZE
            
            if self.selected_cell:
                prev_row, prev_col = self.selected_cell
                if ((abs(row - prev_row) == 1 and col == prev_col) or (abs(col - prev_col) == 1 and row == prev_row)):
                    move = f"{chr(65 + prev_row)}{prev_col + 1} {chr(65 + row)}{col + 1}"
                    self.loop.run_until_complete(self.send_move(move))
                
                self.selected_cell = None
            else:
                self.selected_cell = (row, col)
        
        # Verifica clique no botão de sair
        panel_x = BOARD_OFFSET_X + CELL_SIZE * BOARD_SIZE + 30
        if (panel_x + 50 <= pos[0] <= panel_x + 200 and
            BOARD_OFFSET_Y + 250 <= pos[1] <= BOARD_OFFSET_Y + 290):
            self.running = False
    
    # def run(self):
    #     while self.running:
    #         for event in pygame.event.get():
    #             if event.type == pygame.QUIT:
    #                 self.running = False
    #             elif event.type == pygame.MOUSEBUTTONDOWN:
    #                 if event.button == 1:  # Botão esquerdo
    #                     self.handle_click(event.pos)
            
    #         self.draw()
    #         pygame.display.flip()
    #         clock.tick(60)
        
    #     pygame.quit()
    #     sys.exit()
    def run(self):
        """Executa o loop principal do jogo"""
        # Configura o loop asyncio
        asyncio.set_event_loop(self.loop)
        
        # Conecta ao servidor
        success = self.loop.run_until_complete(self.connect_to_server())
        if not success:
            pygame.quit()
            return
        
        # Main game loop
        while self.running:
            # Processa eventos do Pygame
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Botão esquerdo
                        self.handle_click(event.pos)
            
            # Executa tarefas asyncio pendentes
            self.loop.run_until_complete(asyncio.sleep(0.01))
            
            self.draw()
            pygame.display.flip()
            clock.tick(60)
        
        # Limpeza
        self.cleanup()
        pygame.quit()
        sys.exit()

    async def process_server_messages(self):
        try:
            # Verifica se há mensagens disponíveis sem bloquear
            message = await asyncio.wait_for(self.websocket.recv(), timeout=0.1)
            data = json.loads(message)
            self.handle_message(data)
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            print(f"Erro ao processar mensagem: {e}")
            self.running = False

    def cleanup(self):
        """Limpeza antes de sair"""
        if self.connection_task:
            self.connection_task.cancel()
        if self.websocket:
            self.loop.run_until_complete(self.websocket.close())
        self.loop.close()

if __name__ == "__main__":
    game = BlockShuffleGame()
    game.run()