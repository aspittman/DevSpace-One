import argparse

from dotenv import load_dotenv

from core.crm_client import CRMClient


def parse_args():
    parser = argparse.ArgumentParser(description="Smoke-test CRM bot endpoints.")
    parser.add_argument("--organization-id", help="CRM organization id.")
    parser.add_argument("--niche", help="Optional niche for scoped endpoints.")
    parser.add_argument("--domain", help="Optional domain for domain checks.")
    return parser.parse_args()


def show_result(name: str, callback):
    try:
        result = callback()
        print(f"{name}: OK")

        if isinstance(result, dict):
            keys = ", ".join(sorted(result.keys()))
            print(f"  keys: {keys}")
        elif isinstance(result, list):
            print(f"  rows: {len(result)}")

    except Exception as exc:
        print(f"{name}: FAILED")
        print(f"  {exc}")


def main():
    load_dotenv()
    args = parse_args()
    crm = CRMClient()

    show_result("enabled-services", crm.get_enabled_services)

    if args.organization_id:
        show_result(
            "domain-signals",
            lambda: crm.get_domain_signals(
                organization_id=args.organization_id,
                niche=args.niche,
            ),
        )
        show_result(
            "outreach-performance",
            lambda: crm.get_outreach_performance(
                organization_id=args.organization_id,
                domain=args.domain,
            ),
        )

    if args.organization_id and args.domain:
        show_result(
            "domain-exists",
            lambda: crm.domain_exists(
                organization_id=args.organization_id,
                domain=args.domain,
            ),
        )


if __name__ == "__main__":
    main()
