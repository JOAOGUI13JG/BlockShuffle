class BlockShuffleGame {
    constructor() {
        this.socket = null;
        this.playerId = null;
        this.board = null;
        this.selectedCell = null;
        this.scores = {};
        this.maxMoves = 0;
        this.movesLeft = 0;
        
        this.initElements();
        this.initEventListeners();
        this.connectToServer();
    }
    
    initElements() {
        this.boardElement = document.getElementById('board');
        this.playerIdElement = document.getElementById('player-id');
        this.scoreElement = document.getElementById('score');
        this.movesLeftElement = document.getElementById('moves-left');
        this.maxMovesElement = document.getElementById('max-moves');
        this.scoresListElement = document.getElementById('scores-list');
        this.gameStatusElement = document.getElementById('game-status');
        this.quitButton = document.getElementById('quit-btn');
    }
    
    initEventListeners() {
        this.quitButton.addEventListener('click', () => {
            if (this.socket) {
                this.socket.send(JSON.stringify({ type: "quit" }));
            }
            window.location.reload();
        });
    }
    
    async connectToServer() {
        try {
            this.socket = new WebSocket('ws://localhost:8765');
            
            this.socket.onopen = () => {
                this.updateStatus('Conectando ao servidor...', 'waiting');
            };
            
            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (e) {
                    console.error('Erro ao processar mensagem:', e);
                }
            };
            
            this.socket.onclose = () => {
                this.updateStatus('Conexão com o servidor perdida.', 'game-over');
            };
            
            this.socket.onerror = (error) => {
                console.error('Erro na conexão:', error);
                this.updateStatus('Erro na conexão com o servidor.', 'game-over');
            };
            
        } catch (error) {
            console.error('Erro ao conectar:', error);
            this.updateStatus('Erro ao conectar ao servidor.', 'game-over');
        }
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'init':
                this.handleInit(data);
                break;
            case 'game_start':
                this.handleGameStart();
                break;
            case 'board_update':
                this.handleBoardUpdate(data);
                break;
            case 'turn_complete':
                this.handleTurnComplete(data);
                break;
            case 'game_over':
                this.handleGameOver(data);
                break;
            case 'move_error':
                this.handleMoveError(data);
                break;
            case 'waiting':
                this.handleWaiting(data);
                break;
            case 'player_left':
                this.handlePlayerLeft(data);
                break;
        }
    }
    
    handleInit(data) {
        this.playerId = data.player_id;
        this.board = data.board;
        this.maxMoves = data.max_moves;
        this.movesLeft = data.max_moves;
        
        this.playerIdElement.textContent = this.playerId;
        this.maxMovesElement.textContent = this.maxMoves;
        this.movesLeftElement.textContent = this.movesLeft;
        
        this.renderBoard();
        
        if (data.waiting) {
            this.updateStatus('Aguardando outro jogador conectar...', 'waiting');
        }
    }
    
    handleGameStart() {
        this.updateStatus('Jogo iniciado! Faça seu movimento.', 'playing');
    }
    
    handleBoardUpdate(data) {
        this.board = data.board;
        this.scores[this.playerId] = data.score;
        this.movesLeft = data.moves_left;
        
        this.scoreElement.textContent = data.score;
        this.movesLeftElement.textContent = this.movesLeft;
        
        this.renderBoard();
        this.updateScores();
        
        if (data.message) {
            this.updateStatus(data.message, 'playing');
        }
    }
    
    handleTurnComplete(data) {
        this.board = data.board;
        this.scores[this.playerId] = data.score;
        this.movesLeft = 0;
        
        this.scoreElement.textContent = data.score;
        this.movesLeftElement.textContent = this.movesLeft;
        
        this.renderBoard();
        this.updateScores();
        this.updateStatus(data.message, 'waiting');
    }
    
    handleGameOver(data) {
        this.scores = data.scores;
        this.updateScores(data.winner);
        this.updateStatus(`Fim de jogo! Vencedor: ${data.winner}`, 'game-over');
    }
    
    handleMoveError(data) {
        this.updateStatus(data.message, 'waiting');
    }
    
    handleWaiting(data) {
        this.updateStatus(data.message, 'waiting');
    }
    
    handlePlayerLeft(data) {
        this.updateStatus(data.message, 'game-over');
    }
    
    updateStatus(message, statusClass) {
        this.gameStatusElement.textContent = message;
        this.gameStatusElement.className = 'status ' + statusClass;
    }
    
    updateScores(winner = null) {
        this.scoresListElement.innerHTML = '';
        
        for (const [player, score] of Object.entries(this.scores)) {
            const scoreItem = document.createElement('div');
            scoreItem.className = 'score-item';
            
            const playerSpan = document.createElement('span');
            playerSpan.textContent = player;
            
            const scoreSpan = document.createElement('span');
            scoreSpan.textContent = score;
            
            if (player === winner) {
                playerSpan.classList.add('winner');
                scoreSpan.classList.add('winner');
            }
            
            scoreItem.appendChild(playerSpan);
            scoreItem.appendChild(scoreSpan);
            this.scoresListElement.appendChild(scoreItem);
        }
    }
    
    renderBoard() {
        this.boardElement.innerHTML = '';
        
        for (let i = 0; i < 6; i++) {
            for (let j = 0; j < 6; j++) {
                const cell = document.createElement('div');
                cell.className = `cell ${this.board[i][j]}`;
                cell.textContent = this.board[i][j];
                cell.dataset.row = i;
                cell.dataset.col = j;
                
                cell.addEventListener('click', () => this.handleCellClick(cell));
                
                this.boardElement.appendChild(cell);
            }
        }
    }
    
    handleCellClick(cell) {
        if (this.movesLeft <= 0) return;
        
        const row = parseInt(cell.dataset.row);
        const col = parseInt(cell.dataset.col);
        
        if (this.selectedCell) {
            // Verifica se é uma célula adjacente
            const prevRow = parseInt(this.selectedCell.dataset.row);
            const prevCol = parseInt(this.selectedCell.dataset.col);
            
            const isAdjacent = 
                (Math.abs(row - prevRow) === 1 && col === prevCol) || 
                (Math.abs(col - prevCol) === 1 && row === prevRow);
            
            if (isAdjacent) {
                // Faz o movimento
                const move = `${String.fromCharCode(65 + prevRow)}${prevCol + 1} ${String.fromCharCode(65 + row)}${col + 1}`;
                this.socket.send(JSON.stringify({ type: "move", move }));
            }
            
            // Remove a seleção em qualquer caso
            this.selectedCell.classList.remove('selected');
            this.selectedCell = null;
        } else {
            // Seleciona a célula
            this.selectedCell = cell;
            cell.classList.add('selected');
        }
    }
}

// Inicia o jogo quando a página carregar
window.onload = () => {
    new BlockShuffleGame();
};