# PRD — Human or Not? (Minijogo do Teste de Turing)

**Versão do documento:** 1.0
**Data:** 13/09/2026
**Autor:** Theus
**Status:** Rascunho para validação

---

## 1. Visão Geral

### 1.1 Resumo
"Human or Not?" é um minijogo inspirado no **humanornot.so** e em material didático sobre o **Teste de Turing**. O usuário conversa por 5 mensagens com um interlocutor cuja identidade (Humano ou IA) é sorteada aleatoriamente, e ao final precisa adivinhar com quem estava falando. O jogo registra acertos e erros ao longo das partidas.

### 1.2 Problema que resolve
Oferecer, de forma lúdica, uma experiência prática que ilustra os conceitos do Teste de Turing — ambiguidade entre respostas humanas e artificiais — servindo como ferramenta educacional e de entretenimento.

### 1.3 Público-alvo
- Estudantes e curiosos sobre IA e o Teste de Turing.
- Uso didático em contexto acadêmico (a julgar pela origem do projeto e do `ROADMAP.md`).

### 1.4 Estado atual do projeto
Existem duas implementações funcionais e independentes, sem persistência de dados entre sessões, sem autenticação e sem integração com LLM real:

| Arquivo | Função |
|---|---|
| `app.py` | Interface web em Streamlit, com chat estilizado, contador de turnos, tela de votação e resultado. |
| `cli_game.py` | Versão para terminal, sem dependências além do Python padrão. |
| `bot_engine.py` | Motor de geração de respostas simuladas (regras + heurísticas), compartilhado pelas duas interfaces. |
| `requirements.txt` | Única dependência declarada: `streamlit>=1.30.0`. |
| `README.md` | Documentação de uso e instruções de execução. |
| `ROADMAP.md` | Plano de evolução para uma plataforma multiusuário com login, IA local via Ollama e atendimento humano. |

O `ROADMAP.md` descreve uma visão de produto **muito mais ambiciosa** do que o que existe hoje: um sistema completo com autenticação, perfis (usuário/operador/admin), IA local via Ollama, fallback para atendimento humano e painéis administrativos. Esse PRD documenta o estado atual e organiza a evolução proposta.

---

## 2. Objetivos

### 2.1 Objetivos do produto (estado atual)
- Proporcionar uma experiência de chat de 5 turnos com um "interlocutor misterioso".
- Sortear aleatoriamente (50/50) se o interlocutor é "Humano" ou "IA".
- Simular padrões linguísticos distintos para cada tipo (gírias/erros de digitação para humano; respostas polidas/estruturadas para IA).
- Permitir votação do usuário ao final da conversa e revelar o resultado.
- Manter um placar de partidas jogadas e acertos.

### 2.2 Objetivos de evolução (conforme ROADMAP.md)
- Adicionar autenticação e perfis de usuário (usuário comum, operador, admin).
- Persistir usuários, sessões e histórico de mensagens em banco de dados.
- Substituir/complementar o motor de respostas simuladas por um LLM local via Ollama.
- Implementar handoff (transferência) da IA para um humano real quando necessário.
- Criar painéis de operador e administrador.
- Reforçar segurança (hash de senha, validação de entradas, controle de acesso por rota).

### 2.3 Não-objetivos (fora de escopo nesta fase)
- Suporte a múltiplos idiomas (o jogo é 100% em português).
- Monetização ou modelo de negócio.
- Aplicativo mobile nativo.
- Integração com LLMs pagos (Fase 3 do roadmap prevê explicitamente uma solução **sem custo**, via Ollama).

---

## 3. Personas

| Persona | Descrição | Necessidade |
|---|---|---|
| **Jogador casual** | Usuário que quer se divertir tentando identificar IA vs Humano. | Interface simples, feedback rápido, placar visível. |
| **Estudante/Pesquisador** | Usa o jogo para entender na prática os limites do Teste de Turing. | Perguntas sugeridas, transparência sobre o funcionamento. |
| **Operador (futuro)** | Pessoa que assume conversas quando a IA falha ou o usuário pede atendimento humano. | Painel com fila de conversas pendentes e histórico. |
| **Administrador (futuro)** | Gerencia usuários, perfis e políticas do sistema. | Painel de controle, métricas, logs de acesso. |

---

## 4. Escopo Funcional Atual (Detalhado por Módulo)

### 4.1 `bot_engine.py` — Motor de Respostas

**Classe `TuringOpponent`:**
- Ao ser instanciada, sorteia `opponent_type` (`"HUMAN"` ou `"AI"`) com 50% de chance cada, caso não seja informado explicitamente.
- Associa uma **persona** aleatória conforme o tipo:
  - Humano: `gamer_jovem`, `estudante_neutro`, `ironico_zoeiro`.
  - IA: `assistente_formal`, `ia_tentando_disfarcar`, `filosofica_precisa`.
  - *Observação: as personas são atribuídas mas atualmente não diferenciam o conteúdo das respostas em `_generate_simulated_response` — a lógica de resposta é a mesma para qualquer persona dentro do mesmo `opponent_type`. Isso é uma inconsistência entre o design pretendido e a implementação atual.*

**Método `get_response(user_message)`:**
Percorre uma cadeia de regras, na seguinte ordem de prioridade:
1. **Correspondência com banco de perguntas clássicas** (`TURING_QA_REFERENCE`): palavras-chave como "cebolinha", "jk rowling", "computador", "armas nucleares", "escola", "dançar", "videogame", "comer".
2. **Perguntas temporais**: "que dia", "que horas" → responde com data/hora real do sistema, com fraseado diferente por tipo.
3. **Operações matemáticas simples**: detecta padrão `número operador número` via regex e calcula (+, -, *, /); humanos "erram de propósito" ou respondem com informalidade, IA responde o valor exato.
4. **Perguntas de suspeita** ("robô", "ia", "bot", "humano"): respostas de negação/afirmação de identidade, diferentes por tipo.
5. **Saudações**: reconhece variações comuns e responde de forma correspondente ao tipo.
6. **Fallback genérico**: lista de respostas genéricas por tipo quando nada mais corresponde.

**Método `_apply_style`:**
Para respostas de humanos, aplica com certa probabilidade:
- Conversão para minúsculas (70% de chance).
- Simulação de erro de digitação por troca de dois caracteres adjacentes (10% de chance, só em textos >10 caracteres).

**Método `_generate_llm_response`:**
Atualmente é apenas um *placeholder* — chama `_generate_simulated_response` mesmo quando um `api_client` é passado no construtor. Não há integração real com LLM.

### 4.2 `app.py` — Interface Web (Streamlit)

**Configuração e estilo:**
- Layout centralizado, ícone de robô, tema com CSS customizado (títulos, badges, caixas de votação e cards de resultado com gradientes).

**Estado de sessão (`st.session_state`):**
- `stats`: contador global de `games` e `wins` (persiste apenas durante a sessão do navegador, perdido ao fechar/recarregar completamente).
- `opponent`: instância atual de `TuringOpponent`.
- `messages`: histórico da conversa atual.
- `game_phase`: máquina de estados com três fases — `"chat"`, `"voting"`, `"result"`.
- `user_vote`: voto do usuário na rodada atual.

**Barra lateral:**
- Explicação das regras.
- Métricas de desempenho (partidas e taxa de acerto).
- Expansor com sugestões de perguntas clássicas do Teste de Turing.
- Botão de reiniciar partida.

**Fluxo principal (máquina de estados):**
1. **Fase "chat"**: exibe histórico, aceita input via `st.chat_input`, simula "digitando..." com delay diferenciado (humano: 1.2–2.5s: IA: 0.6–1.4s), gera resposta via `bot_engine`, incrementa contador. Ao atingir 5 mensagens do usuário, transiciona para "voting".
2. **Fase "voting"**: bloqueia novo input, exibe dois botões (IA / Humano). Ao votar, atualiza `stats` e transiciona para "result".
3. **Fase "result"**: exibe card de vitória ou derrota com gradiente, mostra o palpite do usuário vs. a verdade, e permite reiniciar.

### 4.3 `cli_game.py` — Interface de Terminal

- Efeito "typewriter" implementado (`typewriter_print`), porém **não utilizado** na função `main()` — as respostas são impressas com `print()` comum, não com o efeito de digitação letra a letra. Isso é código morto/não integrado.
- Laço principal roda indefinidamente até o usuário optar por não jogar novamente ou interromper (Ctrl+C / EOF).
- Cada rodada: 5 turnos de input do usuário, com resposta do oponente após delay simulado (`time.sleep`) e limpeza visual do aviso "digitando".
- Validação de voto restrita a "1" ou "2".
- Placar acumulado (`score_games`, `score_wins`) mantido apenas em memória durante a execução do processo — perdido ao fechar o terminal.
- Uso de emojis para reforçar a identidade visual também no terminal.

### 4.4 `requirements.txt`
- Declara apenas `streamlit>=1.30.0`. Como `cli_game.py` não depende de bibliotecas externas além da biblioteca padrão, essa dependência é exclusiva do `app.py`.

---

## 5. Regras de Negócio

| Regra | Descrição |
|---|---|
| RN01 | Cada rodada tem exatamente 5 mensagens do usuário. |
| RN02 | O tipo do interlocutor (Humano/IA) é sorteado com 50% de probabilidade a cada nova rodada. |
| RN03 | O usuário deve votar obrigatoriamente entre "IA" ou "Humano" ao final da rodada. |
| RN04 | O placar (partidas/vitórias) é acumulado apenas durante a sessão ativa (sem persistência em disco/banco). |
| RN05 | Respostas de humanos podem conter gírias, erros de digitação propositais e informalidade; respostas de IA tendem a ser mais estruturadas e "corretas". |
| RN06 | Perguntas matemáticas são respondidas corretamente pela IA e com erro/informalidade proposital pelo humano simulado. |

---

## 6. Limitações e Inconsistências Identificadas no Código Atual

Vale destacar estes pontos para priorização de correções:

1. **Personas não afetam de fato as respostas.** O atributo `self.persona` é definido mas nunca lido dentro de `_generate_simulated_response`; todas as personas do mesmo tipo (humano ou IA) respondem de forma idêntica.
2. **`_generate_llm_response` é um stub.** Não existe, hoje, nenhuma chamada real a um provedor de LLM (nem local via Ollama, nem externo) — apesar do docstring do módulo mencionar Gemini/OpenAI/Groq.
3. **Efeito "typewriter" não utilizado no CLI.** A função existe mas não é chamada em `main()`.
4. **Sem persistência de dados.** Estatísticas e histórico se perdem a cada reinício (tanto na versão Streamlit quanto na CLI).
5. **Sem testes automatizados.** Não há arquivos de teste no projeto.
6. **Roadmap muito além do código atual.** O `ROADMAP.md` descreve login, RBAC, banco relacional, IA local e painéis — nenhum desses itens está implementado; o projeto está na "Fase 0" em relação a esse plano.
7. **Links do README apontam para caminho local do autor** (`file:///c:/Users/joker/...`), o que quebra para qualquer outra pessoa que abrir o README.

---

## 7. Roadmap de Evolução (baseado em `ROADMAP.md`)

| Fase | Objetivo | Principais entregáveis |
|---|---|---|
| **Fase 1** | Autenticação e perfis | Login funcional, cadastro, hash de senha, sessão, redirecionamento por perfil (usuário/operador/admin) |
| **Fase 2** | Estrutura de chat persistente | Histórico salvo em banco relacional, estado de conversa, botão "falar com humano" |
| **Fase 3** | IA local gratuita | Integração com Ollama (Llama 3, Mistral, Gemma, Qwen ou Phi), prompt base e gerenciamento de contexto |
| **Fase 4** | Fallback para humano | Regras de handoff (pedido explícito, IA insuficiente, contexto sensível), fila de atendimento |
| **Fase 5** | Painel do operador | Lista de conversas ativas/pendentes, resposta direta, marcação de resolvido |
| **Fase 6** | Painel do administrador | Gestão de usuários, ativação/bloqueio, métricas, controle de regras de IA/humano |
| **Fase 7** | Segurança e validação | Revisão de hashing, expiração de sessão, validação de entradas, proteção de rotas, práticas OWASP |

**Stack recomendada no roadmap:** Python, FastAPI ou Flask, SQLite (evoluindo depois para PostgreSQL), SQLAlchemy/SQLModel, HTML/CSS/JS, Ollama; com Redis e WebSockets para chat em tempo real em estágio avançado.

---

## 8. Métricas de Sucesso (sugeridas)

Como não há métricas formalizadas no projeto hoje, seguem sugestões alinhadas ao que já é exibido na interface:

- **Taxa de acerto do jogador** (já calculada: `wins / games`).
- **Distribuição de acertos por tipo de oponente** (ainda não medido: separar taxa de acerto quando o oponente real era Humano vs. quando era IA — indicaria se um dos dois é "mais fácil de identificar").
- **Tempo médio de resposta do usuário por turno** (não coletado atualmente).
- Para as fases futuras: número de handoffs para operador, tempo médio de resolução por operador, taxa de reincidência de usuários.

---

## 9. Riscos

| Risco | Impacto | Mitigação sugerida |
|---|---|---|
| Falta de persistência real | Estatísticas perdidas a cada sessão, ruim para engajamento de longo prazo | Priorizar banco de dados simples (SQLite) antes de qualquer painel |
| Complexidade do roadmap vs. tempo disponível (projeto acadêmico) | Risco de abandono nas fases finais (5–7) | Entregar em fatias verticais pequenas e funcionais, validando cada fase isoladamente |
| Ausência de testes | Regressões silenciosas ao evoluir `bot_engine.py` | Introduzir testes unitários básicos para as regras de resposta antes de acrescentar IA local |
| Dependência de Ollama rodando localmente | Pode não funcionar em todos os ambientes de avaliação/apresentação | Manter o motor simulado atual como fallback automático caso o Ollama não esteja disponível |

---

## 10. Próximos Passos Recomendados

1. Corrigir as inconsistências da Seção 6 (personas, stub de LLM, typewriter não usado, links do README).
2. Definir se o foco imediato é polir o jogo atual (Fase 0) ou já iniciar a Fase 1 do roadmap (login).
3. Se for avançar no roadmap, começar pela Fase 1 (autenticação) por ser pré-requisito de todas as demais.
4. Avaliar se o motor de regras atual deve conviver com o LLM local (modo híbrido) ou ser totalmente substituído na Fase 3.

---

*Documento gerado a partir da leitura direta do código-fonte (`app.py`, `cli_game.py`, `bot_engine.py`), `README.md`, `requirements.txt` e `ROADMAP.md` fornecidos.*
