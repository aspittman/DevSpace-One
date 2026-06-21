from pathlib import Path

import yaml


NICHES_DIR = Path(__file__).resolve().parent / "niches"


def load_niche_config(niche: str) -> dict:
    key = niche or "chiropractors"
    path = NICHES_DIR / f"{key}.yaml"

    if not path.exists():
        raise ValueError(f"Unknown devspace outreach niche: {key}")

    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    config.setdefault("key", key)
    return config


def available_niches() -> list[str]:
    return sorted(path.stem for path in NICHES_DIR.glob("*.yaml"))
