"""
cli_game.py
Versão para linha de comando (Terminal) do Minijogo Teste de Turing.
Permite jogar diretamente no terminal com efeito typewriter e persistência opcional no banco SQLite.
"""

import time
import sys
from core.database import init_db
from bot_engine import TuringOpponent
from services.auth_service import AuthService
from services.game_service import GameService
from core.config import ROLE_USUARIO

def typewriter_print(text: str, delay: float = 0.015):
    """Exibe o texto no terminal com efeito visual de digitação fluida."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def main():
    # Inicializa banco se necessário
    init_db()
    game_service = GameService()

    print("=" * 65)
    print("      🎮 TESTE DE TURING: HUMAN OR NOT? (TERMINAL) 🤖 vs 👤")
    print("=" * 65)
    print("1. Você conversará com um interlocutor misterioso por até 5 mensagens.")
    print("2. Ao final, vote se você estava falando com uma IA ou com um Humano.")
    print("=" * 65)

    current_user = None
    print("\n[1] Jogar como Convidado (modo rápido offline)")
    print("[2] Entrar com Usuário (salvar histórico no banco)")
    choice = input("Escolha uma opção (1 ou 2): ").strip()

    if choice == "2":
        username = input("Usuário: ").strip()
        password = input("Senha: ").strip()
        user, err = AuthService.authenticate(username, password)
        if user:
            current_user = user
            print(f"Bem-vindo de volta, {user.full_name}!")
        else:
            print(f"Falha de autenticação ({err}). Continuando como Convidado...")

    score_games = 0
    score_wins = 0

    while True:
        session = None
        opponent = None

        if current_user:
            session = game_service.start_new_game(current_user.id)
            opponent_type = session.opponent_type
        else:
            opponent = TuringOpponent()
            opponent_type = opponent.opponent_type

        print("\n" + "-" * 65)
        print("[!] Novo interlocutor conectado! Inicie a conversa.")
        print("-" * 65)

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
            delay = 1.0 if opponent_type == "HUMAN" else 0.6
            time.sleep(delay)
            print(" " * 35, end="\r")  # Limpa o aviso

            if current_user and session:
                reply, _ = game_service.send_user_message(session.id, current_user.username, user_msg)
            else:
                reply = opponent.get_response(user_msg)

            sys.stdout.write("Interlocutor: ")
            sys.stdout.flush()
            typewriter_print(reply)

        print("\n" + "=" * 65)
        print("🛑 LIMITE DE 5 MENSAGENS ATINGIDO! HORA DO VOTO:")
        print("[1] 🤖 Inteligência Artificial (IA)")
        print("[2] 👤 Humano")
        print("=" * 65)

        vote_choice = ""
        while vote_choice not in ["1", "2"]:
            vote_choice = input("Qual o seu palpite? (1 ou 2): ").strip()

        user_voted = "AI" if vote_choice == "1" else "HUMAN"

        if current_user and session:
            is_correct, actual, _ = game_service.submit_vote(session.id, user_voted)
        else:
            actual = opponent_type
            is_correct = (user_voted == actual)

        score_games += 1
        if is_correct:
            score_wins += 1

        print("\n" + "-" * 45)
        if is_correct:
            print("🎉 PARABÉNS! VOCÊ ACERTOU!")
        else:
            print("❌ VOCÊ FOI ENGANADO!")

        print(f"Seu palpite: {'🤖 IA' if user_voted == 'AI' else '👤 Humano'}")
        print(f"A verdade  : Na realidade era {'🤖 IA' if actual == 'AI' else '👤 Humano'}!")
        print(f"Placar     : {score_wins}/{score_games} vitórias ({(score_wins/score_games)*100:.0f}%)")
        print("-" * 45)

        jogar_novamente = input("\nDeseja jogar outra rodada? (s/n): ").strip().lower()
        if jogar_novamente != 's':
            print("\nObrigado por jogar o Teste de Turing! Até a próxima.")
            break

if __name__ == "__main__":
    main()
