import os
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import requests


DEFAULT_BLOCKED_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "yelp.com",
    "yellowpages.com",
    "mapquest.com",
    "google.com",
    "bing.com",
    "healthgrades.com",
    "zocdoc.com",
    "webmd.com",
    "bbb.org",
}


def as_list(value):
    if not value:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    return [
        item.strip()
        for item in str(value).split(",")
        if item.strip()
    ]


def _host_matches(host: str, blocked_domain: str) -> bool:
    return host == blocked_domain or host.endswith(f".{blocked_domain}")


def is_blocked_url(url: str, blocked_domains: set[str]) -> bool:
    host = urlparse(url).netloc.lower()

    if host.startswith("www."):
        host = host[4:]

    return any(_host_matches(host, domain) for domain in blocked_domains)


def clean_url(url: str) -> str:
    parsed = urlparse(url)

    if parsed.netloc.endswith("google.com") and parsed.path == "/url":
        target = parse_qs(parsed.query).get("q", [None])[0]

        if target:
            return clean_url(target)

    parsed = parsed._replace(fragment="")

    if parsed.query:
        query = {
            key: value
            for key, value in parse_qs(parsed.query).items()
            if not key.lower().startswith("utm_")
        }
        parsed = parsed._replace(query=urlencode(query, doseq=True))

    return urlunparse(parsed)


def website_key(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if host.startswith("www."):
        host = host[4:]

    return host


def infer_company_name(title: str, fallback_domain: str) -> str:
    title = (title or "").strip()

    for separator in (" | ", " - ", " – ", " — "):
        if separator in title:
            title = title.split(separator)[0].strip()
            break

    if title:
        return title

    return fallback_domain.removeprefix("www.").split(".")[0].replace("-", " ").title()


def _provider(config: dict) -> str:
    provider = (
        config.get("search_provider")
        or os.getenv("DEVSPACE_SEARCH_PROVIDER")
        or ""
    ).lower().strip()

    if provider:
        return provider

    if config.get("bing_api_key") or os.getenv("BING_SEARCH_API_KEY"):
        return "bing"

    if (
        config.get("google_api_key")
        or os.getenv("GOOGLE_SEARCH_API_KEY")
    ) and (
        config.get("google_cse_id")
        or os.getenv("GOOGLE_CSE_ID")
    ):
        return "google_cse"

    if config.get("serpapi_key") or os.getenv("SERPAPI_API_KEY") or os.getenv("SERP_API_KEY"):
        return "serpapi"

    return "disabled"


def _bing_search(query: str, count: int, config: dict) -> list[dict]:
    api_key = config.get("bing_api_key") or os.getenv("BING_SEARCH_API_KEY")

    if not api_key:
        raise ValueError("BING_SEARCH_API_KEY is missing")

    response = requests.get(
        config.get("bing_endpoint") or "https://api.bing.microsoft.com/v7.0/search",
        headers={"Ocp-Apim-Subscription-Key": api_key},
        params={"q": query, "count": count},
        timeout=int(config.get("search_timeout", 20)),
    )
    response.raise_for_status()

    return [
        {
            "title": item.get("name", ""),
            "url": item.get("url", ""),
            "snippet": item.get("snippet", ""),
        }
        for item in response.json().get("webPages", {}).get("value", [])
    ]


def _google_cse_search(query: str, count: int, config: dict) -> list[dict]:
    api_key = config.get("google_api_key") or os.getenv("GOOGLE_SEARCH_API_KEY")
    cse_id = config.get("google_cse_id") or os.getenv("GOOGLE_CSE_ID")

    if not api_key:
        raise ValueError("GOOGLE_SEARCH_API_KEY is missing")

    if not cse_id:
        raise ValueError("GOOGLE_CSE_ID is missing")

    response = requests.get(
        "https://www.googleapis.com/customsearch/v1",
        params={
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "num": min(count, 10),
        },
        timeout=int(config.get("search_timeout", 20)),
    )
    response.raise_for_status()

    return [
        {
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        }
        for item in response.json().get("items", [])
    ]


def _serpapi_search(query: str, count: int, config: dict) -> list[dict]:
    api_key = config.get("serpapi_key") or os.getenv("SERPAPI_API_KEY") or os.getenv("SERP_API_KEY")

    if not api_key:
        raise ValueError("SERPAPI_API_KEY or SERP_API_KEY is missing")

    response = requests.get(
        "https://serpapi.com/search.json",
        params={
            "engine": "google",
            "api_key": api_key,
            "q": query,
            "num": count,
        },
        timeout=int(config.get("search_timeout", 20)),
    )
    response.raise_for_status()

    return [
        {
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        }
        for item in response.json().get("organic_results", [])
    ]


def search_query(query: str, count: int, config: dict) -> list[dict]:
    provider = _provider(config)

    if provider == "bing":
        return _bing_search(query, count, config)

    if provider == "google_cse":
        return _google_cse_search(query, count, config)

    if provider == "serpapi":
        return _serpapi_search(query, count, config)

    if provider in {"disabled", "none", "off"}:
        return []

    raise ValueError(f"Unsupported search provider: {provider}")


def discover_prospects(niche_config: dict, config: dict) -> list[dict]:
    search_config = niche_config.get("search", {})
    queries = as_list(config.get("queries")) or as_list(search_config.get("queries"))
    locations = as_list(config.get("locations")) or as_list(niche_config.get("locations"))
    results_per_query = int(config.get("results_per_query", 5))
    max_prospects = int(config.get("max_prospects", 25))
    blocked_domains = DEFAULT_BLOCKED_DOMAINS.union(
        {domain.lower() for domain in as_list(config.get("blocked_domains"))}
    )
    prospects = []
    seen = set()

    if not queries or not locations:
        return prospects

    for location in locations:
        for template in queries:
            query = template.format(location=location)

            for result in search_query(query, results_per_query, config):
                url = clean_url(result.get("url") or "")

                if not url or is_blocked_url(url, blocked_domains):
                    continue

                key = website_key(url)

                if not key or key in seen:
                    continue

                seen.add(key)
                prospects.append({
                    "company_name": infer_company_name(result.get("title", ""), key),
                    "website": url,
                    "location": location,
                    "search_query": query,
                    "search_title": result.get("title", ""),
                    "search_snippet": result.get("snippet", ""),
                    "discovery_source": _provider(config),
                })

                if len(prospects) >= max_prospects:
                    return prospects

    return prospects
