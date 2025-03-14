import random

# Função para gerar o tabuleiro e garantir que não comece com combinações
def generate_board():
    while True:
        board = [[random.choice(['O', 'X', 'Y', 'Z']) for _ in range(6)] for _ in range(6)]
        if not check_matches(board):  # Se não houver combinações, retornamos o tabuleiro
            return board

# Função para verificar combinações
def check_matches(board):
    matches = []
    
    # Verificar linhas
    for i in range(6):
        for j in range(4):
            if board[i][j] == board[i][j + 1] == board[i][j + 2]:
                matches.append([(i, j), (i, j + 1), (i, j + 2)])
    
    # Verificar colunas
    for i in range(4):
        for j in range(6):
            if board[i][j] == board[i + 1][j] == board[i + 2][j]:
                matches.append([(i, j), (i + 1, j), (i + 2, j)])
    
    return matches

# Mapeamento das coordenadas
letters = ['A', 'B', 'C', 'D', 'E', 'F']

def coords_to_index(coord):
    letter, number = coord[0].upper(), int(coord[1])
    return letters.index(letter), number - 1

# Função para imprimir o tabuleiro com coordenadas e a pontuação
def print_board(score, moves_left):
    print(f"Pontuação: {score}")
    print(f"Movimentos restantes: {moves_left}")
    print("  1 2 3 4 5 6")
    for i, row in enumerate(board):
        print(f"{letters[i]} {' '.join(row)}")
    print()

# Função para processar a troca de peças no tabuleiro
def swap_pieces(coord1, coord2):
    x1, y1 = coords_to_index(coord1)
    x2, y2 = coords_to_index(coord2)
    
    # Trocar peças
    board[x1][y1], board[x2][y2] = board[x2][y2], board[x1][y1]

# Função para aplicar a gravidade (fazer as peças caírem)
def apply_gravity(board):
    for col in range(6):
        # Pegando a coluna atual e verificando quais peças estão vazias
        empty_spaces = []
        for row in range(5, -1, -1):  # Começar da última linha
            if board[row][col] == ' ':
                empty_spaces.append(row)
            elif empty_spaces:
                # Se a célula não estiver vazia, move as peças para baixo
                empty_row = empty_spaces.pop()
                board[empty_row][col] = board[row][col]
                board[row][col] = ' '

        # Preencher as células vazias no topo com peças aleatórias
        for row in empty_spaces:
            board[row][col] = random.choice(['O', 'X', 'Y', 'Z'])

# Função para calcular a pontuação com base no número de peças no match
def calculate_points(match_length):
    if match_length == 3:
        return 100
    elif match_length == 4:
        return 150
    elif match_length == 5:
        return 200
    elif match_length == 6:
        return 250
    return 0

# Função para verificar se a troca resulta em um match
def is_valid_move(board, coord1, coord2):
    # Simula a troca
    swap_pieces(coord1, coord2)
    
    # Verifica se a troca gerou uma combinação
    matches = check_matches(board)
    
    # Desfaz a troca
    swap_pieces(coord1, coord2)
    
    # Retorna True se a troca resultar em uma combinação
    return len(matches) > 0

# Função para processar o movimento, garantindo que o movimento seja válido
def process_move(coord1, coord2):
    global moves_left
    if is_valid_move(board, coord1, coord2):
        swap_pieces(coord1, coord2)
        moves_left -= 1  # Diminuir a quantidade de movimentos restantes apenas se o movimento for válido
        return True  # Movimento válido
    else:
        print("Movimento inválido! A troca não gera um match.")
        return False  # Movimento inválido

# Função para calcular a pontuação após realizar um movimento
def process_matches():
    global score
    matches = check_matches(board)
    
    if matches:
        print("Combinações encontradas! Substituindo peças...")
        # Calculando a pontuação para cada match
        for match in matches:
            match_length = len(match)
            score += calculate_points(match_length)
            
            # Substituindo as peças combinadas por novas aleatórias
            for x, y in match:
                board[x][y] = ' '  # Marcar as posições como vazias

        apply_gravity(board)  # Aplica a gravidade após os matches

# Jogo local para 1 jogador
def play_game():
    global score, moves_left
    while moves_left > 0:
        print_board(score, moves_left)
        
        try:
            move = input("Digite a troca (ex: A1 B3 ou 'sair' para encerrar): ")
            if move.lower() == 'sair':
                break
            coord1, coord2 = move.split()
            
            # Realizar a troca, garantindo que o movimento seja válido
            if process_move(coord1, coord2):
                process_matches()  # Verificar os matches e somar pontos
        except:
            print("Movimento inválido! Tente novamente.")

    print("Jogo encerrado. Pontuação final:", score)

# Inicialização do tabuleiro e início do jogo
score = 0  # Inicializando o contador de pontos
moves_left = 5  # Jogador pode fazer até 5 movimentos
print("Bem-vindo ao jogo de match-3 local! 🎮")
board = generate_board()  # Gerar um tabuleiro válido
play_game()
