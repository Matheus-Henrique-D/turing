# 🤖 Human or Not? — Plataforma Teste de Turing 👤

Plataforma interativa inspirada no **[humanornot.so](https://humanornot.so)** e no material didático do **Teste de Turing**, desenvolvida com arquitetura limpa em camadas (*Clean Architecture*), controle de acesso baseado em papéis (**RBAC**), persistência relacional em **SQLite**, suporte a **Handoff Humano** e **Mocks de IA**.

---

## 🚀 Funcionalidades Implementadas (Roadmap Fases 1 a 7)

- **Fase 1: Autenticação & Perfis (RBAC)**
  - Cadastro de usuários com validação e hash seguro (`PBKDF2-HMAC-SHA256` com salt individual).
  - Perfis de acesso distintos: `usuario` (jogador), `operador` (atendimento humano) e `admin` (gestão e governança).
- **Fase 2: Chat Estruturado & Persistência Relacional**
  - Banco de dados SQLite (`data/turing_platform.db`) com histórico completo de mensagens, sessões e logs.
  - Regra de negócio de 5 turnos com controle estrito e contador em tempo real.
- **Fase 3: IA Local (Mocks & Stubs Desacoplados)**
  - Operação 100% offline e sem consumo de APIs externas via `MockTuringProvider` enriquecido com personas comportamentais (`gamer_jovem`, `ironico_zoeiro`, `estudante_neutro`, `assistente_formal`, `ia_tentando_disfarcar`, `filosofica_precisa`).
  - `OllamaProviderStub` preparado para conexão futura com IA local gratuita via Ollama.
- **Fase 4: Handoff para Operador Humano**
  - Botão *"Falar com Humano"* durante o chat: transfere a sessão para a fila de atendimento humano.
- **Fase 5: Painel do Operador**
  - Fila de atendimento ao vivo, visualização do histórico e resposta direta do operador para o jogador.
- **Fase 6: Painel do Administrador**
  - Gestão de usuários (ativação, bloqueio e promoção de perfis RBAC), métricas consolidadas e trilha de auditoria.
- **Fase 7: Segurança e Testes Automatizados**
  - Sanitização de entradas, proteção contra timing-attacks e suíte de testes unitários com 100% de aprovação.

---

## 🔐 Contas Padrão de Demonstração

Ao inicializar o sistema pela primeira vez, as seguintes contas pré-configuradas ficam disponíveis para teste imediato:

| Perfil | Usuário (Login) | Senha | Acesso / Permissões |
|---|---|---|---|
| **Administrador** | `admin` | `admin123` | Painel de controle, gestão de usuários, RBAC, métricas e auditoria |
| **Operador** | `operador` | `operador123` | Painel de atendimento ao vivo, fila de handoff e respostas diretas |
| **Jogador** | `jogador1` | `jogador123` | Jogo Teste de Turing, chat de 5 turnos, votação e solicitação de humano |

*Você também pode criar novos usuários a qualquer momento pela aba "Criar Conta".*

---

## 🛠️ Como Executar a Aplicação

### 1. Interface Web Completa (Streamlit) — Recomendada 🌟
```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Executar a aplicação web
streamlit run app.py
```
Acesse no seu navegador: `http://localhost:8501`.

### Selecionar o provider de IA

O padrão continua sendo o Ollama. Para testar o BERTimbau como provider opcional:

```powershell
$env:TURING_AI_PROVIDER = "bertimbau"
streamlit run app.py
```

O BERTimbau é um modelo de preenchimento de máscara, então ele gera respostas curtas assistidas por contexto e não substitui um modelo conversacional. O provider carrega os pesos sob demanda e usa o mock offline automaticamente quando `torch`, os pesos locais ou o download do modelo não estão disponíveis. Para voltar ao Ollama, remova a variável ou use `$env:TURING_AI_PROVIDER = "ollama"`.

### 2. Interface Terminal (CLI) 💻
```bash
python cli_game.py
```
*Oferece efeito typewriter letra a letra e opção de salvar histórico no banco de dados SQLite.*

### 3. Executar a Suíte de Testes Automatizados 🧪
```bash
python -m unittest discover -s tests
```

---

## 📁 Estrutura do Projeto

```
Turing/
│
├── core/                       # Núcleo do sistema
│   ├── config.py               # Configurações globais e constantes do jogo
│   ├── security.py             # Hash criptográfico PBKDF2, salts e validação de senhas
│   └── database.py             # Conexão SQLite, criação de tabelas e seeds automáticos
│
├── models/                     # Entidades e Repositórios de Dados
│   ├── user.py                 # Entidade e CRUD de Usuários
│   ├── session.py              # Entidade e CRUD de Sessões de Jogo e Estatísticas
│   └── message.py              # Entidade e Persistência de Mensagens
│
├── services/                   # Camada de Serviços de Negócio
│   ├── auth_service.py         # Login, Registro e Verificação RBAC
│   ├── game_service.py         # Mecânica do Teste de Turing (5 turnos e votação)
│   ├── handoff_service.py      # Fila de espera e atendimento por operadores
│   ├── admin_service.py        # Gestão administrativa, métricas e auditoria
│   └── ai_provider.py          # Provedor de IA: Mock offline e Stub para Ollama
│
├── tests/                      # Suíte de Testes Unitários Automatizados
│   ├── test_security.py        # Testes de criptografia e regras de senha
│   ├── test_auth.py            # Testes de login, registro e RBAC
│   ├── test_game.py            # Testes do ciclo de 5 turnos e votação
│   ├── test_handoff.py         # Testes de solicitação e atendimento humano
│   └── test_ai_provider.py     # Testes do Mock isolado sem chamadas de rede
│
├── GUIA_INTEGRACAO_EXTERNA.md  # Guia passo a passo para conectar Ollama / APIs reais
├── PRD_Human_or_Not.md         # Documento de Requisitos de Produto (PRD)
├── ROADMAP.md                  # Roadmap arquitetural das fases 1 a 7
├── app.py                      # Aplicação Web Streamlit multi-perfil
├── cli_game.py                 # Aplicação interativa para terminal
├── bot_engine.py               # Motor mantido para compatibilidade retroativa
└── requirements.txt            # Dependências Python
```

---

## 📖 Guia para Conectar IA Real (Ollama)

Conforme a regra estrita do projeto, a aplicação não efetua requisições para serviços externos de terceiros por padrão. Para aprender a conectar um modelo local (como Llama 3, Mistral, Gemma ou Phi) via Ollama, consulte o documento:

👉 **[GUIA_INTEGRACAO_EXTERNA.md](GUIA_INTEGRACAO_EXTERNA.md)**
