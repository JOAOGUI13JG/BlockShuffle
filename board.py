# board.py
import random

# Função para imprimir o tabuleiro
def print_board(board):
    letters = ['A', 'B', 'C', 'D', 'E', 'F']
    print("  1 2 3 4 5 6")
    for i, row in enumerate(board):
        print(f"{letters[i]} {' '.join(row)}")
    print()

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
                matches.append([(i, j), (i, j + 1), (i, j + 2)] )
    
    # Verificar colunas
    for i in range(4):
        for j in range(6):
            if board[i][j] == board[i + 1][j] == board[i + 2][j]:
                matches.append([(i, j), (i + 1, j), (i + 2, j)] )
    
    return matches

# Mapeamento das coordenadas
letters = ['A', 'B', 'C', 'D', 'E', 'F']

def coords_to_index(coord):
    letter, number = coord[0].upper(), int(coord[1])
    return letters.index(letter), number - 1

# Função para processar o movimento de troca
def process_player_move(board, move):
    coord1, coord2 = move.split()
    
    # Realiza a troca de peças
    swap_pieces(board, coord1, coord2)
    
    # Verifica se o movimento gerou combinações
    if check_matches(board):
        print("Movimento válido! Combinações encontradas.")
        # Verifica combinações e aplica a gravidade
        process_matches(board)
    else:
        print("Movimento inválido! Nenhuma combinação encontrada.")
        # Desfaz a troca de peças
        swap_pieces(board, coord1, coord2)
    
    return board

# Função para trocar as peças no tabuleiro
def swap_pieces(board, coord1, coord2):
    x1, y1 = coords_to_index(coord1)
    x2, y2 = coords_to_index(coord2)
    
    # Trocar peças
    board[x1][y1], board[x2][y2] = board[x2][y2], board[x1][y1]

# Função para aplicar a gravidade
def apply_gravity(board):
    for col in range(6):
        empty_spaces = []
        for row in range(5, -1, -1):  # Começar da última linha
            if board[row][col] == ' ':
                empty_spaces.append(row)
            elif empty_spaces:
                empty_row = empty_spaces.pop()
                board[empty_row][col] = board[row][col]
                board[row][col] = ' '

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

# Função para processar e atualizar as combinações no tabuleiro
def process_matches(board):
    matches = check_matches(board)
    
    if matches:
        print("Combinações encontradas! Substituindo peças...")
        # Calcula a pontuação para cada match
        for match in matches:
            match_length = len(match)
            print(f"Pontuação ganha: {calculate_points(match_length)}")
            
            # Substituindo as peças combinadas por novas aleatórias
            for x, y in match:
                board[x][y] = ' '  # Marcar as posições como vazias

        apply_gravity(board)  # Aplica a gravidade após os matches

if __name__ == "__main__":
    # Gera o tabuleiro inicial
    board = generate_board()
    print("Tabuleiro inicial:")
    print_board(board)

    # Loop para permitir que o usuário faça movimentos
    while True:
        # Solicita as coordenadas do movimento
        move = input("Digite seu movimento (ex: A1 B5) ou 'sair' para encerrar: ")
        
        # Verifica se o usuário quer sair
        if move.lower() == 'sair':
            print("Jogo encerrado.")
            break
        
        # Processa o movimento
        board = process_player_move(board, move)
        
        # Exibe o tabuleiro atualizado
        print("Tabuleiro atualizado:")
        print_board(board)
