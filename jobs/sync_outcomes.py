import argparse
import os

from dotenv import load_dotenv

from core.crm_client import CRMClient
from services.afternic_sync.runner import run as run_afternic_sync
from services.apollo_outreach.responses import RESPONSES_FILE, sync_responses


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sync marketplace and outreach outcomes into the CRM."
    )
    parser.add_argument("--organization-id", help="CRM organization id.")
    parser.add_argument("--niche", help="Optional niche.")
    parser.add_argument("--afternic-file", help="Afternic CSV export path.")
    parser.add_argument("--purchases-file", help="Domain purchases CSV path.")
    parser.add_argument(
        "--responses-file",
        default=str(RESPONSES_FILE),
        help="Apollo outreach responses CSV path.",
    )
    parser.add_argument(
        "--skip-afternic",
        action="store_true",
        help="Only sync Apollo outreach responses.",
    )
    parser.add_argument(
        "--skip-responses",
        action="store_true",
        help="Only sync Afternic outcomes.",
    )
    return parser.parse_args()


def main():
    load_dotenv()
    args = parse_args()
    crm = CRMClient()
    organization_id = (
        args.organization_id
        or os.getenv("APOLLO_OUTREACH_ORG_ID")
        or os.getenv("DOMAIN_MERCHANT_ORG_ID")
    )

    if not organization_id:
        raise ValueError(
            "Provide --organization-id or set APOLLO_OUTREACH_ORG_ID/DOMAIN_MERCHANT_ORG_ID."
        )

    if not args.skip_afternic:
        config = {}

        if args.afternic_file:
            config["afternic_file"] = args.afternic_file

        if args.purchases_file:
            config["purchases_file"] = args.purchases_file

        run_afternic_sync(
            organization_id=organization_id,
            niche=args.niche,
            config=config,
        )

    if not args.skip_responses:
        synced = sync_responses(
            organization_id=organization_id,
            responses_file=args.responses_file,
            crm=crm,
        )
        print(f"Synced {synced} Apollo Outreach responses to CRM")


if __name__ == "__main__":
    main()
