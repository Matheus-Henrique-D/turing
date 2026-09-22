from pathlib import Path
from typing import Any


MODEL_ID = "neuralmind/bert-base-portuguese-cased"
LOCAL_MODEL_DIR = Path(__file__).resolve().parent / "Arquivos modelo nlp"


def has_local_weights() -> bool:
    """Indica se o diretório local tem pesos, e não apenas o tokenizer."""
    return any((LOCAL_MODEL_DIR / filename).exists() for filename in (
        "pytorch_model.bin",
        "model.safetensors",
        "tf_model.h5",
    ))


def load_fill_mask_pipeline() -> Any:
    """Carrega o BERTimbau sob demanda, usando pesos locais quando existirem."""
    import torch
    from transformers import AutoModelForMaskedLM, AutoTokenizer, pipeline

    model_source = str(LOCAL_MODEL_DIR) if has_local_weights() else MODEL_ID
    tokenizer = AutoTokenizer.from_pretrained(model_source, do_lower_case=False)
    model = AutoModelForMaskedLM.from_pretrained(model_source)
    device = 0 if torch.cuda.is_available() else -1

    return pipeline("fill-mask", model=model, tokenizer=tokenizer, device=device)


def predict_masked_tokens(text: str, top_k: int = 3) -> list[dict[str, Any]]:
    """Retorna previsões do BERTimbau sem manter o modelo carregado na importação."""
    fill_mask = load_fill_mask_pipeline()
    return fill_mask(text, top_k=top_k)


def main():
    fill_mask = load_fill_mask_pipeline()
    results = fill_mask("A inteligência artificial ajuda a compreender a [MASK] portuguesa.")
    for result in results[:5]:
        print(f"{result['token_str']}: {result['score']:.4f} - {result['sequence']}")


if __name__ == "__main__":
    main()