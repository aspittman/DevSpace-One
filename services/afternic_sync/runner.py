import os
from pathlib import Path

from core.crm_client import CRMClient
from services.afternic_sync.csv_loader import read_csv
from services.afternic_sync.normalizer import normalize_afternic_row, normalize_domain_purchase_row
from services.afternic_sync.adapter import afternic_result_to_crm_payload, domain_purchase_to_crm_payload


AFTERNIC_FILE = Path("data/afternic/afternic_export.csv")
PURCHASES_FILE = Path("data/afternic/domain_purchases.csv")


def run(organization_id: str, niche: str | None = None, signals=None, config=None):
    config = config or {}
    organization_id = organization_id or os.getenv("DOMAIN_MERCHANT_ORG_ID")

    if not organization_id:
        raise ValueError("DOMAIN_MERCHANT_ORG_ID is missing from .env")

    purchases_file = Path(config.get("purchases_file", PURCHASES_FILE))
    afternic_file = Path(config.get("afternic_file", AFTERNIC_FILE))
    purchase_rows = read_csv(purchases_file)
    rows = read_csv(afternic_file)

    if not rows and not purchase_rows:
        print("No Afternic rows or domain purchase rows found.")
        return

    crm = CRMClient()

    purchased = 0
    synced = 0
    sold = 0
    listed = 0

    for row in purchase_rows:
        result = normalize_domain_purchase_row(row)

        if not result["domain"]:
            continue

        payload = domain_purchase_to_crm_payload(
            result=result,
            organization_id=organization_id,
        )

        crm.ingest_lead(payload)
        purchased += 1

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
    print(f"Purchased domains synced: {purchased}")
    print(f"Rows synced: {synced}")
    print(f"Sold domains: {sold}")
    print(f"Listed domains: {listed}")
