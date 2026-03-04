class RetailPipeline:
    def run(self, applicant):
        score = applicant["cibil_score"] - applicant["foir_post_loan"]
        risk = "LOW" if score > 650 else "MEDIUM" if score > 550 else "HIGH"
        return {
            **applicant,
            "risk": risk,
            "lead_score": 70
        }

class SMEPipeline:
    def run(self, applicant):
        score = applicant["cibil_score"] + applicant["dscr"]*40
        risk = "LOW" if score > 800 else "MEDIUM" if score > 700 else "HIGH"
        return {
            **applicant,
            "risk": risk,
            "financial_health_score": 75
        }
