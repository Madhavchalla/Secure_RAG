from typing import Dict, Any
from app.core.config import settings


class DecisionMatrix:
    """
    Policy decision engine translating composite risk scores into
    actionable governance outcomes: ALLOW, RESTRICT, VERIFY, BLOCK.
    """

    def __init__(
        self,
        allow_threshold: float = None,
        restrict_threshold: float = None,
        verify_threshold: float = None
    ):
        self.allow_threshold = allow_threshold or settings.THRESHOLD_ALLOW
        self.restrict_threshold = restrict_threshold or settings.THRESHOLD_RESTRICT
        self.verify_threshold = verify_threshold or settings.THRESHOLD_VERIFY

    def evaluate_decision(self, final_risk_score: float) -> Dict[str, Any]:
        """
        Determines the policy posture based on composite risk score.
        """
        if final_risk_score < self.allow_threshold:
            return {
                "decision": "ALLOW",
                "explanation": "Request permitted under current baseline risk profile.",
                "mask_pii": False,
                "truncate_context": False,
                "allow_llm": True,
            }
        elif final_risk_score < self.restrict_threshold:
            return {
                "decision": "RESTRICT",
                "explanation": "Elevated risk detected. Response restricted: PII masking enforced and context truncated.",
                "mask_pii": True,
                "truncate_context": True,
                "allow_llm": True,
            }
        elif final_risk_score < self.verify_threshold:
            return {
                "decision": "VERIFY",
                "explanation": "High contextual risk detected. Elevated verification is required before information disclosure.",
                "mask_pii": True,
                "truncate_context": True,
                "allow_llm": False,
            }
        else:
            return {
                "decision": "BLOCK",
                "explanation": "Security violation: Request blocked due to critical risk score and potential threat activity.",
                "mask_pii": True,
                "truncate_context": True,
                "allow_llm": False,
            }


# Singleton decision matrix instance
decision_matrix = DecisionMatrix()
