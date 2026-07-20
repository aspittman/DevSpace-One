import unittest
from unittest.mock import patch

from services.apollo_outreach import runner


class ApolloRunnerConfigTests(unittest.TestCase):
    @patch.object(runner, "write_csv")
    @patch.object(runner, "outreach_result_to_crm_payload", return_value={})
    @patch.object(runner, "build_email", return_value="Body")
    @patch.object(runner, "build_subject_for_lead", return_value="Subject")
    @patch.object(runner, "best_domain_match")
    @patch.object(runner, "load_apollo_leads")
    @patch.object(runner, "load_domain_offers", return_value=[{"domain": "businessfunding.com"}])
    @patch.object(runner, "CRMClient")
    def test_creates_at_most_five_crm_drafts(
        self,
        crm_class,
        load_domains,
        load_leads,
        best_match,
        build_subject,
        build_body,
        build_payload,
        write_csv,
    ):
        leads = [
            {"email": f"person{index}@example.com", "company": f"Company {index}"}
            for index in range(8)
        ]
        offer = {"domain": "businessfunding.com"}
        load_leads.return_value = leads
        best_match.return_value = (offer, 90, ["strong fit"])

        runner.run(
            organization_id="org-1",
            config={"sync_responses": False, "max_ingests": 50},
        )

        self.assertEqual(crm_class.return_value.ingest_lead.call_count, 5)
        self.assertEqual(build_payload.call_count, 5)

    @patch.object(runner, "send_approved_outreach", create=True)
    @patch.object(runner, "load_domain_offers", return_value=[])
    @patch.object(runner, "CRMClient")
    def test_does_not_send_email_during_draft_generation(
        self, crm_class, load_domains, legacy_sender
    ):
        runner.run(organization_id="org-1", config={"sync_responses": False})

        legacy_sender.assert_not_called()


if __name__ == "__main__":
    unittest.main()
