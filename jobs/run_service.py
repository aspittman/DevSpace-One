import argparse

from dotenv import load_dotenv

from core.crm_client import CRMClient
from services.afternic_sync.runner import run as run_afternic_sync
from services.apollo_outreach.runner import run as run_apollo_outreach
from services.domain_merchant.runner import run as run_domain_merchant


RUNNERS = {
    "domain_merchant": run_domain_merchant,
    "apollo_outreach": run_apollo_outreach,
    "afternic_sync": run_afternic_sync,
}


def parse_args():
    parser = argparse.ArgumentParser(description="Run one CRM bot service.")
    parser.add_argument(
        "service",
        choices=sorted(RUNNERS),
        help="Service key to run.",
    )
    parser.add_argument("--organization-id", help="CRM organization id.")
    parser.add_argument("--niche", help="Optional service niche.")
    parser.add_argument(
        "--use-crm-config",
        action="store_true",
        help="Load service config from the CRM before running.",
    )
    return parser.parse_args()


def main():
    load_dotenv()
    args = parse_args()
    crm = CRMClient()
    config = {}

    if args.use_crm_config and args.organization_id:
        response = crm.get_service_config(
            organization_id=args.organization_id,
            service_key=args.service,
            niche=args.niche,
        )
        config = response.get("config_json") or response.get("config") or {}

    signals = None

    if args.service in {"domain_merchant", "apollo_outreach"} and args.organization_id:
        signals = crm.get_domain_signals(
            organization_id=args.organization_id,
            niche=args.niche,
        )

    RUNNERS[args.service](
        organization_id=args.organization_id,
        niche=args.niche,
        signals=signals,
        config=config,
    )


if __name__ == "__main__":
    main()
