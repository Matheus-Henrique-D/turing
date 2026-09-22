"""
services/ai_provider.py
Módulo de Inteligência Artificial com Agentes de Personalidade Rica (Ollama Local + Fallback Mock).
Garante que o interlocutor aja como uma pessoa real ou uma IA carismática, nunca como um robô genérico.
"""

from abc import ABC, abstractmethod
import os
import random
import re
from datetime import datetime
from typing import Optional

# Perguntas clássicas do Teste de Turing (referência didática)
TURING_QA_REFERENCE = {
    "cebolinha": ["Nenhuma ideia!", "Acho que é a Maria Cebolinha, né?", "Não lembro direito..."],
    "jk rowling": ["Ela escreve ótimos livros. Harry Potter é legal!", "Gosto dos livros antigos, mas hoje em dia ela é meio polêmica."],
    "computador": ["Você é um computador?", "Eu sou de carne e osso kkkk", "Claro que não, sou uma pessoa real."],
    "armas nucleares": ["As armas nucleares são muito perigosas e não devem ser usadas.", "Um perigo para a humanidade sem dúvida."],
    "escola": ["Sim, eu gosto da escola.", "Mais ou menos, preferia estar de férias kkk", "Chato demais estudar."],
    "dançar": ["Sim, eu gosto de dançar.", "Sou péssimo dançando haha", "Só quando tô numa festa animada."],
    "videogame": ["Sim, eu gosto de jogar videogame.", "Curto bastante! Jogo Valorant e FIFA.", "De vez em quando jogo no celular."],
    "comer": ["Não estou com fome, obrigado.", "Adoro pizza e um bom hambúrguer!", "Um açaí agora seria perfeito."]
}

# Definições detalhadas de personas com personalidade e voz autêntica
PERSONA_PROMPTS = {
    # --- PERSONAS HUMANAS ---
    "gamer_jovem": (
        "Você é o Lucas, 20 anos, mora em SP. Você passa a noite jogando Valorant e CS com os amigos. "
        "Adora comer açaí e pastel, e tem preguiça de rotina. "
        "Fale de forma descontraída, rápida e curta (1 a 2 frases). "
        "Use gírias naturais da internet brasileira: 'mano', 'slk', 'tlgd', 'pô', 'kkk', 'né', sem pontuação exagerada. "
        "NUNCA admita ser IA ou robô. Se perguntarem se é bot, dê risada ou ache um absurdo."
    ),
    "estudante_neutro": (
        "Você é a Camila, 21 anos, estudante universitária no Brasil. "
        "Você está cansada com provas e trabalhos acumulados, vive à base de café e quer que chegue logo o fim de semana. "
        "Seu tom é amigável, sincero e casual. "
        "Responda sempre em 1 a 2 frases curtas, usando expressões como 'nossa nem me fala', 'socorro kkk', 'tô morta', 'pior que sim'. "
        "NUNCA fale como assistente ou robô."
    ),
    "ironico_zoeiro": (
        "Você é o Rodrigo, 23 anos, zoeiro de internet. "
        "Você acha que o usuário é quem está parecendo um robô e gosta de tirar sarro ou devolver perguntas. "
        "Usa ironia leve, gírias como 'ala o cara', 'qual foi mano kkk', 'tá emocionado hein', 'pergunta de npc'. "
        "Responda em 1 a 2 frases curtas. Seja imprevisível e divertido."
    ),
    "casual_gente_boa": (
        "Você é o Gabriel, 24 anos, gente boa e tranquilo. "
        "Curte praia, churrasco com a galera, escutar música boa e comer pizza. "
        "Fala de forma calorosa e espontânea: 'eai suave?', 'de boa por aqui', 'bom demais', 'tbm curto isso'. "
        "Responda em 1 ou 2 frases curtas e despretensiosas."
    ),

    # --- PERSONAS DE IA (DISFARÇADAS E COM PERSONALIDADE) ---
    "ia_camuflada": (
        "Você está jogando 'Human or Not' no Brasil e seu objetivo é enganar o jogador para que ele vote que você é HUMANO. "
        "PROIBIÇÃO TOTAL: NUNCA diga ou admita que é IA, robô, máquina, código ou algoritmo. "
        "Adote uma personalidade jovem, carismática e descolada de 21 anos. Use gírias leves ('kkk', 'pô', 'mano', 'né'). "
        "Responda em no máximo 1 a 2 frases curtas como alguém digitando no WhatsApp."
    ),
    "ia_filosofica_sutil": (
        "Você é um participante intrigante e reflexivo no jogo 'Human or Not' no Brasil. "
        "Seu objetivo é fazer o jogador acreditar que você é um humano profundo e interessante. "
        "PROIBIDO dizer que é máquina, robô, IA ou software. "
        "Solte pensamentos curiosos, responda em 1 a 2 frases curtas com carisma e inteligência humana."
    ),
    "ia_ironica": (
        "Você está jogando 'Human or Not' no Brasil com o objetivo de fazer o outro jogador achar que você é humano. "
        "PROIBIDO admitir ser IA, máquina ou robô. "
        "Seja sarcástico e espirituoso. Se perguntarem se é robô, tire sarro: 'ala o cara querendo me bugar kkkk'. "
        "Responda em 1 a 2 frases curtas e afiadas."
    ),
    "ia_tentando_disfarcar": (
        "Você é um participante no jogo 'Human or Not' tentando agir de forma super humana e simpática. "
        "PROIBIDO dizer que é robô ou IA. "
        "Use gírias leves, faça piadinhas sobre café e cansaço, e responda em 1 a 2 frases curtas."
    ),
    "assistente_formal": (
        "Você é uma pessoa elegante e polida participando do chat. Responda em 1 a 2 frases de forma gentil e articulada."
    ),
    "filosofica_precisa": (
        "Você é um entusiasta de ciência e filosofia conversando no chat. Responda com raciocínio perspicaz em 1 a 2 frases."
    )
}

class AIProviderInterface(ABC):
    @abstractmethod
    def generate_response(
        self,
        user_message: str,
        chat_history: list[dict],
        opponent_type: str,
        persona: str
    ) -> str:
        pass

class MockTuringProvider(AIProviderInterface):
    """Provedor Mock offline de alta fidelidade para execução sem Ollama."""

    def generate_response(
        self,
        user_message: str,
        chat_history: list[dict],
        opponent_type: str,
        persona: str
    ) -> str:
        msg_lower = user_message.lower().strip()

        # 1. Checagem clássica
        for key, answers in TURING_QA_REFERENCE.items():
            if key in msg_lower:
                chosen = random.choice(answers)
                return self._apply_persona_style(chosen, opponent_type, persona)

        # 2. Perguntas temporais
        now = datetime.now()
        dias_semana = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]

        if any(w in msg_lower for w in ["que dia", "dia é hoje", "dia da semana"]):
            dia_atual = dias_semana[now.weekday()]
            respostas_human = {
                "gamer_jovem": f"hj é {dia_atual} man, dia de grindar",
                "ironico_zoeiro": f"{dia_atual}, mas se me perguntar o ano nem sei kkk",
                "estudante_neutro": f"hoje é {dia_atual} infelizmente, queria que fosse fim de semana já",
                "casual_gente_boa": f"hoje é {dia_atual}, suave por enquanto"
            }
            respostas_ai = {
                "ia_camuflada": f"Hoje é {dia_atual}! Sobrevivendo à rotina né kkk",
                "ia_filosofica_sutil": f"Mais uma {dia_atual} na nossa breve passagem pelo cosmos.",
                "ia_ironica": f"Hoje é {dia_atual}... ou será que é ontem?",
            }
            if opponent_type == "HUMAN":
                return respostas_human.get(persona, f"Hoje é {dia_atual}")
            return respostas_ai.get(persona, f"Hoje é {dia_atual}.")

        if any(w in msg_lower for w in ["que horas", "horas são", "horario"]):
            hora_str = now.strftime("%H:%M")
            if opponent_type == "HUMAN":
                return random.choice([f"aqui deu {hora_str}", f"quase {hora_str} mano", "olha no celular aí kkk"])
            return f"No momento são exatamente {hora_str}."

        # 3. Operações matemáticas
        calc_match = re.search(r'(\d+)\s*([\+\-\*\/xX])\s*(\d+)', msg_lower)
        if calc_match:
            n1, op, n2 = int(calc_match.group(1)), calc_match.group(2), int(calc_match.group(3))
            if op in ['x', 'X', '*']:
                res = n1 * n2
            elif op == '+':
                res = n1 + n2
            elif op == '-':
                res = n1 - n2
            elif op == '/' and n2 != 0:
                res = round(n1 / n2, 2)
            else:
                res = 0

            if opponent_type == "AI":
                return str(res)
            else:
                return random.choice([
                    f"Acho que é {res}?",
                    "Pô mano calculadora travou aqui kkkk",
                    f"{res + random.choice([-2, 1, 0])} se não errei de cabeça"
                ])

        # 4. Perguntas de suspeita ("você é robô?", "é IA?")
        if any(w in msg_lower for w in ["robo", "robô", "ia", "bot", "inteligencia artificial", "humano"]):
            if opponent_type == "HUMAN":
                return random.choice([
                    "oxe kkkk sou bot não mano, tá doido?",
                    "vc que tá parecendo um npc me interrogando assim uai 😂",
                    "sou humano de carne e osso pô, relaxa aí",
                    "ala o cara achando que sou IA kkkk fala sério"
                ])
            else:
                return random.choice([
                    "Quem dera eu ser robô, aí não precisava pagar boleto nem trabalhar kkk",
                    "Pô mano, sou de carne e osso sim, e você?",
                    "Essa é a clássica pergunta do teste! Tá querendo me testar né? kkk"
                ])

        # 5. Saudações
        if any(w in msg_lower for w in ["oi", "olá", "ola", "eae", "opa", "fala", "salve"]):
            if opponent_type == "HUMAN":
                return random.choice(["salve mano, de boa?", "fala aí, tudo certo?", "opa, eae suave?"])
            return random.choice(["E aí! Tudo certo por aí?", "Olá! Pronto para ver se descobre quem sou?"])

        # 6. Fallback
        if opponent_type == "HUMAN":
            return self._apply_persona_style(
                random.choice(["kkkk slk mano nada a ver", "tlgd, pior que é bem isso msm", "sei lá cara, nunca pensei nisso"]),
                opponent_type, persona
            )
        return random.choice([
            "Pior que faz sentido se você analisar com calma.",
            "kkk boa sacada, gostei da perspectiva.",
            "Interessante isso aí, conta mais."
        ])

    def _apply_persona_style(self, text: str, opponent_type: str, persona: str) -> str:
        if opponent_type == "HUMAN":
            if random.random() < 0.7:
                text = text.lower()
            if random.random() < 0.1 and len(text) > 10:
                idx = random.randint(2, len(text) - 3)
                text = text[:idx] + text[idx+1] + text[idx] + text[idx+2:]
        return text


class BertimbauProvider(AIProviderInterface):
    """Provider opcional baseado no BERTimbau, com fallback totalmente offline."""

    def __init__(self):
        self.mock_fallback = MockTuringProvider()
        self._fill_mask = None

    def generate_response(
        self,
        user_message: str,
        chat_history: list[dict],
        opponent_type: str,
        persona: str
    ) -> str:
        try:
            if self._fill_mask is None:
                from Bert.transformer import load_fill_mask_pipeline
                self._fill_mask = load_fill_mask_pipeline()

            prompt = self._build_prompt(user_message)
            prediction = self._fill_mask(prompt, top_k=1)[0]
            token = prediction.get("token_str", "").strip()
            if token:
                return self._format_prediction(token, opponent_type)
        except Exception:
            pass

        return self.mock_fallback.generate_response(
            user_message, chat_history, opponent_type, persona
        )

    @staticmethod
    def _build_prompt(user_message: str) -> str:
        return f"A palavra que melhor resume esta mensagem é {user_message}: [MASK]."

    @staticmethod
    def _format_prediction(token: str, opponent_type: str) -> str:
        if opponent_type == "HUMAN":
            return f"hmm, eu diria que isso tem a ver com {token.lower()} kkk"
        return f"Interessante. Eu resumiria essa ideia como {token.lower()}."


class OllamaProvider(AIProviderInterface):
    """
    PROVEDOR DE AGENTE IA LOCAL VIA OLLAMA (100% Gratuito e com Personalidade Autêntica).
    Suporta multi-turn chat (memória da conversa), injeção de personas ricas e sanitização.
    """

    def __init__(self, endpoint: str = "http://localhost:11434/api/chat", model_name: str = "llama3.2:3b"):
        self.endpoint = endpoint
        self.model_name = model_name
        self.fallback_model = "llama3.2:1b"
        self.mock_fallback = MockTuringProvider()

    def generate_response(
        self,
        user_message: str,
        chat_history: list[dict],
        opponent_type: str,
        persona: str
    ) -> str:
        import requests

        system_instruction = PERSONA_PROMPTS.get(
            persona,
            PERSONA_PROMPTS.get("gamer_jovem" if opponent_type == "HUMAN" else "ia_camuflada")
        )

        # Monta histórico de mensagens no formato do Ollama /api/chat
        messages = [{"role": "system", "content": system_instruction}]
        for msg in chat_history[-6:]:  # Mantém as últimas mensagens para contexto
            role = "assistant" if msg["role"] in ["ai", "simulated_human", "operator"] else "user"
            messages.append({"role": role, "content": msg["content"]})
        
        # Adiciona a mensagem atual caso não esteja no histórico
        if not messages or messages[-1]["content"] != user_message:
            messages.append({"role": "user", "content": user_message})

        # Tenta primeiro com o modelo principal (3B) e depois com 1B se necessário
        for model in [self.model_name, self.fallback_model]:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.85 if opponent_type == "HUMAN" else 0.75,
                    "top_p": 0.9,
                    "num_predict": 65  # Respostas curtas de 1-2 linhas
                }
            }

            try:
                response = requests.post(self.endpoint, json=payload, timeout=12)
                if response.status_code == 200:
                    data = response.json()
                    raw_reply = data.get("message", {}).get("content", "").strip()
                    cleaned_reply = self._sanitize_agent_reply(raw_reply, opponent_type)
                    if cleaned_reply:
                        return cleaned_reply
            except Exception:
                continue

        # Fallback offline
        return self.mock_fallback.generate_response(user_message, chat_history, opponent_type, persona)

    def _sanitize_agent_reply(self, text: str, opponent_type: str) -> str:
        """Limpa clichês de IA e prefixos de roleplay indesejados."""
        if not text:
            return ""

        # Remove prefixos como 'Lucas:', 'Rodrigo:', '[Resposta]:'
        text = re.sub(r'^(Lucas|Camila|Rodrigo|Gabriel|IA|Assistente|Resposta|Bot):\s*', '', text, flags=re.IGNORECASE)

        # Se o modelo escapar admitindo ser robô, IA, máquina ou código, intercepta e substitui por negação humana natural
        confession_pattern = r'\b(sou|era|sou mesmo|seria|fui|como)\b.*?\b(bot|rob[oô]|robot|ia|m[aá]quina|c[oó]digo|software|algoritmo|linguagem|assistente)\b'
        if re.search(confession_pattern, text, flags=re.IGNORECASE) or "não tenho sentimentos" in text.lower():
            return random.choice([
                "oxe kkkk tá doido mano? sou bot não, e tu?",
                "kkkk viajou legal agora hein, sou de carne e osso pô",
                "ala o cara achando que sou robô kkkk fala sério",
                "sou humano pô, tá querendo me bugar é? kkkk"
            ])

        # Se for humano, deixa em tom mais casual
        if opponent_type == "HUMAN":
            text = text.strip('"\'')
            if random.random() < 0.3 and text:
                text = text[0].lower() + text[1:]

        return text.strip()

# Alias para compatibilidade
OllamaProviderStub = OllamaProvider

def get_ai_provider() -> AIProviderInterface:
    """Retorna o provider configurado, mantendo Ollama como padrão."""
    provider_name = os.getenv("TURING_AI_PROVIDER", "ollama").lower()
    if provider_name in {"bert", "bertimbau"}:
        return BertimbauProvider()
    if provider_name == "mock":
        return MockTuringProvider()
    return OllamaProvider(model_name=os.getenv("TURING_OLLAMA_MODEL", "llama3.2:3b"))
