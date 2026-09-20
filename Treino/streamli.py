import pickle
from pathlib import Path
import streamlit_authenticator as stauth

nome= ["Bruce Wayne", "Clark Kent"]
usernames = ["Bwayne", "Ckent"]
passwords= ["bigbat10", "Manoftomorrow001"]

senha_hash= stauth.Hasher(passwords).generate()

caminho = Path(__file__).parent / "Os_hash_pw.pkl"
with caminho.open("wb") as file:
    pickle.dump(senha_hash, file)