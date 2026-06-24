import os
from typing import Any

import requests


DEFAULT_APOLLO_BASE_URL = "https://api.apollo.io/api/v1"
PEOPLE_SEARCH_PATH = "/mixed_people/api_search"


class ApolloClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.getenv("APOLLO_API_KEY")
        self.base_url = (base_url or os.getenv("APOLLO_BASE_URL") or DEFAULT_APOLLO_BASE_URL).rstrip("/")

        if not self.api_key:
            raise ValueError("APOLLO_API_KEY is missing")

    def _headers(self) -> dict[str, str]:
        return {
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "X-Api-Key": self.api_key,
        }

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(
            f"{self.base_url}{path}",
            headers=self._headers(),
            json=payload,
            timeout=45,
        )

        if not response.ok:
            raise Exception(f"Apollo POST failed: {response.status_code} {response.text}")

        return response.json()

    def search_people(
        self,
        *,
        keywords: list[str],
        titles: list[str] | None = None,
        seniorities: list[str] | None = None,
        organization_locations: list[str] | None = None,
        per_page: int = 25,
        max_pages: int = 1,
        extra_payload: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        people: list[dict[str, Any]] = []
        base_payload = dict(extra_payload or {})

        if titles:
            base_payload["person_titles"] = titles

        if seniorities:
            base_payload["person_seniorities"] = seniorities

        if organization_locations:
            base_payload["organization_locations"] = organization_locations

        for keyword in keywords:
            for page in range(1, max_pages + 1):
                payload = {
                    **base_payload,
                    "q_keywords": keyword,
                    "page": page,
                    "per_page": per_page,
                }

                response = self._post(PEOPLE_SEARCH_PATH, payload)
                batch = response.get("people") or response.get("contacts") or []

                if not batch:
                    break

                for person in batch:
                    person["_apollo_keyword"] = keyword
                    people.append(person)

        return people


def normalize_apollo_person(person: dict[str, Any], keyword: str | None = None) -> dict[str, Any]:
    organization = person.get("organization") or {}

    website = (
        organization.get("website_url")
        or organization.get("primary_domain")
        or person.get("organization_website_url")
        or ""
    )

    company = (
        organization.get("name")
        or person.get("organization_name")
        or person.get("company")
        or ""
    )

    keywords = " ".join(
        str(value)
        for value in [
            keyword,
            organization.get("industry"),
            organization.get("short_description"),
            organization.get("seo_description"),
        ]
        if value
    )

    return {
        "apollo_person_id": person.get("id"),
        "apollo_organization_id": organization.get("id") or person.get("organization_id"),
        "first_name": person.get("first_name") or "",
        "last_name": person.get("last_name") or "",
        "title": person.get("title") or "",
        "email": person.get("email") or "",
        "email_status": person.get("email_status") or "",
        "company": company,
        "website": website,
        "industry": organization.get("industry") or "",
        "linkedin_url": person.get("linkedin_url") or "",
        "city": person.get("city") or "",
        "state": person.get("state") or "",
        "country": person.get("country") or "",
        "keywords": keywords,
        "apollo_raw": person,
    }
