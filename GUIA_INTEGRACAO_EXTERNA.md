# 📘 Guia Completo de Integração Externa: IA Local e Serviços de Terceiros

Este documento foi elaborado para que você, desenvolvedor, possa conectar serviços externos e modelos de Inteligência Artificial reais (locais ou na nuvem) à aplicação com total controle e segurança.

Em conformidade com a sua regra estrita:
> **A aplicação foi entregue 100% funcional em modo isolado (Mock/Stub)**. Nenhuma chamada externa é feita automaticamente. Os pontos exatos de integração foram preparados como *stubs* desacoplados.

---

## 📑 Sumário
1. [Arquitetura dos Mocks e Stubs](#1-arquitetura-dos-mocks-e-stubs)
2. [Passo a Passo: Como Conectar o Ollama (IA Local Gratuita)](#2-passo-a-passo-como-conectar-o-ollama-ia-local-gratuita)
3. [Como Testar a IA Local na Aplicação](#3-como-testar-a-ia-local-na-aplicação)
4. [Passo a Passo: Como Conectar Provedores em Nuvem (Groq / OpenAI / Gemini)](#4-passo-a-passo-como-conectar-provedores-em-nuvem-groq--openai--gemini)
5. [Boas Práticas de Segurança e Ambientes](#5-boas-práticas-de-segurança-e-ambientes)

---

## 1. Arquitetura dos Mocks e Stubs

No diretório `services/ai_provider.py`, existe uma interface limpa:

```python
class AIProviderInterface(ABC):
    @abstractmethod
    def generate_response(self, user_message, chat_history, opponent_type, persona) -> str:
        pass
```

- **`MockTuringProvider` (Ativo)**: Responsável por simular os humanos (gírias, typos, respostas curtas) e as IAs sem depender de internet ou GPU.
- **`OllamaProviderStub` (Espaço Reservado)**: Contém o layout da requisição pronto para receber o envio de prompts ao Ollama.
- **`get_ai_provider()`**: Função fábrica no final de `services/ai_provider.py` que define qual provedor a aplicação utiliza.

---

## 2. Passo a Passo: Como Conectar o Ollama (IA Local Gratuita)

O **Ollama** permite rodar modelos de linguagem (LLMs) direto na sua máquina (CPU ou GPU), sem pagar por tokens e com total privacidade.

### Etapa 2.1 — Instalação do Ollama
1. Acesse o site oficial: [https://ollama.com](https://ollama.com) e baixe o instalador para Windows.
2. Execute o instalador. Após a conclusão, abra o seu terminal (PowerShell) e verifique:
   ```bash
   ollama --version
   ```

### Etapa 2.2 — Modelos Leves Recomendados (100% Gratuitos)
O modelo **`llama3.2:1b`** (Meta Llama 3.2 1B - ~1.3 GB) já foi baixado e configurado como padrão no projeto devido à sua altíssima velocidade, excelente compreensão de português e baixo consumo de memória.

Caso queira experimentar outros modelos no futuro, basta executar no terminal:
- `ollama pull llama3.2:3b` (~2.0 GB — modelo ligeiramente mais inteligente)
- `ollama pull phi3:mini` (~2.2 GB — modelo leve da Microsoft)
- `ollama pull qwen2.5:1.5b` (~980 MB — modelo super compacto)

Para listar os modelos já instalados na sua máquina:
```bash
ollama list
```

---

### Etapa 2.3 — Ativar a Chamada Real no Código

Abra o arquivo [`services/ai_provider.py`](file:///c:/Users/joker/OneDrive/Documentos/Turing/services/ai_provider.py).

#### 1. Modifique o método `generate_response` da classe `OllamaProviderStub`:

Substitua o corpo do método pelo código abaixo:

```python
import requests

class OllamaProviderStub(AIProviderInterface):
    def __init__(self, endpoint: str = "http://localhost:11434/api/generate", model_name: str = "llama3"):
        self.endpoint = endpoint
        self.model_name = model_name
        self.mock_fallback = MockTuringProvider()

    def generate_response(
        self,
        user_message: str,
        chat_history: list[dict],
        opponent_type: str,
        persona: str
    ) -> str:
        system_prompt = self._build_system_prompt(opponent_type, persona)
        payload = {
            "model": self.model_name,
            "prompt": user_message,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.8 if opponent_type == "HUMAN" else 0.3
            }
        }
        
        try:
            # Requisição HTTP direta ao daemon do Ollama
            response = requests.post(self.endpoint, json=payload, timeout=12)
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()
            else:
                print(f"[Aviso] Ollama retornou código {response.status_code}. Usando fallback.")
                return self.mock_fallback.generate_response(user_message, chat_history, opponent_type, persona)
        except Exception as e:
            print(f"[Erro de Conexão com Ollama]: {e}. Ativando mock seguro.")
            return self.mock_fallback.generate_response(user_message, chat_history, opponent_type, persona)
```

#### 2. Alterne a fábrica para retornar o `OllamaProviderStub`:

No final de `services/ai_provider.py`:

```python
# Altere de:
def get_ai_provider() -> AIProviderInterface:
    return MockTuringProvider()

# Para:
def get_ai_provider() -> AIProviderInterface:
    return OllamaProviderStub(model_name="llama3")
```

---

## 3. Como Testar a IA Local na Aplicação

1. Certifique-se de que o Ollama está rodando (`curl http://localhost:11434` no terminal retornará *"Ollama is running"*).
2. Inicie o Streamlit:
   ```bash
   streamlit run app.py
   ```
3. Faça login e inicie uma partida. Se o sorteio selecionar "IA", quem gerará a resposta será o modelo local rodando no seu computador!

---

## 4. Passo a Passo: Como Conectar Provedores em Nuvem (Groq / OpenAI / Gemini)

Caso prefira utilizar um provedor em nuvem no futuro:

### 1. Criar um arquivo `.env` na raiz do projeto:
```env
GROQ_API_KEY=gsk_sua_chave_aqui
OPENAI_API_KEY=sk-sua_chave_aqui
```

### 2. Criar uma nova classe de Provedor (exemplo com Groq):
Adicione em `services/ai_provider.py`:

```python
import os
from groq import Groq

class GroqCloudProvider(AIProviderInterface):
    def __init__(self, model_name: str = "llama-3.1-8b-instant"):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model_name = model_name

    def generate_response(self, user_message, chat_history, opponent_type, persona):
        system_prompt = (
            "Aja como humano comum com gírias brasileiras." if opponent_type == "HUMAN"
            else "Aja como uma IA analítica no Teste de Turing."
        )
        
        chat_completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model=self.model_name,
            max_tokens=60
        )
        return chat_completion.choices[0].message.content
```

---

## 5. Boas Práticas de Segurança e Ambientes

1. **Nunca versione chaves:** Adicione `.env` e qualquer arquivo com senhas ao `.gitignore` (já configurado no projeto).
2. **Fallback Gracioso:** Sempre encapsule requisições externas com blocos `try/except` para que, caso a internet caia ou o servidor do Ollama seja fechado, a aplicação continue funcionando através do `MockTuringProvider`.
3. **Limitação de Tokens:** No Teste de Turing, respostas humanas devem ser curtas (1 a 2 sentenças). Ajuste `max_tokens` entre 40 e 80 para evitar respostas gigantescas que entregam imediatamente que se trata de uma IA.
