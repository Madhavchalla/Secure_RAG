import re
from typing import Tuple, List, Dict

PII_PATTERNS = [
    {
        "type": "EMAIL",
        "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "mask": "[EMAIL_REDACTED]",
    },
    {
        "type": "PHONE",
        "pattern": r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "mask": "[PHONE_REDACTED]",
    },
    {
        "type": "SSN",
        "pattern": r"\b\d{3}-\d{2}-\d{4}\b",
        "mask": "[SSN_REDACTED]",
    },
    {
        "type": "CREDIT_CARD",
        "pattern": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        "mask": "[CARD_REDACTED]",
    },
    {
        "type": "FINANCIAL_AMOUNT",
        "pattern": r"\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b",
        "mask": "[AMOUNT_REDACTED]",
    },
]


class PIIMasker:
    """
    Sanitizes retrieved document context and model outputs by masking
    Personally Identifiable Information (PII) and financial identifiers.
    """

    def __init__(self, patterns: List[Dict[str, str]] = None):
        self.patterns = patterns or PII_PATTERNS

    def mask(self, text: str, mask_financial: bool = True) -> Tuple[str, List[str]]:
        """
        Replaces detected PII tokens with sanitized placeholders.
        Returns sanitized text and list of masked categories.
        """
        if not text:
            return text, []

        sanitized = text
        masked_types = []

        for p in self.patterns:
            if not mask_financial and p["type"] == "FINANCIAL_AMOUNT":
                continue

            matches = re.findall(p["pattern"], sanitized)
            if matches:
                masked_types.append(p["type"])
                sanitized = re.sub(p["pattern"], p["mask"], sanitized)

        return sanitized, list(set(masked_types))


# Singleton PII masker instance
pii_masker = PIIMasker()
