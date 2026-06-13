from services.domain_merchant.config import CITY_TERMS, STATE_TERMS
from services.domain_merchant.niche_config import NICHE_CONFIG


def generate_domains_for_niche(niche: str, limit: int | None = None) -> list[dict]:
    if niche not in NICHE_CONFIG:
        raise ValueError(f"Unknown domain merchant niche: {niche}")

    config = NICHE_CONFIG[niche]
    patterns = config["patterns"]

    candidates = []
    locations = STATE_TERMS + CITY_TERMS
    prefixes = ["top", "best", "fast", "local"]

    for pattern in patterns:
        candidates.append({
            "domain": f"{pattern}.com",
            "source": "generated_base",
            "niche": niche,
        })

        for prefix in prefixes:
            candidates.append({
                "domain": f"{prefix}{pattern}.com",
                "source": "generated_prefix",
                "niche": niche,
            })

        for location in locations:
            candidates.append({
                "domain": f"{location}{pattern}.com",
                "source": "generated_local",
                "niche": niche,
            })

    seen = set()
    deduped = []

    for item in candidates:
        domain = item["domain"]

        if domain in seen:
            continue

        seen.add(domain)
        deduped.append(item)

    if limit:
        return deduped[:limit]

    return deduped