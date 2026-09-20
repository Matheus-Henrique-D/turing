"""
bot_engine.py
Módulo responsável por gerar as respostas do interlocutor misterioso.
Atualizado para utilizar o MockTuringProvider com suporte real a personas,
mantendo compatibilidade com execuções legadas.
"""

import random
from services.ai_provider import MockTuringProvider, OllamaProviderStub, AIProviderInterface

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
        
        # Seleção de persona com impacto comportamental real
        if self.opponent_type == "HUMAN":
            self.persona = random.choice(["gamer_jovem", "estudante_neutro", "ironico_zoeiro"])
        else:
            self.persona = random.choice(["assistente_formal", "ia_tentando_disfarcar", "filosofica_precisa"])

        # Provedor base (Mock local seguro)
        self.provider: AIProviderInterface = MockTuringProvider()

    def get_response(self, user_message: str) -> str:
        """Gera a resposta do interlocutor com base no seu tipo e persona."""
        self.chat_history.append({"role": "user", "content": user_message})
        
        reply = self.provider.generate_response(
            user_message=user_message,
            chat_history=self.chat_history,
            opponent_type=self.opponent_type,
            persona=self.persona
        )
            
        self.chat_history.append({"role": "assistant", "content": reply})
        return reply
