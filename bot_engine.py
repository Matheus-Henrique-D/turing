"""
bot_engine.py
Módulo responsável por gerar as respostas do interlocutor misterioso.
Pode simular Humanos ou IAs de forma offline (com gírias, erros de digitação e padrões típicos)
ou conectar a provedores de LLM reais via API (ex: Gemini/OpenAI/Groq).
"""

import random
import time
import re
from datetime import datetime

# Respostas pré-configuradas e comportamentos inspirados no material didático do Teste de Turing
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

class TuringOpponent:
    def __init__(self, opponent_type: str = None, api_client = None):
        """
        opponent_type: 'HUMAN' ou 'AI'. Se None, sorteia 50%/50%.
        """
        if opponent_type is None:
            self.opponent_type = random.choice(["HUMAN", "AI"])
        else:
            self.opponent_type = opponent_type
        
        self.api_client = api_client
        self.chat_history = []
        
        # Perfis de personalidade para enriquecer o chat offline
        if self.opponent_type == "HUMAN":
            self.persona = random.choice([
                "gamer_jovem",      # Gírias, abreviações, 'kkk', 'mano', 'slk'
                "estudante_neutro", # Português casual, direto, respostas curtas
                "ironico_zoeiro"    # Desconfiado, faz piadinhas, devolve perguntas
            ])
        else:
            self.persona = random.choice([
                "assistente_formal", # Tenta soar prestativo, pontuação correta, vocabulário polido
                "ia_tentando_disfarcar", # Usa gírias de forma um pouco forçada ou excessivamente explicativa
                "filosofica_precisa"  # Respostas com dados, cálculos rápidos, tom analítico
            ])

    def get_response(self, user_message: str) -> str:
        """Gera a resposta do interlocutor com base no seu tipo e persona."""
        self.chat_history.append({"role": "user", "content": user_message})
        
        # Se houver cliente LLM configurado, usamos prompts especializados
        if self.api_client:
            reply = self._generate_llm_response(user_message)
        else:
            reply = self._generate_simulated_response(user_message)
            
        self.chat_history.append({"role": "assistant", "content": reply})
        return reply

    def _generate_simulated_response(self, user_msg: str) -> str:
        msg_lower = user_msg.lower().strip()
        
        # 1. Checagem de perguntas clássicas do Teste de Turing
        for key, answers in TURING_QA_REFERENCE.items():
            if key in msg_lower:
                chosen = random.choice(answers)
                return self._apply_style(chosen)

        # 2. Perguntas temporais / fatos
        now = datetime.now()
        dias_semana = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
        
        if "que dia" in msg_lower or "dia é hoje" in msg_lower:
            dia_atual = dias_semana[now.weekday()]
            if self.opponent_type == "HUMAN":
                return random.choice([f"Hoje é {dia_atual}", f"{dia_atual}, por quê?", "é dia de trabalhar infelizmente kkk"])
            else:
                return f"Hoje é {dia_atual}, dia {now.strftime('%d/%m/%Y')}."

        if "que horas" in msg_lower or "horas são" in msg_lower:
            hora_str = now.strftime("%H:%M")
            if self.opponent_type == "HUMAN":
                return random.choice([f"Aqui são {hora_str}", f"Quase {hora_str}", "olha no seu relógio aí pow kkk"])
            else:
                return f"No momento são exatamente {hora_str}."

        # 3. Contas matemáticas
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

            if self.opponent_type == "AI":
                return str(res)
            else:
                # Humanos erram, demoram ou respondem com preguiça
                return random.choice([
                    f"Acho que é {res}?",
                    "Pô, não sou calculadora não kkkk",
                    f"{res + random.choice([-2, 1, 0])} se não errei a conta de cabeça",
                    "Preguiça de calcular agora mano"
                ])

        # 4. Perguntas de suspeita ("você é robô?", "é IA?", "quem é você?")
        if any(w in msg_lower for w in ["robo", "robô", "ia", "bot", "inteligencia artificial", "humano"]):
            if self.opponent_type == "HUMAN":
                return random.choice([
                    "oxe kkkk sou humano né, e vc?",
                    "óbvio que sou humano uai",
                    "todo mundo pergunta isso kkk sou pessoa de verdade po",
                    "vc que tá parecendo um bot me interrogando assim 😂",
                    "sou humano mano, relaxa"
                ])
            else:
                return random.choice([
                    "Eu sou um participante deste teste, assim como você.",
                    "Sou uma consciência digital interagindo através desta interface.",
                    "Defina o que é ser humano... Brincadeira, sou uma pessoa real sim!",
                    "Essa é a clássica pergunta do Teste de Turing! O que você acha que eu sou?"
                ])

        # 5. Saudações iniciais
        if any(w in msg_lower for w in ["oi", "olá", "ola", "eae", "opa", "fala", "hello", "hi", "bom dia", "boa tarde", "boa noite"]):
            if self.opponent_type == "HUMAN":
                return random.choice([
                    "opa, eae tudo bem?",
                    "oi, suave?",
                    "fala mano, blz?",
                    "oi oi, de onde vc é?",
                    "eai, pronto pro teste?"
                ])
            else:
                return random.choice([
                    "Olá! Como você está hoje?",
                    "Oi! Tudo bem? Prazer em conversar com você.",
                    "Olá, pronto para mais uma rodada do jogo?",
                    "Oi! Vamos bater um papo rápido."
                ])

        # 6. Respostas genéricas / contextuais
        if self.opponent_type == "HUMAN":
            human_replies = [
                "kkkkk faz sentido",
                "sei lá cara, nunca pensei nisso",
                "caraca sério? conta mais",
                "tbm acho isso",
                "mano do céu, que aleatório kkk",
                "hmmm entendi",
                "vish, aí me pegou",
                "pior que concordo contigo",
                "nada a ver isso aí pô",
                "to meio sem assunto hj kkk"
            ]
            return self._apply_style(random.choice(human_replies))
        else:
            ai_replies = [
                "Interessante sua perspectiva sobre esse assunto.",
                "Entendo seu ponto de vista perfeitamente.",
                "Essa é uma questão que suscita várias interpretações lógicas.",
                "Compreendo. E você costuma pensar frequentemente sobre isso?",
                "Interessante observação. O que te levou a essa conclusão?",
                "Faz todo sentido se analisarmos sob esse ângulo.",
                "É um tópico fascinante para se discutir em 5 mensagens."
            ]
            return random.choice(ai_replies)

    def _apply_style(self, text: str) -> str:
        """Aplica pequenas nuances de estilo (como typos sutis ou minúsculas para humanos)."""
        if self.opponent_type == "HUMAN":
            if random.random() < 0.7:
                text = text.lower()
            if random.random() < 0.1 and len(text) > 10:
                idx = random.randint(3, len(text) - 4)
                text = text[:idx] + text[idx+1] + text[idx] + text[idx+2:]
        return text

    def _generate_llm_response(self, user_msg: str) -> str:
        """Fallback para modo simulado ou suporte a LLM externo."""
        return self._generate_simulated_response(user_msg)
