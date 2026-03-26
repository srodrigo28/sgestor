import json
import re
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "financial_categories.json"
DEFAULT_FINANCIAL_CATEGORIES = {
    "income": ["serviço", "contrato", "salario mensal", "bico"],
    "expense": ["Operacional", "Fornecedores", "Pessoal", "Outros"],
}


def _normalize_text(value: str | None) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    return text


def _kind_key(kind: str | None) -> str:
    key = str(kind or "").strip().lower()
    if key not in {"income", "expense"}:
        raise ValueError("Tipo de categoria financeira inválido.")
    return key


def _normalize_payload(data: dict | None) -> dict:
    payload = dict(DEFAULT_FINANCIAL_CATEGORIES)
    if isinstance(data, dict):
        for kind in ("income", "expense"):
            items = data.get(kind, payload[kind])
            normalized = []
            seen = set()
            if isinstance(items, list):
                for item in items:
                    name = _normalize_text(item)
                    if not name:
                        continue
                    token = name.casefold()
                    if token in seen:
                        continue
                    seen.add(token)
                    normalized.append(name)
            payload[kind] = normalized or list(DEFAULT_FINANCIAL_CATEGORIES[kind])
    return payload


def _write_payload(payload: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_financial_categories() -> dict:
    if not CONFIG_PATH.exists():
        payload = _normalize_payload(DEFAULT_FINANCIAL_CATEGORIES)
        _write_payload(payload)
        return payload

    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        raw = DEFAULT_FINANCIAL_CATEGORIES

    payload = _normalize_payload(raw)
    if payload != raw:
        _write_payload(payload)
    return payload


def save_financial_categories(data: dict) -> dict:
    payload = _normalize_payload(data)
    _write_payload(payload)
    return payload


def list_financial_categories(kind: str) -> list[str]:
    payload = load_financial_categories()
    return list(payload[_kind_key(kind)])


def is_valid_financial_category(kind: str, name: str | None) -> bool:
    normalized = _normalize_text(name)
    if not normalized:
        return False
    return normalized.casefold() in {item.casefold() for item in list_financial_categories(kind)}


def add_financial_category(kind: str, name: str) -> tuple[bool, str]:
    key = _kind_key(kind)
    normalized = _normalize_text(name)
    if not normalized:
        return False, "Informe o nome da categoria."

    payload = load_financial_categories()
    existing = payload[key]
    if normalized.casefold() in {item.casefold() for item in existing}:
        return False, "Categoria já cadastrada."

    existing.append(normalized)
    payload[key] = sorted(existing, key=lambda item: item.casefold())
    save_financial_categories(payload)
    return True, normalized


def rename_financial_category(kind: str, current_name: str, new_name: str) -> tuple[bool, str]:
    key = _kind_key(kind)
    current = _normalize_text(current_name)
    new = _normalize_text(new_name)
    if not current or not new:
        return False, "Categoria atual e nova categoria são obrigatórias."

    payload = load_financial_categories()
    existing = payload[key]
    lower_map = {item.casefold(): item for item in existing}
    current_key = current.casefold()
    new_key = new.casefold()

    if current_key not in lower_map:
        return False, "Categoria não encontrada."
    if new_key != current_key and new_key in lower_map:
        return False, "Já existe uma categoria com esse nome."

    updated = []
    for item in existing:
        if item.casefold() == current_key:
            updated.append(new)
        else:
            updated.append(item)

    payload[key] = sorted(updated, key=lambda item: item.casefold())
    save_financial_categories(payload)
    return True, lower_map[current_key]


def delete_financial_category(kind: str, name: str) -> tuple[bool, str]:
    key = _kind_key(kind)
    normalized = _normalize_text(name)
    if not normalized:
        return False, "Categoria inválida."

    payload = load_financial_categories()
    existing = payload[key]
    remaining = [item for item in existing if item.casefold() != normalized.casefold()]
    if len(remaining) == len(existing):
        return False, "Categoria não encontrada."
    if not remaining:
        return False, "Mantenha ao menos uma categoria cadastrada."

    payload[key] = remaining
    save_financial_categories(payload)
    return True, normalized
