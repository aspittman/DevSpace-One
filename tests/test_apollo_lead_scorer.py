import unittest

from services.apollo_outreach.apollo_client import normalize_apollo_person
from services.apollo_outreach.lead_scorer import score_lead


DOMAIN = {"domain": "bestbusinessfunding.com"}


class ApolloLeadScorerTests(unittest.TestCase):
    def test_strong_verified_decision_maker_passes_threshold(self):
        score, reasons = score_lead({
            "company": "Acme Funding",
            "title": "Founder and CEO",
            "email": "owner@example.com",
            "email_status": "verified",
            "website": "https://example.com",
            "keywords": "Small business loans and working capital",
            "employee_count": 25,
        }, DOMAIN)

        self.assertGreaterEqual(score, 70)
        self.assertIn("verified email", reasons)
        self.assertEqual(1, sum(reason.startswith("decision-maker title:") for reason in reasons))

    def test_search_keyword_is_not_used_as_fit_evidence(self):
        lead = normalize_apollo_person({
            "title": "CEO",
            "email": "owner@example.com",
            "email_status": "verified",
            "organization": {"name": "Unrelated Software", "industry": "Software"},
        }, keyword="business funding")

        score, reasons = score_lead(lead, DOMAIN)

        self.assertLess(score, 70)
        self.assertFalse(any(reason.startswith("industry match:") for reason in reasons))
        self.assertEqual("business funding", lead["apollo_search_keyword"])
        self.assertNotIn("business funding", lead["keywords"])

    def test_invalid_email_and_excluded_industry_are_penalized(self):
        score, reasons = score_lead({
            "company": "Student Loan Help University",
            "title": "CEO",
            "email": "bad@example.com",
            "email_status": "invalid",
            "website": "https://example.com",
            "keywords": "business funding and student loan forgiveness",
        }, DOMAIN)

        self.assertLess(score, 70)
        self.assertTrue(any(reason.startswith("bad fit:") for reason in reasons))
        self.assertIn("invalid email status: invalid", reasons)

    def test_overlapping_industry_terms_do_not_each_add_full_bonus(self):
        score, reasons = score_lead({
            "keywords": "business funding, small business loans, working capital, capital, lending",
        }, DOMAIN)

        self.assertEqual(45, score)
        self.assertLessEqual(sum(reason.startswith("industry match:") for reason in reasons), 2)


if __name__ == "__main__":
    unittest.main()
