# 🤖 Human or Not? — Minijogo do Teste de Turing 👤

Minijogo interativo inspirado no clássico **[humanornot.so](https://humanornot.so)** e no material didático do **Teste de Turing**.

---

## 🎯 Como Funciona a Mecânica
1. **Chat de 5 Turnos**: Você conversa com um interlocutor misterioso por até 5 mensagens.
2. **Identidade Sorteada**: O interlocutor tem 50% de chance de ser uma **Inteligência Artificial** ou um **Humano**.
   - *Se for Humano*: Exibe gírias comuns da internet brasileira (`kkk`, `mano`, `slk`), pontuação casual, possíveis errinhos de digitação e respostas espontâneas.
   - *Se for IA*: Exibe padrões de linguagem mais polidos, respostas diretas ou estruturadas.
3. **Votação**: Após a 5ª mensagem, a caixa de texto é bloqueada e surgem os botões de votação:
   - `🤖 Inteligência Artificial`
   - `👤 Humano`
4. **Revelação e Placar**: O jogo revela quem era o interlocutor de verdade e registra seu histórico de acertos e taxa de sucesso.

---

## 🚀 Como Executar

Você tem duas formas de jogar:

### Opção 1: Interface Web Moderna (Streamlit) — Recomendada 🌟
1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Inicie a aplicação web:
   ```bash
   streamlit run app.py
   ```
3. O navegador abrirá automaticamente no endereço `http://localhost:8501`.

---

### Opção 2: Versão Linha de Comando / Terminal (Sem dependências extras) 💻
Você pode rodar diretamente com o Python padrão:
```bash
python cli_game.py
```

---

## 📁 Estrutura dos Arquivos
- [`app.py`](file:///c:/Users/joker/OneDrive/Documentos/Turing/app.py): Interface Web estilizada no Streamlit com histórico de chat, indicador de digitação e tela de votação.
- [`cli_game.py`](file:///c:/Users/joker/OneDrive/Documentos/Turing/cli_game.py): Versão para jogar direto no terminal.
- [`bot_engine.py`](file:///c:/Users/joker/OneDrive/Documentos/Turing/bot_engine.py): Motor lógico de geração de respostas e simulação de comportamentos/personas.
- [`requirements.txt`](file:///c:/Users/joker/OneDrive/Documentos/Turing/requirements.txt): Dependências do projeto.
