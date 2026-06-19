import os
import requests


class CRMClient:
    def __init__(self):
        self.base_url = os.getenv("CRM_BASE_URL")
        self.api_secret = os.getenv("CRM_BOT_API_SECRET")

        if not self.base_url:
            raise ValueError("CRM_BASE_URL is missing")

        if not self.api_secret:
            raise ValueError("CRM_BOT_API_SECRET is missing")

        self.base_url = self.base_url.rstrip("/")

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_secret}",
            "Content-Type": "application/json",
        }

    def _get(self, path, params=None):
        url = f"{self.base_url}{path}"

        response = requests.get(
            url,
            headers=self._headers(),
            params=params or {},
            timeout=30,
        )

        if not response.ok:
            raise Exception(f"CRM GET failed: {response.status_code} {response.text}")

        return response.json()

    def _post(self, path, payload):
        url = f"{self.base_url}{path}"

        response = requests.post(
            url,
            headers=self._headers(),
            json=payload,
            timeout=30,
        )

        if not response.ok:
            raise Exception(f"CRM POST failed: {response.status_code} {response.text}")

        return response.json()

    def ingest_lead(self, payload):
        return self._post("/api/ingest", payload)

    def domain_exists(self, organization_id, domain):
        return self._get(
            "/api/bot/domain-exists",
            params={
                "organization_id": organization_id,
                "domain": domain,
            },
        )

    def get_enabled_services(self):
        return self._get("/api/bot/enabled-services")

    def get_service_config(self, organization_id, service_key, niche=None):
        params = {
            "organization_id": organization_id,
            "service_key": service_key,
        }

        if niche:
            params["niche"] = niche

        return self._get("/api/bot/service-config", params=params)

    def get_domain_signals(self, organization_id, niche=None):
        params = {
            "organization_id": organization_id,
        }

        if niche:
            params["niche"] = niche

        return self._get("/api/bot/domain-signals", params=params)

    def get_outreach_performance(self, organization_id, domain=None):
        params = {
            "organization_id": organization_id,
        }

        if domain:
            params["domain"] = domain

        return self._get("/api/bot/outreach-performance", params=params)
