"""
cli_game.py
Versão para linha de comando (Terminal) do Minijogo Teste de Turing.
Permite jogar diretamente no terminal sem dependências adicionais além do Python.
"""

import time
import sys
from bot_engine import TuringOpponent

def typewriter_print(text: str, delay: float = 0.02):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def main():
    print("=" * 60)
    print("      🎮 TESTE DE TURING: HUMAN OR NOT? (TERMINAL) 🤖 vs 👤")
    print("=" * 60)
    print("Regras:")
    print("1. Você conversará com um interlocutor misterioso por 5 mensagens.")
    print("2. Ao final, vote se você estava falando com uma IA ou com um Humano.")
    print("=" * 60)
    
    score_games = 0
    score_wins = 0
    
    while True:
        opponent = TuringOpponent()
        print("\n[!] Novo interlocutor conectado! Inicie a conversa.")
        print("-" * 60)
        
        for turno in range(1, 6):
            print(f"\n[Turno {turno}/5]")
            try:
                user_msg = input("Você: ").strip()
                while not user_msg:
                    user_msg = input("Você (digite algo): ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nEncerrando o jogo...")
                return

            print("Interlocutor está digitando...", end="\r")
            time.sleep(1.2 if opponent.opponent_type == "HUMAN" else 0.8)
            reply = opponent.get_response(user_msg)
            print(" " * 35, end="\r")  # Limpa o aviso de digitando
            print(f"Interlocutor: {reply}")

        print("\n" + "=" * 60)
        print("🛑 LIMITE DE 5 MENSAGENS ATINGIDO! HORA DO VOTO:")
        print("[1] 🤖 Inteligência Artificial (IA)")
        print("[2] 👤 Humano")
        print("=" * 60)
        
        vote_choice = ""
        while vote_choice not in ["1", "2"]:
            vote_choice = input("Qual o seu palpite? (1 ou 2): ").strip()
            
        user_voted = "AI" if vote_choice == "1" else "HUMAN"
        actual = opponent.opponent_type
        
        score_games += 1
        print("\n" + "-" * 40)
        if user_voted == actual:
            score_wins += 1
            print(f"🎉 PARABÉNS! VOCÊ ACERTOU!")
        else:
            print(f"❌ VOCÊ ERROU!")
            
        print(f"Seu palpite: {'🤖 IA' if user_voted == 'AI' else '👤 Humano'}")
        print(f"A verdade  : Na realidade era {'🤖 IA' if actual == 'AI' else '👤 Humano'}!")
        print(f"Placar     : {score_wins}/{score_games} vitórias ({(score_wins/score_games)*100:.0f}%)")
        print("-" * 40)
        
        jogar_novamente = input("\nDeseja jogar outra rodada? (s/n): ").strip().lower()
        if jogar_novamente != 's':
            print("\nObrigado por jogar o Teste de Turing! Até a próxima.")
            break

if __name__ == "__main__":
    main()
