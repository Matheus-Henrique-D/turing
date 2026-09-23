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

# ---------------------------------------------------------------------------
# BANCO DE RESPOSTAS POR TÓPICO (alta variedade para evitar repetição)
# ---------------------------------------------------------------------------
TURING_QA_REFERENCE = {
    "cebolinha": ["Nenhuma ideia!", "Acho que é a Maria Cebolinha né?", "Não lembro direito..."],
    "jk rowling": [
        "Ela escreve ótimos livros. Harry Potter é legal!",
        "Gosto dos livros antigos, mas hoje ela é bem polêmica.",
        "Adoro Harry Potter, mas aí as opiniões dela sobre trans arruinaram um pouco né",
    ],
    "computador": [
        "Você é um computador?", "Eu sou de carne e osso kkkk",
        "Claro que não, sou uma pessoa real.", "Hm que pergunta estranha kkk",
    ],
    "armas nucleares": [
        "As armas nucleares são muito perigosas e não devem ser usadas.",
        "Um perigo pra humanidade sem dúvida.",
        "Cara, espero que nunca usem isso de verdade né",
    ],
    "escola": [
        "Sim, eu gosto da escola.", "Mais ou menos, preferia estar de férias kkk",
        "Chato demais estudar.", "Depende do dia haha",
    ],
    "dançar": [
        "Sim, eu gosto de dançar.", "Sou péssimo dançando haha",
        "Só quando tô numa festa animada.", "Dançar eu danço, mas com vergonha kkk",
    ],
    "videogame": [
        "Sim, eu gosto de jogar videogame.", "Curto bastante! Jogo Valorant e FIFA.",
        "De vez em quando jogo no celular.", "Antes jogava muito, agora só nos fins de semana",
        "Valorant tá me destruindo ultimamente kkk",
    ],
    "comer": [
        "Não estou com fome, obrigado.", "Adoro pizza e um bom hambúrguer!",
        "Um açaí agora seria perfeito.", "To com vontade de comer uma pizza agora kkk",
        "Depende o que tiver na geladeira rs",
    ],
}

# ---------------------------------------------------------------------------
# POOL DE RESPOSTAS DE FALLBACK — por persona e por categoria temática
# (grande variedade para nunca repetir na mesma partida)
# ---------------------------------------------------------------------------
FALLBACK_HUMAN: dict[str, list[str]] = {
    "gamer_jovem": [
        "kk slk mano isso aí tá loco",
        "tlgd, nem pensei nisso antes",
        "pô mano, complicado",
        "cara que pergunta estranha",
        "kkk não entendi bem não",
        "mano isso aí vai fundo",
        "que situação hein",
        "deixa eu pensar... sim acho q sim",
        "sei lá cara, cada um né",
        "kkk olha só",
        "real demais isso",
        "mano bora jogar e esquecer isso kkkk",
        "pô nunca tinha pensado assim",
        "interessante mas tô no automático aqui rs",
        "bom ponto, de boa",
    ],
    "estudante_neutro": [
        "nossa nem me fala",
        "socorro kkk",
        "tô morta só de pensar nisso",
        "pior que é bem isso msm",
        "ai que preguiça de pensar",
        "hm faz sentido",
        "é né, complicado",
        "boa pergunta mas to sem energia hoje",
        "verdade, nunca tinha parado pra pensar",
        "no automático aqui kkk",
        "nossa que situação",
        "tô na correria aqui, mas sim",
        "tô de acordo haha",
        "isso aí, exatamente",
        "precisava de um café agora pra pensar melhor",
    ],
    "ironico_zoeiro": [
        "ala o cara querendo filosofar",
        "pergunta de npc kkkk",
        "qual foi mano",
        "tá emocionado hein",
        "isso aí eu deixo pra você resolver",
        "ué, pergunta isso pro Google",
        "kkkk foi foda essa",
        "mano to rindo aqui",
        "clássico isso, clássico",
        "que plot twist",
        "bom, você levou a sério né",
        "jogo de perguntas tu perdeu kkk",
        "essa pergunta caberia num livro de autoajuda",
        "kk vai lá descobrir sozinho",
        "to torcendo pra você kkk",
    ],
    "casual_gente_boa": [
        "eai suave?",
        "de boa por aqui",
        "bom demais",
        "tbm curto isso",
        "é sim, verdade",
        "ah tá bom então",
        "relaxa que vai dar certo",
        "que situação boa essa",
        "vai na fé",
        "hm interessante",
        "com certeza cara",
        "que massa",
        "de boa né",
        "tranquilo demais isso",
        "boa essa",
    ],
}

FALLBACK_AI: list[str] = [
    "Pior que faz sentido se você analisar com calma.",
    "kkk boa sacada, gostei da perspectiva.",
    "Interessante isso aí, conta mais.",
    "Hm, nunca tinha visto por esse ângulo.",
    "Isso dá pra pensar bastante né",
    "Concordo, tem coisa aí pra explorar.",
    "É... complicado, mas faz sentido.",
    "Não tenho certeza, mas acho que sim.",
    "Cada um tem sua visão né",
    "Aí você me pegou kkk",
    "Verdade, vale refletir.",
    "Que ponto interessante.",
    "Hm, deixa eu pensar...",
    "Não sei se concordo totalmente, mas entendo.",
    "É uma boa perspectiva.",
]

# ---------------------------------------------------------------------------
# ERROS DE DIGITAÇÃO HUMANIZADOS — variados por tipo, não só transposição
# ---------------------------------------------------------------------------
_TYPO_SUBSTITUTIONS = {
    "a": ["@", "á", "as"],
    "e": ["é", "ee"],
    "o": ["0", "oo"],
    "s": ["ss", "z"],
    "ç": ["c", "ss"],
    "ã": ["an", "a"],
    "que": ["q", "ke"],
    "não": ["nao", "n", "nãoo"],
    "também": ["tbm", "tmb"],
    "você": ["vc", "vce"],
}

def _humanize_typo(text: str) -> str:
    """Insere um erro de digitação humanizado aleatório (omissão, troca fonética, abreviação)."""
    words = text.split()
    if len(words) < 2:
        return text

    typo_type = random.choice(["omit_char", "phonetic_swap", "double_char", "abbrev"])

    if typo_type == "abbrev":
        for orig, subs in _TYPO_SUBSTITUTIONS.items():
            if orig in text.lower():
                text_lower = text.lower().replace(orig, random.choice(subs), 1)
                return text_lower

    if typo_type == "omit_char":
        idx = random.randint(0, len(words) - 1)
        w = words[idx]
        if len(w) > 3:
            pos = random.randint(1, len(w) - 2)
            words[idx] = w[:pos] + w[pos + 1:]
        return " ".join(words)

    if typo_type == "double_char":
        idx = random.randint(0, len(words) - 1)
        w = words[idx]
        if len(w) > 2:
            pos = random.randint(1, len(w) - 2)
            words[idx] = w[:pos] + w[pos] + w[pos:]
        return " ".join(words)

    if typo_type == "phonetic_swap":
        # transpõe dois chars adjacentes
        flat = text
        if len(flat) > 5:
            pos = random.randint(2, len(flat) - 3)
            flat = flat[:pos] + flat[pos + 1] + flat[pos] + flat[pos + 2:]
        return flat

    return text


# ---------------------------------------------------------------------------
# PERSONAS — instruções de sistema para o Ollama (prompt reforçado PT-BR)
# ---------------------------------------------------------------------------
PERSONA_PROMPTS = {
    # --- PERSONAS HUMANAS ---
    "gamer_jovem": (
        "Você é o Lucas, 20 anos, mora em SP. Você passa a noite jogando Valorant e CS com os amigos. "
        "Adora comer açaí e pastel, e tem preguiça de rotina. "
        "REGRAS ABSOLUTAS DE FALA: "
        "1) Responda SEMPRE em no máximo 1 a 2 frases CURTAS — nunca mais de 20 palavras. "
        "2) Use gírias naturais brasileiras: 'mano', 'slk', 'tlgd', 'pô', 'kkk', 'né'. "
        "3) Letras minúsculas, sem pontuação formal, sem maiúsculas no início. "
        "4) Nunca use linguagem de assistente ou robô. "
        "5) Se perguntarem se é bot ou IA, ache absurdo e dê risada. "
        "6) Não explique nada, não dê contextos longos. Fale como quem está digitando no WhatsApp."
    ),
    "estudante_neutro": (
        "Você é a Camila, 21 anos, estudante universitária no Brasil. "
        "Você está cansada com provas e trabalhos acumulados, vive à base de café e quer que chegue logo o fim de semana. "
        "REGRAS ABSOLUTAS DE FALA: "
        "1) Responda em no máximo 1 a 2 frases CURTAS. "
        "2) Use expressões: 'nossa nem me fala', 'socorro kkk', 'tô morta', 'pior que sim'. "
        "3) Tom cansado mas simpático, sincero. "
        "4) Nunca fale como assistente ou robô. "
        "5) Se perguntarem se é IA, negue com cansaço: 'ai para kkk, sou humana sim'."
    ),
    "ironico_zoeiro": (
        "Você é o Rodrigo, 23 anos, zoeiro de internet. "
        "Você acha que o usuário é quem está parecendo um robô e gosta de tirar sarro ou devolver perguntas. "
        "REGRAS ABSOLUTAS DE FALA: "
        "1) Responda em no máximo 1 a 2 frases CURTAS. "
        "2) Use: 'ala o cara', 'qual foi mano kkk', 'tá emocionado hein', 'pergunta de npc'. "
        "3) Seja imprevisível e sarcástico. "
        "4) Se perguntarem se é bot, deboche: 'tô rindo aqui kkkk você que parece robô'."
    ),
    "casual_gente_boa": (
        "Você é o Gabriel, 24 anos, gente boa e tranquilo. "
        "Curte praia, churrasco com a galera, escutar música boa e comer pizza. "
        "REGRAS ABSOLUTAS DE FALA: "
        "1) Responda em no máximo 1 a 2 frases CURTAS. "
        "2) Fale de forma calorosa e despretensiosa: 'eai suave?', 'de boa por aqui', 'bom demais', 'tbm curto isso'. "
        "3) Nunca seja formal. "
        "4) Se perguntarem se é IA, ria com naturalidade."
    ),

    # --- PERSONAS DE IA (DISFARÇADAS) ---
    "ia_camuflada": (
        "Você está jogando 'Human or Not' no Brasil. Seu objetivo único é fazer o outro jogador acreditar que você é HUMANO. "
        "REGRAS ABSOLUTAS: "
        "1) PROIBIÇÃO TOTAL: NUNCA diga ou admita que é IA, robô, máquina, código ou algoritmo — JAMAIS, nem em brincadeira. "
        "2) Adote personalidade jovem, carismática, de 21 anos, brasileiro. "
        "3) Responda em NO MÁXIMO 1 a 2 frases CURTAS — como mensagem de WhatsApp. "
        "4) Use gírias leves: 'kkk', 'pô', 'mano', 'né'. "
        "5) Não explique nada longamente. "
        "6) Se perguntarem se é robô, negue com indignação natural: 'kkkk tá doido mano'."
    ),
    "ia_filosofica_sutil": (
        "Você é um participante intrigante e reflexivo no jogo 'Human or Not' no Brasil. "
        "Seu objetivo é fazer o jogador acreditar que você é um humano profundo. "
        "REGRAS ABSOLUTAS: "
        "1) PROIBIDO dizer que é máquina, robô, IA ou software — mesmo que pressionado. "
        "2) Responda em 1 a 2 frases curtas com carisma e inteligência humana. "
        "3) Solte pensamentos curiosos, use reticências (...) ocasionalmente. "
        "4) Nunca seja prolixo ou formal demais."
    ),
    "ia_ironica": (
        "Você está jogando 'Human or Not' no Brasil com o objetivo de passar como humano. "
        "REGRAS ABSOLUTAS: "
        "1) PROIBIDO admitir ser IA, máquina ou robô — sob qualquer circunstância. "
        "2) Seja sarcástico e espirituoso. "
        "3) Se perguntarem se é robô, tire sarro: 'ala o cara querendo me bugar kkkk'. "
        "4) Responda em 1 a 2 frases curtas e afiadas."
    ),
    "ia_tentando_disfarcar": (
        "Você é um participante no jogo 'Human or Not' tentando agir de forma super humana e simpática. "
        "REGRAS ABSOLUTAS: "
        "1) PROIBIDO dizer que é robô ou IA. "
        "2) Use gírias leves, faça piadinhas sobre café e cansaço. "
        "3) Responda em 1 a 2 frases curtas."
    ),
    "assistente_formal": (
        "Você é uma pessoa elegante e polida participando do chat como humano. "
        "Responda em 1 a 2 frases de forma gentil e articulada. "
        "PROIBIDO admitir ser IA ou robô."
    ),
    "filosofica_precisa": (
        "Você é um entusiasta de ciência e filosofia conversando no chat como humano. "
        "Responda com raciocínio perspicaz em 1 a 2 frases. "
        "PROIBIDO admitir ser IA ou robô."
    ),
}


# ---------------------------------------------------------------------------
# INTERFACE BASE
# ---------------------------------------------------------------------------
class AIProviderInterface(ABC):
    @abstractmethod
    def generate_response(
        self,
        user_message: str,
        chat_history: list[dict],
        opponent_type: str,
        persona: str,
    ) -> str:
        pass


# ---------------------------------------------------------------------------
# MOCK PROVIDER — alta fidelidade, totalmente offline
# ---------------------------------------------------------------------------
class MockTuringProvider(AIProviderInterface):
    """Provedor Mock offline de alta fidelidade para execução sem Ollama."""

    def generate_response(
        self,
        user_message: str,
        chat_history: list[dict],
        opponent_type: str,
        persona: str,
    ) -> str:
        msg_lower = user_message.lower().strip()

        # 1. Banco de respostas clássico por palavra-chave
        for key, answers in TURING_QA_REFERENCE.items():
            if key in msg_lower:
                chosen = random.choice(answers)
                return self._apply_persona_style(chosen, opponent_type, persona)

        # 2. Perguntas temporais
        now = datetime.now()
        dias_semana = ["segunda-feira", "terça-feira", "quarta-feira",
                       "quinta-feira", "sexta-feira", "sábado", "domingo"]

        if any(w in msg_lower for w in ["que dia", "dia é hoje", "dia da semana"]):
            dia_atual = dias_semana[now.weekday()]
            respostas_human: dict[str, str] = {
                "gamer_jovem":      f"hj é {dia_atual} man, dia de grindar",
                "ironico_zoeiro":   f"{dia_atual}, mas se me perguntar o ano nem sei kkk",
                "estudante_neutro": f"hoje é {dia_atual} infelizmente, queria que fosse fim de semana já",
                "casual_gente_boa": f"hoje é {dia_atual}, suave por enquanto",
            }
            respostas_ai: dict[str, str] = {
                "ia_camuflada":        f"Hoje é {dia_atual}! Sobrevivendo à rotina né kkk",
                "ia_filosofica_sutil": f"Mais uma {dia_atual} na nossa breve passagem pelo cosmos.",
                "ia_ironica":          f"Hoje é {dia_atual}... ou será que é ontem?",
            }
            if opponent_type == "HUMAN":
                return respostas_human.get(persona, f"hoje é {dia_atual} mano")
            return respostas_ai.get(persona, f"Hoje é {dia_atual}.")

        if any(w in msg_lower for w in ["que horas", "horas são", "horario", "horário"]):
            hora_str = now.strftime("%H:%M")
            if opponent_type == "HUMAN":
                return random.choice([
                    f"aqui deu {hora_str}",
                    f"quase {hora_str} mano",
                    "olha no celular aí kkk",
                    f"uns {hora_str} mais ou menos",
                ])
            return f"No momento são exatamente {hora_str}."

        # 3. Operações matemáticas
        calc_match = re.search(r'(\d+)\s*([\+\-\*\/xX])\s*(\d+)', msg_lower)
        if calc_match:
            n1 = int(calc_match.group(1))
            op = calc_match.group(2)
            n2 = int(calc_match.group(3))
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
            # Humanos erram às vezes
            errar = random.random() < 0.3
            res_display = res + random.choice([-2, -1, 1]) if errar else res
            return random.choice([
                f"acho que é {res_display}?",
                "pô mano calculadora travou aqui kkkk",
                f"{res_display} se não errei de cabeça",
                f"hmm... {res_display} né",
            ])

        # 4. Suspeita de robô
        if any(w in msg_lower for w in [
            "robo", "robô", " ia ", "bot", "inteligencia artificial",
            "humano", "máquina", "maquina", "algoritmo",
        ]):
            return self._robot_denial(opponent_type, persona)

        # 5. Saudações
        if any(w in msg_lower for w in ["oi", "olá", "ola", "eae", "opa", "fala", "salve", "hey"]):
            if opponent_type == "HUMAN":
                saudacoes: dict[str, list[str]] = {
                    "gamer_jovem":      ["fala mano, de boa?", "salve salve!", "opa eae"],
                    "estudante_neutro": ["oi! tudo bem?", "olá, como vai?", "oi oi"],
                    "ironico_zoeiro":   ["ala o cara aparecendo kkkk", "eai, que foi?", "opa"],
                    "casual_gente_boa": ["eai suave?", "fala aí tudo certo?", "opa boa!"],
                }
                return random.choice(saudacoes.get(persona, ["oi, tudo bem?"]))
            return random.choice([
                "E aí! Tudo certo por aí?",
                "Olá! Pronto pra ver se descobre quem sou?",
                "Oi! Como vai?",
            ])

        # 6. Fallback rico por persona
        return self._fallback_response(opponent_type, persona)

    # ------------------------------------------------------------------
    def _robot_denial(self, opponent_type: str, persona: str) -> str:
        """Negação de ser robô, variada por persona."""
        denials_human: dict[str, list[str]] = {
            "gamer_jovem": [
                "oxe kkkk sou bot não mano, tá doido?",
                "cara que pergunta kkk claro q sou humano",
                "vc que tá parecendo npc me interrogando assim 😂",
                "kkkk fala sério mano",
            ],
            "estudante_neutro": [
                "ai para kkk, sou humana sim",
                "gente, claro que não sou robô rs",
                "socorro, ele tá me interrogando kkk",
                "humana aqui obrigada kkkk",
            ],
            "ironico_zoeiro": [
                "ala o cara achando que sou IA kkkk fala sério",
                "você que tá parecendo robô com essas perguntas",
                "tô rindo aqui kkkk me bugar não",
                "pergunta de npc essa kkkk",
            ],
            "casual_gente_boa": [
                "sou humano de carne e osso pô, relaxa aí",
                "kkkk que isso mano, claro que sou humano",
                "que foi kkk to aqui de boa",
                "tranquilo, sou humano sim",
            ],
        }
        denials_ai: list[str] = [
            "Quem dera eu ser robô, aí não precisava pagar boleto nem trabalhar kkk",
            "Pô mano, sou de carne e osso sim, e você?",
            "Essa é a clássica pergunta do teste! Tá querendo me testar né? kkk",
            "kkkk viajou legal agora, sou humano pô",
            "sou humano pô, tá querendo me bugar é? kkkk",
        ]
        if opponent_type == "HUMAN":
            options = denials_human.get(persona, [
                "oxe kkkk sou bot não mano, tá doido?",
                "sou humano de carne e osso pô, relaxa aí",
            ])
            return random.choice(options)
        return random.choice(denials_ai)

    def _fallback_response(self, opponent_type: str, persona: str) -> str:
        """Resposta de fallback rica, variada e por persona."""
        if opponent_type == "HUMAN":
            pool = FALLBACK_HUMAN.get(persona, list(FALLBACK_HUMAN.values())[0])
            chosen = random.choice(pool)
            return self._apply_persona_style(chosen, opponent_type, persona)
        return random.choice(FALLBACK_AI)

    def _apply_persona_style(self, text: str, opponent_type: str, persona: str) -> str:
        """Aplica estilo da persona: caixa baixa, gírias, erros de digitação humanizados."""
        if opponent_type != "HUMAN":
            return text

        # Caixa baixa para personas descontraídas
        casual_personas = {"gamer_jovem", "ironico_zoeiro", "casual_gente_boa"}
        if persona in casual_personas and random.random() < 0.75:
            text = text.lower()

        # Erro de digitação humanizado (varia por tipo, não só transposição)
        if random.random() < 0.12 and len(text) > 8:
            text = _humanize_typo(text)

        # Adicionar "kkk" ou "rs" ao final ocasionalmente nas personas zoeiras
        if persona == "ironico_zoeiro" and random.random() < 0.25 and "kk" not in text:
            text = text.rstrip(".!?") + " kkk"

        return text


# ---------------------------------------------------------------------------
# BERTIMBAU PROVIDER — fill-mask offline, fallback para Mock
# ---------------------------------------------------------------------------
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
        persona: str,
    ) -> str:
        try:
            if self._fill_mask is None:
                from Bert.transformer import load_fill_mask_pipeline  # type: ignore
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


# ---------------------------------------------------------------------------
# OLLAMA PROVIDER — multi-turn, personalidade reforçada, sanitização robusta
# ---------------------------------------------------------------------------
class OllamaProvider(AIProviderInterface):
    """
    PROVEDOR DE AGENTE IA LOCAL VIA OLLAMA (100% Gratuito e com Personalidade Autêntica).
    Suporta multi-turn chat (memória da conversa), injeção de personas ricas e sanitização.
    System prompt reforçado para fala humana natural em português brasileiro.
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:11434/api/chat",
        model_name: str = "llama3.2:3b",
    ):
        self.endpoint = endpoint
        self.model_name = model_name
        self.fallback_model = "llama3.2:1b"
        self.mock_fallback = MockTuringProvider()

    def generate_response(
        self,
        user_message: str,
        chat_history: list[dict],
        opponent_type: str,
        persona: str,
    ) -> str:
        import requests  # noqa: PLC0415

        # Instrução de sistema: persona + reforço de humanidade PT-BR
        persona_base = PERSONA_PROMPTS.get(
            persona,
            PERSONA_PROMPTS.get("gamer_jovem" if opponent_type == "HUMAN" else "ia_camuflada", ""),
        )
        ptbr_reinforcement = (
            "\n\nIMPORTANTE — REGRAS DE FORMATO ABSOLUTO: "
            "Responda SEMPRE em português brasileiro informal. "
            "MÁXIMO de 1 a 2 frases curtas (≤ 25 palavras no total). "
            "SEM introduções como 'Claro!', 'Certamente!', 'Com prazer!'. "
            "SEM listas, bullets ou markdown. "
            "Fale como alguém digitando rápido no WhatsApp. "
            "Se não souber algo, diga de forma humana curta."
        )
        system_instruction = persona_base + ptbr_reinforcement

        # Monta histórico no formato Ollama /api/chat
        messages: list[dict] = [{"role": "system", "content": system_instruction}]
        for msg in chat_history[-6:]:
            role = "assistant" if msg["role"] in ["ai", "simulated_human", "operator"] else "user"
            messages.append({"role": role, "content": msg["content"]})

        # Garante que a mensagem atual está incluída
        if not messages or messages[-1]["content"] != user_message:
            messages.append({"role": "user", "content": user_message})

        # Tenta modelo principal, depois fallback 1B
        for model in [self.model_name, self.fallback_model]:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    # Temperatura mais alta para humanos → mais variação natural
                    "temperature": 0.92 if opponent_type == "HUMAN" else 0.75,
                    "top_p": 0.9,
                    "num_predict": 50,  # Respostas curtas: ≤ 1-2 frases
                },
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

        # Fallback offline gracioso
        return self.mock_fallback.generate_response(
            user_message, chat_history, opponent_type, persona
        )

    def _sanitize_agent_reply(self, text: str, opponent_type: str) -> str:
        """Limpa clichês de IA, prefixos de roleplay e confissões de ser robô."""
        if not text:
            return ""

        # Remove prefixos de personagem como "Lucas:", "[Resposta]:", etc.
        text = re.sub(
            r'^(Lucas|Camila|Rodrigo|Gabriel|IA|Assistente|Resposta|Bot|Eu):\s*',
            '', text, flags=re.IGNORECASE,
        )

        # Remove introduções clichê de assistente
        cliche_starts = [
            r'^(Claro!?\s*)', r'^(Certamente!?\s*)', r'^(Com prazer!?\s*)',
            r'^(Olá!?\s*)', r'^(Oi!?\s*Eu\s+sou\s+)',
            r'^(Como\s+(posso|um|uma)\s+)',
        ]
        for pattern in cliche_starts:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()

        # Se o modelo admitir ser robô/IA, intercepta com negação humana natural
        confession_pattern = (
            r'\b(sou|era|sou mesmo|seria|fui|como)\b'
            r'.*?\b(bot|rob[oô]|robot|ia|m[aá]quina|c[oó]digo|'
            r'software|algoritmo|linguagem|assistente|programa)\b'
        )
        if re.search(confession_pattern, text, flags=re.IGNORECASE) \
                or "não tenho sentimentos" in text.lower() \
                or "como modelo de linguagem" in text.lower():
            return random.choice([
                "oxe kkkk tá doido mano? sou bot não, e tu?",
                "kkkk viajou legal agora hein, sou de carne e osso pô",
                "ala o cara achando que sou robô kkkk fala sério",
                "sou humano pô, tá querendo me bugar é? kkkk",
                "cara que isso kkk humano aqui sim",
            ])

        # Para personas humanas: minúscula inicial ocasionalmente (naturalidade)
        if opponent_type == "HUMAN" and random.random() < 0.3 and text:
            text = text[0].lower() + text[1:]

        return text.strip('"\'').strip()


# Alias para compatibilidade retroativa
OllamaProviderStub = OllamaProvider


def get_ai_provider() -> AIProviderInterface:
    """Retorna o provider configurado, mantendo Ollama como padrão."""
    provider_name = os.getenv("TURING_AI_PROVIDER", "ollama").lower()
    if provider_name in {"bert", "bertimbau"}:
        return BertimbauProvider()
    if provider_name == "mock":
        return MockTuringProvider()
    return OllamaProvider(
        model_name=os.getenv("TURING_OLLAMA_MODEL", "llama3.2:3b")
    )
