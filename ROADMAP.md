# Roadmap do Projeto: Login, Usuários, IA Local e Resposta Humana

## Visão geral
Este projeto deve evoluir em etapas para ter:
- login com diferentes perfis
- acesso de usuário comum
- acesso de operador/humano
- acesso de administrador
- conversa com IA local, sem custo
- transição para resposta humana quando necessário

---

## Fase 1 - Base da autenticação

### Objetivo
Permitir que cada pessoa tenha um login e um perfil diferente.

### O que precisa ser definido
- tipos de usuário:
  - usuario
  - operador
  - admin
- cadastro de usuários
- senha segura
- sessão ativa
- redirecionamento conforme perfil

### Conceitos a aprender
- autenticação
- autorização
- hash de senha
- sessão
- cookies / JWT
- RBAC (Role-Based Access Control)

### Entregável da fase
- tela de login funcional
- cadastro de usuário
- perfil atribuído ao usuário
- redirecionamento para página certa

---

## Fase 2 - Estrutura do sistema de chat

### Objetivo
Preparar a conversa para receber IA e também humana.

### O que precisa existir
- chat por usuário
- histórico de mensagens
- identificação de sessão
- estado da conversa
- botão de “falar com humano”

### Conceitos a aprender
- banco de dados relacional
- relacionamento entre usuários e mensagens
- estado de conversa
- fila de mensagens
- logs e auditoria

### Entregável da fase
- usuário consegue enviar e visualizar mensagens
- conversa fica salva
- operadores conseguem consultar o histórico

---

## Fase 3 - IA local gratuita

### Objetivo
Integrar um modelo de IA que funcione sem custo e sem depender de API paga.

### Melhor opção recomendada
- Ollama

### O que aprender
- instalação do Ollama
- escolha de modelo leve
- como chamar o modelo via Python
- prompt base
- contexto da conversa
- limites de memória e desempenho

### Modelos sugeridos
- Llama 3
- Mistral
- Gemma
- Qwen
- Phi

### Entregável da fase
- IA responde às mensagens do usuário
- respostas ficam registradas no histórico
- fluxo de conversa funciona sem depender de pagamento

---

## Fase 4 - Fallback para humano

### Objetivo
Permitir que uma pessoa real responda quando a IA não for suficiente.

### Regra de negócio sugerida
A conversa pode seguir assim:
- IA responde normalmente
- se o usuário pedir “falar com humano”
- ou se a IA não souber responder
- ou se o contexto indicar que a resposta precisa ser humana
- então a mensagem vai para operador

### Conceitos a aprender
- handoff entre IA e humano
- fila de atendimento
- botões de ação no chat
- regras de prioridade
- alocação de mensagens para operador

### Entregável da fase
- usuário pode solicitar humano
- operador consegue responder diretamente
- conversa continua com o contexto correto

---

## Fase 5 - Painel do operador

### Objetivo
Dar ao humano acesso ao fluxo de conversas.

### Funcionalidades do operador
- ver lista de usuários ativos
- visualizar conversas pendentes
- responder mensagens
- marcar conversa como resolvida
- ver mensagens da IA e do humano

### Conceitos a aprender
- dashboards simples
- gerenciamento de filas
- status de conversa
- filtros por usuário e sessão

### Entregável da fase
- operador consegue intervir e responder
- sistema mantém histórico do que foi feito

---

## Fase 6 - Painel do administrador

### Objetivo
Controlar o ambiente do sistema.

### Funcionalidades do admin
- ver usuários cadastrados
- alterar perfis
- ativar ou bloquear acessos
- ver estatísticas gerais
- controlar regras de IA e humano

### Conceitos a aprender
- administração de usuários
- relatórios
- logs de acesso
- regras de segurança

### Entregável da fase
- admin tem controle do sistema
- métricas e monitoramento simples

---

## Fase 7 - Segurança e validação

### Objetivo
Tornar o sistema utilizável de verdade.

### O que revisar
- senha com hash
- sessão expirada
- validação de entrada
- controle de rotas por perfil
- proteção contra abuso
- logs de ação

### Conceitos a aprender
- OWASP básico
- validação de dados
- proteção de endpoints
- boas práticas de autenticação

---

## Tecnologias recomendadas

### Em ordem prática
- Python
- FastAPI ou Flask
- SQLite (início)
- SQLAlchemy ou SQLModel
- HTML/CSS/JS
- Ollama

### Quando crescer
- PostgreSQL
- Redis
- WebSockets para chat ao vivo
- painel mais robusto em React ou Vue

---

## Ordem de implementação recomendada

1. login e perfis
2. banco de usuários e mensagens
3. chat base
4. IA local via Ollama
5. botão de “falar com humano”
6. painel do operador
7. painel do admin
8. segurança e refinamento

---

## Checklist de maturidade do projeto

### Já funcional
- [ ] cadastro de usuários
- [ ] login
- [ ] diferenciação por perfil
- [ ] chat básico
- [ ] IA respondendo localmente
- [ ] operador consegue responder
- [ ] histórico salvo
- [ ] controle de acesso

### Próximo nível
- [ ] conversa em tempo real
- [ ] painel de admin
- [ ] métricas e logs
- [ ] segurança mais robusta
- [ ] deploy simples

---

## Recomendação final
O caminho mais saudável é:
- primeiro autenticação
- depois chat
- depois IA
- depois humano
- depois admin

Não tente fazer tudo ao mesmo tempo. O segredo é construir em camadas com fluxo bem definido.
