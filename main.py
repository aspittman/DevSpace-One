import argparse

from services.apollo_outreach.runner import run as run_apollo
from services.brazilian_lemonade_scout.runner import run as run_brazilian_lemonade
from services.devspace_outreach.runner import run as run_devspace
from services.domain_merchant.runner import run as run_merchant
from services.microgreen_scout.runner import run as run_microgreen_scout
from services.snowcone_scout.runner import run as run_snowcone_scout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--service", required=True)
    parser.add_argument("--niche", required=False)
    args = parser.parse_args()

    if args.service == "apollo_outreach":
        run_apollo()
    elif args.service == "devspace_outreach":
        run_devspace(niche=args.niche)
    elif args.service == "brazilian_lemonade_scout":
        run_brazilian_lemonade()
    elif args.service == "microgreen_scout":
        run_microgreen_scout()
    elif args.service == "domain_merchant":
        run_merchant(niche=args.niche)
    elif args.service == "snowcone_scout":
        run_snowcone_scout()
    else:
        raise ValueError(f"Unknown service: {args.service}")


if __name__ == "__main__":
    main()