import os
import requests
from dotenv import load_dotenv

load_dotenv()


class CRMClient:
    def __init__(self):
        self.base_url = os.getenv("CRM_BASE_URL")
        self.api_key = os.getenv("CRM_BOT_API_KEY")

        if not self.base_url:
            raise ValueError("CRM_BASE_URL is missing")

        if not self.api_key:
            raise ValueError("CRM_BOT_API_KEY is missing")

    def headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def ingest_lead(self, payload: dict):
        url = f"{self.base_url}/api/ingest"
        response = requests.post(url, json=payload, headers=self.headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def get_strategy(self, lead_id: str):
        url = f"{self.base_url}/api/bot/strategy"
        response = requests.get(
            url,
            params={"lead_id": lead_id},
            headers=self.headers(),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def record_outreach_event(self, payload: dict):
        url = f"{self.base_url}/api/bot/outreach-events"
        response = requests.post(url, json=payload, headers=self.headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def register_service(self, client_slug, service_key, service_name, niche=None):
        url = f"{self.base_url}/api/bot/register-service"

        payload = {
            "client_slug": client_slug,
            "service_key": service_key,
            "service_name": service_name,
            "niche": niche,
        }

        response = requests.post(
            url,
            json=payload,
            headers=self.headers(),
            timeout=30,
        )

        response.raise_for_status()
        return response.json()