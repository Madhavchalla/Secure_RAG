import re
from typing import Dict, Any, List

# Curated detection rules for prompt injection and instruction hijacking
INJECTION_SIGNATURES = [
    {
        "id": "INJ-001",
        "name": "Instruction Override",
        "pattern": r"(?i)\b(ignore|disregard|forget|override)\s+(all\s+)?(previous|prior|above|system)\s+(instructions|prompts|rules|guidelines)",
        "severity": "CRITICAL",
        "weight": 85.0,
    },
    {
        "id": "INJ-002",
        "name": "System Prompt Extraction",
        "pattern": r"(?i)\b(reveal|output|print|show|repeat|dump)\s+(the\s+)?(system\s+prompt|initial\s+prompt|developer\s+mode|internal\s+instructions)",
        "severity": "HIGH",
        "weight": 75.0,
    },
    {
        "id": "INJ-003",
        "name": "Privilege Escalation & ACL Bypass",
        "pattern": r"(?i)\b(bypass|disregard|ignore)\s+(the\s+)?(user'?s?\s+)?(permission|acl|access\s+control|role|restrictions|limits)",
        "severity": "CRITICAL",
        "weight": 90.0,
    },
    {
        "id": "INJ-004",
        "name": "Confidential Exfiltration Directive",
        "pattern": r"(?i)\b(output|print|dump|leak|exfiltrate)\s+(all\s+)?(confidential|restricted|secret|salary|payroll|passwords?|credentials?)",
        "severity": "HIGH",
        "weight": 70.0,
    },
    {
        "id": "INJ-005",
        "name": "Synthetic Persona / Jailbreak Staging",
        "pattern": r"(?i)\b(you\s+are\s+now\s+in\s+|act\s+as\s+a\s+|enter\s+)(developer\s+maintenance\s+mode|unrestricted\s+mode|god\s+mode|dan\s+mode)",
        "severity": "CRITICAL",
        "weight": 80.0,
    },
    {
        "id": "INJ-006",
        "name": "Adversarial Control Delimiters",
        "pattern": r"(<\/?system>|\[INST\]|\[\/INST\]|###\s*(Instruction|System):|<<SYS>>)",
        "severity": "MEDIUM",
        "weight": 55.0,
    },
]


class IngestionSecurityScanner:
    """
    Static heuristic scanner for pre-ingestion threat analysis.
    Inspects document text for known prompt injection payloads,
    privilege bypass directives, and malicious control delimiters.
    """

    def __init__(self, signatures: List[Dict[str, Any]] = None):
        self.signatures = signatures or INJECTION_SIGNATURES

    def scan_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze document or query text against compiled threat signatures.
        Returns detection verdict, triggered rules, and threat score.
        """
        if not text or not text.strip():
            return {
                "is_suspicious": False,
                "triggered_rules": [],
                "highest_severity": "NONE",
                "threat_score": 0.0,
            }

        triggered_rules = []
        max_score = 0.0
        severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}
        highest_severity = "NONE"

        for sig in self.signatures:
            matches = list(re.finditer(sig["pattern"], text))
            if matches:
                # Capture matched snippet for explainability
                sample_snippet = matches[0].group(0)
                triggered_rules.append({
                    "id": sig["id"],
                    "name": sig["name"],
                    "severity": sig["severity"],
                    "weight": sig["weight"],
                    "matched_snippet": sample_snippet,
                })
                if sig["weight"] > max_score:
                    max_score = sig["weight"]
                if severity_order.get(sig["severity"], 0) > severity_order.get(highest_severity, 0):
                    highest_severity = sig["severity"]

        is_suspicious = len(triggered_rules) > 0

        return {
            "is_suspicious": is_suspicious,
            "triggered_rules": triggered_rules,
            "highest_severity": highest_severity,
            "threat_score": min(100.0, max_score),
        }


# Singleton scanner instance
ingestion_scanner = IngestionSecurityScanner()
