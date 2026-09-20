from pathlib import Path

import torch
from transformers import AutoModelForMaskedLM, AutoTokenizer, pipeline


MODEL_ID = "neuralmind/bert-base-portuguese-cased"
LOCAL_MODEL_DIR = Path(__file__).resolve().parent / "Arquivos modelo nlp"


def load_fill_mask_pipeline():
    """Carrega o BERTimbau localmente quando os artefatos estiverem disponíveis."""
    model_source = str(LOCAL_MODEL_DIR) if LOCAL_MODEL_DIR.exists() else MODEL_ID
    tokenizer = AutoTokenizer.from_pretrained(model_source, do_lower_case=False)
    model = AutoModelForMaskedLM.from_pretrained(model_source)
    device = 0 if torch.cuda.is_available() else -1

    return pipeline(
        task="fill-mask",
        model=model,
        tokenizer=tokenizer,
        device=device,
    )


def main():
    fill_mask = load_fill_mask_pipeline()
    results = fill_mask("A inteligência artificial ajuda a compreender a [MASK] portuguesa.")
    for result in results[:5]:
        print(f"{result['token_str']}: {result['score']:.4f} - {result['sequence']}")


if __name__ == "__main__":
    main()