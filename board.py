import random
from typing import List, Tuple, Dict

def generate_board() -> List[List[str]]:
    """Gera um tabuleiro 6x6 sem combinações iniciais"""
    symbols = ['O', 'X', 'Y', 'Z']
    while True:
        board = [[random.choice(symbols) for _ in range(6)] for _ in range(6)]
        if not find_matches(board):
            return board

def find_matches(board: List[List[str]]) -> Dict[Tuple[int, int], int]:
    """Encontra apenas matches de 3+ peças consecutivas (horizontal/vertical)"""
    matches = {}

    # Verifica linhas (apenas sequências consecutivas)
    for i in range(6):
        for j in range(4):
            if board[i][j] != ' ' and board[i][j] == board[i][j+1] == board[i][j+2]:
                k = j + 2
                while k + 1 < 6 and board[i][j] == board[i][k+1]:
                    k += 1
                for x in range(j, k + 1):
                    matches[(i, x)] = k - j + 1

    # Verifica colunas (apenas sequências consecutivas)
    for j in range(6):
        for i in range(4):
            if board[i][j] != ' ' and board[i][j] == board[i+1][j] == board[i+2][j]:
                k = i + 2
                while k + 1 < 6 and board[i][j] == board[k+1][j]:
                    k += 1
                for x in range(i, k + 1):
                    matches[(x, j)] = k - i + 1

    return matches

def calculate_points(matches: Dict[Tuple[int, int], int]) -> int:
    """Calcula pontos baseado no tamanho das combinações"""
    if not matches:
        return 0
    # Soma pontos de todas as combinações encontradas
    return sum(100 + 50 * (size - 3) for size in matches.values())

def apply_gravity(board: List[List[str]]):
    """Faz as peças caírem para preencher espaços vazios"""
    for j in range(6):
        # Coletar todas as peças da coluna (de baixo pra cima)
        column = [board[i][j] for i in range(5, -1, -1) if board[i][j] != ' ']
        # Preencher com espaços vazios no topo
        column += [' '] * (6 - len(column))
        # Atualizar a coluna
        for i in range(6):
            board[i][j] = column[5 - i]

def fill_board(board: List[List[str]]):
    """Preenche espaços vazios com novas peças"""
    symbols = ['O', 'X', 'Y', 'Z']
    for i in range(6):
        for j in range(6):
            if board[i][j] == ' ':
                board[i][j] = random.choice(symbols)

def process_move(board: List[List[str]], move: str) -> Dict:
    """Processa movimentos com validação consistente"""
    try:
        # Verificação robusta de formato
        if len(move.split()) != 2:
            return {
                "valid": False, 
                "board": board, 
                "points": 0,
                "steps": [{
                    "board": board,
                    "points": 0,
                    "message": "Formato de movimento inválido"
                }]
            }
        
        coord1, coord2 = move.split()
        row1 = ord(coord1[0].upper()) - ord('A')
        col1 = int(coord1[1]) - 1
        row2 = ord(coord2[0].upper()) - ord('A')
        col2 = int(coord2[1]) - 1

        # Verificação de limites
        if not all(0 <= x < 6 for x in [row1, col1, row2, col2]):
            return {
                "valid": False, 
                "board": board, 
                "points": 0,
                "steps": [{
                    "board": board,
                    "points": 0,
                    "message": "Coordenadas fora do tabuleiro"
                }]
            }

        # Cria cópia segura do tabuleiro
        new_board = [row.copy() for row in board]
        new_board[row1][col1], new_board[row2][col2] = new_board[row2][col2], new_board[row1][col1]

        # Sistema de verificação otimizado
        def verify_matches(b):
            matches = set()
            # Verificação horizontal e vertical simultânea
            for i in range(6):
                for j in range(4):
                    if b[i][j] == b[i][j+1] == b[i][j+2] != ' ':
                        matches.update((i, x) for x in range(j, j+3))
                    if b[j][i] == b[j+1][i] == b[j+2][i] != ' ':
                        matches.update((x, i) for x in range(j, j+3))
            return matches

        matches = verify_matches(new_board)
        if not matches:
            return {
                "valid": False, 
                "board": board, 
                "points": 0,
                "steps": [{
                    "board": board,
                    "points": 0,
                    "message": "Nenhuma combinação formada"
                }]
            }

        # Processamento de matches em cadeia
        steps = []
        current_board = [row.copy() for row in board]
        current_board[row1][col1], current_board[row2][col2] = current_board[row2][col2], current_board[row1][col1]
        
        total_points = 0
        while True:
            matches = find_matches(current_board)
            if not matches:
                break
                
            # Adiciona o estado ANTES de limpar as peças
            steps.append({
                "board": [row.copy() for row in current_board],
                "points": total_points,
                "message": "Combinação encontrada!"
            })
            
            # Remove as peças combinadas
            for (i, j) in matches:
                current_board[i][j] = ' '
            
            total_points += calculate_points(matches)
            
            # Adiciona o estado APÓS limpar (antes da gravidade)
            steps.append({
                "board": [row.copy() for row in current_board],
                "points": total_points,
                "message": "Removendo peças..."
            })
            
            apply_gravity(current_board)
            fill_board(current_board)
        
        # Garante que sempre haja steps mesmo sem matches
        if not steps:
            steps.append({
                "board": current_board,
                "points": 0,
                "message": "Movimento realizado"
            })

        return {
            "valid": True,
            "board": current_board,
            "points": total_points,
            "steps": steps  # Todas as etapas intermediárias
        }

    except Exception as e:
        print(f"Erro no processamento: {str(e)}")
        return {
            "valid": False,
            "board": board,
            "points": 0,
            "steps": [{
                "board": board,
                "points": 0,
                "message": "Erro no movimento"
            }]
        }
