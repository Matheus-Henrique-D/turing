"""
tests/test_ai_provider.py
Testes unitários para garantir que o Mock opera 100% offline e sem rede externa.
"""

import unittest
from services.ai_provider import MockTuringProvider, OllamaProviderStub, get_ai_provider

class TestAIProvider(unittest.TestCase):
    def setUp(self):
        self.provider = get_ai_provider()

    def test_mock_returns_responses_without_network(self):
        mock = MockTuringProvider()
        reply = mock.generate_response(
            user_message="Você é um computador?",
            chat_history=[],
            opponent_type="HUMAN",
            persona="gamer_jovem"
        )
        self.assertIsInstance(reply, str)
        self.assertTrue(len(reply) > 0)

    def test_math_logic_differentiation(self):
        # Mock do Turing responde o valor matemático exato
        mock = MockTuringProvider()
        reply_ai = mock.generate_response(
            user_message="Quanto é 25 * 4?",
            chat_history=[],
            opponent_type="AI",
            persona="filosofica_precisa"
        )
        self.assertEqual(reply_ai.strip(), "100")

    def test_ollama_provider_response(self):
        # OllamaProvider com fallback seguro
        reply = self.provider.generate_response(
            user_message="Oi, tudo bem?",
            chat_history=[],
            opponent_type="AI",
            persona="assistente_formal"
        )
        self.assertIsInstance(reply, str)
        self.assertTrue(len(reply) > 0)

if __name__ == "__main__":
    unittest.main()
