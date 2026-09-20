from pathlib import Path

from huggingface_hub import snapshot_download


MODEL_ID = "neuralmind/bert-base-portuguese-cased"
LOCAL_MODEL_DIR = Path(__file__).resolve().parent / "Arquivos modelo nlp"


def main():
    snapshot_download(
        repo_id=MODEL_ID,
        repo_type="model",
        local_dir=str(LOCAL_MODEL_DIR),
    )
    print(f"Modelo salvo em: {LOCAL_MODEL_DIR}")


if __name__ == "__main__":
    main()