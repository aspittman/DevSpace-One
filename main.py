from core.crm_client import CRMClient
from services.domain_merchant.runner import run as run_domain_merchant
from services.apollo_outreach.runner import run as run_apollo_outreach
from dotenv import load_dotenv

load_dotenv()

def main():
    crm = CRMClient()

    response = crm.get_enabled_services()
    services = response.get("services", [])

    for service in services:
        service_key = service["service_key"]
        organization_id = service["organization_id"]
        niche = service.get("niche")

        print(f"Running {service_key} for {organization_id}")

        if service_key == "domain_merchant":
            signals = crm.get_domain_signals(
                organization_id=organization_id,
                niche=niche,
            )

            run_domain_merchant(
                organization_id=organization_id,
                niche=niche,
                signals=signals,
                config=service.get("config_json", {}),
            )

        elif service_key == "apollo_outreach":
            run_apollo_outreach(
                organization_id=organization_id,
                niche=niche,
                config=service.get("config_json", {}),
            )

if __name__ == "__main__":
    main()