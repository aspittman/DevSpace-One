import os
from typing import Any
from urllib.parse import urlparse

import requests


DEFAULT_APOLLO_BASE_URL = "https://api.apollo.io/api/v1"
PEOPLE_SEARCH_PATH = "/mixed_people/api_search"
PEOPLE_ENRICHMENT_PATH = "/people/match"


def _domain_from_url(value: str | None) -> str:
    raw = str(value or "").strip()

    if not raw:
        return ""

    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    return parsed.netloc or parsed.path.split("/", 1)[0]


def _first_email(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and "@" in value:
            return value

        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and "@" in item:
                    return item

                if isinstance(item, dict):
                    email = _first_email(item.get("email"), item.get("value"))

                    if email:
                        return email

    return ""


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

    def _post(self, path: str, payload: dict[str, Any], *, as_params: bool = False) -> dict[str, Any]:
        response = requests.post(
            f"{self.base_url}{path}",
            headers=self._headers(),
            params=payload if as_params else None,
            json=None if as_params else payload,
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

    def enrich_person(
        self,
        person: dict[str, Any],
        *,
        reveal_personal_emails: bool = False,
        run_waterfall_email: bool = False,
    ) -> dict[str, Any] | None:
        payload: dict[str, Any] = {}

        if person.get("apollo_person_id"):
            payload["id"] = person["apollo_person_id"]

        if person.get("first_name"):
            payload["first_name"] = person["first_name"]

        if person.get("last_name"):
            payload["last_name"] = person["last_name"]

        if person.get("company"):
            payload["organization_name"] = person["company"]

        if person.get("website"):
            payload["domain"] = _domain_from_url(person["website"])

        if person.get("linkedin_url"):
            payload["linkedin_url"] = person["linkedin_url"]

        if reveal_personal_emails:
            payload["reveal_personal_emails"] = "true"

        if run_waterfall_email:
            payload["run_waterfall_email"] = "true"

        if not payload:
            return None

        response = self._post(PEOPLE_ENRICHMENT_PATH, payload, as_params=True)
        return response.get("person") or response.get("contact") or response


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

    # Do not include ``keyword`` here. It is the query that found the person, not
    # independent evidence that their organization matches the query.
    keywords = " ".join(
        str(value)
        for value in [
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
        "email": _first_email(
            person.get("email"),
            person.get("work_email"),
            person.get("personal_email"),
            person.get("personal_emails"),
            person.get("emails"),
        ),
        "email_status": person.get("email_status") or "",
        "apollo_search_keyword": keyword or "",
        "company": company,
        "website": website,
        "industry": organization.get("industry") or "",
        "linkedin_url": person.get("linkedin_url") or "",
        "city": person.get("city") or "",
        "state": person.get("state") or "",
        "country": person.get("country") or "",
        "employee_count": (
            organization.get("estimated_num_employees")
            or organization.get("employee_count")
            or ""
        ),
        "keywords": keywords,
        "apollo_raw": person,
    }
