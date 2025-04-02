<p align="center">
 <img src= "logo_Block_Shuffle.png" width=50%>
</p>



Block Shuffle
Um jogo de combinação de blocos multiplayer em tempo real usando WebSocket, Python e Apache na AWS

🌟 # Visão Geral
Block Shuffle é um jogo de puzzle multiplayer onde jogadores combinam blocos coloridos em tempo real usando WebSocket. Esta versão utiliza Apache como proxy reverso em uma instância AWS EC2.

📦 # Tecnologias Principais
Componente	Tecnologia
Backend	Python + WebSocket (websockets)
Frontend	Terminal (cliente Python)
Servidor Web	Apache HTTP Server
Cloud	AWS EC2 (Ubuntu)
Protocolo	WebSocket (ws://)
🚀 Configuração Rápida na AWS
1. Pré-requisitos
Instância EC2 com Ubuntu (t2.micro)

Security Group liberando portas: 22 (SSH), 80 (HTTP), 8000 (WebSocket)

Apache instalado

2. Instalação do Apache com suporte a WebSocket
bash
Copy
sudo apt update
sudo apt install apache2 -y

# Habilitar módulos necessários
sudo a2enmod proxy proxy_http proxy_wstunnel rewrite
sudo systemctl restart apache2
3. Configuração do Virtual Host
Edite o arquivo de configuração:

bash
Copy
sudo nano /etc/apache2/sites-available/block-shuffle.conf
Cole esta configuração:

apache
Copy
<VirtualHost *:80>
    ServerName seu-ip-ou-dominio.com

    # Proxy para WebSocket
    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} =websocket [NC]
    RewriteRule /(.*) ws://localhost:8000/$1 [P,L]

    # Proxy para HTTP normal
    ProxyPass / http://localhost:8000/
    ProxyPassReverse / http://localhost:8000/

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
Ative o site e reinicie:

bash
Copy
sudo a2ensite block-shuffle
sudo systemctl restart apache2
🎮 Como Executar
No Servidor (EC2)
Instale as dependências:

bash
Copy
pip3 install websockets colorama
Inicie o servidor WebSocket:

bash
Copy
python3 server.py
Nos Clientes
bash
Copy
python3 client.py --host ws://seu-ip-ec2
🔧 Solução de Problemas Comuns
Apache não está redirecionando WebSockets
Verifique:

Se os módulos estão ativos:

bash
Copy
sudo apache2ctl -M | grep -E 'proxy|rewrite'
Logs de erro:

bash
Copy
sudo tail -f /var/log/apache2/error.log
Conexão bloqueada pelo Security Group
Verifique se a porta 8000 está liberada nas regras de entrada da EC2

📊 Arquitetura do Sistema
mermaid
Copy
flowchart LR
    Client1 -->|WebSocket| Apache
    Client2 -->|WebSocket| Apache
    Apache -->|Proxy| Server[Server Python:8000]
    Server -->|Dados do Jogo| Client1
    Server -->|Dados do Jogo| Client2
📜 Comandos Úteis
Comando	Descrição
sudo systemctl status apache2	Verifica status do Apache
sudo tail -f /var/log/apache2/access.log	Monitora acessos
`netstat -tulnp	grep 8000`	Verifica se o servidor Python está ouvindo
📄 Licença
MIT License 

