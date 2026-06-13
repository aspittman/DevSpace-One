import os
from pathlib import Path

from core.crm_client import CRMClient
from services.afternic_sync.csv_loader import read_csv
from services.afternic_sync.normalizer import normalize_afternic_row
from services.afternic_sync.adapter import afternic_result_to_crm_payload


AFTERNIC_FILE = Path("data/afternic/afternic_export.csv")


def run():
    organization_id = os.getenv("DOMAIN_MERCHANT_ORG_ID")

    if not organization_id:
        raise ValueError("DOMAIN_MERCHANT_ORG_ID is missing from .env")

    rows = read_csv(AFTERNIC_FILE)

    if not rows:
        print("No Afternic rows found.")
        return

    crm = CRMClient()

    synced = 0
    sold = 0
    listed = 0

    for row in rows:
        result = normalize_afternic_row(row)

        if not result["domain"]:
            continue

        payload = afternic_result_to_crm_payload(
            result=result,
            organization_id=organization_id,
        )

        crm.ingest_lead(payload)

        synced += 1

        if result["outcome"] == "sold":
            sold += 1
        elif result["outcome"] == "listed":
            listed += 1

    print(f"Afternic sync complete.")
    print(f"Rows synced: {synced}")
    print(f"Sold domains: {sold}")
    print(f"Listed domains: {listed}")