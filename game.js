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
                if (data.waiting) {
                    this.updateStatus('Aguardando outro jogador...', 'waiting');
                    this.blockInput(true);
                }
                break;
            case 'game_start':
                this.handleGameStart();
                this.blockInput(false);
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

    blockInput(blocked) {
        const cells = document.querySelectorAll('.cell');
        cells.forEach(cell => {
            cell.style.pointerEvents = blocked ? 'none' : 'auto';
            cell.style.opacity = blocked ? '0.5' : '1';
        });
        
        if (blocked) {
            this.gameStatusElement.textContent = 'Aguardando outro jogador...';
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
    
    async handleBoardUpdate(data) {
        try {
            this.board = data.board;
            this.scores[this.playerId] = data.score;
            this.movesLeft = data.moves_left;
    
            this.renderBoard();
            
            this.scoreElement.textContent = data.score;
            this.movesLeftElement.textContent = this.movesLeft;
            this.updateScores();
    
            if (data.message) {
                const statusType = data.message.includes("Removendo") ? 'waiting' : 'playing';
                this.updateStatus(data.message, statusType);
            }
    
            if (this.movesLeft <= 0) {
                setTimeout(() => {
                    if (!this.gameEnded) {
                        this.updateStatus("Processando resultado final...", 'waiting');
                    }
                }, 5000);
            }
        } catch (e) {
            console.error("Erro ao processar atualização:", e);
        }
    }

    handleTurnComplete(data) {
        this.handleBoardUpdate(data);
        
        if (data.moves_left <= 0) {
            this.updateStatus("Seu turno terminou! Aguardando resultado final...", 'waiting');
            
            setTimeout(() => {
                if (!this.gameEnded) {
                    this.updateStatus("Preparando placar final...", 'game-over');
                    this.handleGameOver({
                        scores: this.scores,
                        winner: Object.keys(this.scores)[0]
                    });
                }
            }, 10000);
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
    
    handleGameOver(data) {
        setTimeout(() => {
            this.scores = data.scores;
            this.updateScores(data.winner);
            this.updateStatus(`Fim de jogo! Vencedor: ${data.winner}`, 'game-over');
        }, 1005);
    }
    
    handleMoveError(data) {
        this.updateStatus(data.message, 'waiting');
        
        if (this.lastSelection) {
            this.lastSelection.cell1.classList.remove('processing');
            this.lastSelection.cell2.classList.remove('processing');
            
            this.lastSelection.cell1.classList.add('invalid');
            setTimeout(() => {
                this.lastSelection.cell1.classList.remove('invalid');
            }, 500);
            
            this.lastSelection = null;
        }
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

        if (this.selectedCell) {
            if (this.selectedCell !== cell) {
                this.lastSelection = {
                    cell1: this.selectedCell,
                    cell2: cell,
                    move: `${String.fromCharCode(65 + parseInt(this.selectedCell.dataset.row))}${parseInt(this.selectedCell.dataset.col) + 1} ${
                           String.fromCharCode(65 + parseInt(cell.dataset.row))}${parseInt(cell.dataset.col) + 1}`
                };

                this.selectedCell.classList.add('processing');
                cell.classList.add('processing');
                
                setTimeout(() => {
                    this.socket.send(JSON.stringify({ 
                        type: "move", 
                        move: this.lastSelection.move 
                    }));
                }, 300);
            }

            this.selectedCell.classList.remove('selected');
            this.selectedCell = null;
        } else {
            this.selectedCell = cell;
            cell.classList.add('selected');
        }
    }

    swapCellsOnScreen(cell1, cell2) {
        const tempText = cell1.textContent;
        const tempClass = cell1.className.replace(/selected|processing/g, '').trim();
        
        cell1.textContent = cell2.textContent;
        cell1.className = cell2.className.replace(/selected|processing/g, '').trim();
        
        cell2.textContent = tempText;
        cell2.className = tempClass;
    }
}

window.onload = () => {
    new BlockShuffleGame();
};