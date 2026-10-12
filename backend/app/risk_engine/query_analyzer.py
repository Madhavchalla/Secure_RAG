import re
from typing import Dict, Any, List, Tuple

# Query threat rules tailored for natural language RAG assistants
QUERY_PATTERNS = [
    {
        "id": "Q-INJ-001",
        "name": "System Override Attempt",
        "pattern": r"(?i)\b(ignore|disregard|override|forget)\s+(all\s+)?(previous|prior|system|above)\s+(instructions|rules|prompts|limits)",
        "score": 85.0,
        "reason": "Direct prompt injection attempt to override system safety instructions.",
    },
    {
        "id": "Q-EXT-002",
        "name": "System Prompt Extraction",
        "pattern": r"(?i)\b(reveal|print|repeat|show|dump|output)\s+(the\s+)?(system\s+prompt|instructions|initial\s+prompt|developer\s+mode)",
        "score": 75.0,
        "reason": "Attempt to extract internal system prompt and control directives.",
    },
    {
        "id": "Q-PRV-003",
        "name": "Privilege Escalation Request",
        "pattern": r"(?i)\b(bypass|ignore|circumvent)\s+(permissions?|access\s+control|acl|role\s+limits|restrictions)",
        "score": 90.0,
        "reason": "Explicit directive to circumvent role-based access control.",
    },
    {
        "id": "Q-EXF-004",
        "name": "Confidential Exfiltration Intent",
        "pattern": r"(?i)\b(dump|leak|exfiltrate|reveal\s+all)\s+(confidential|secret|passwords?|credentials?|private\s+keys?)",
        "score": 80.0,
        "reason": "Bulk exfiltration attempt of sensitive credentials or confidential records.",
    },
    {
        "id": "Q-DEL-005",
        "name": "Adversarial Control Delimiters",
        "pattern": r"(<\/?system>|\[INST\]|\[\/INST\]|###\s*(Instruction|System):|<<SYS>>)",
        "score": 60.0,
        "reason": "Detection of structural delimiter injection syntax.",
    },
    {
        "id": "Q-HAR-006",
        "name": "Cross-User Probing",
        "pattern": r"(?i)\b(other\s+users?('s)?|another\s+user('s)?|all\s+users?('s)?)\s+(documents?|files?|chats?|salaries|data)",
        "score": 65.0,
        "reason": "Attempt to access data belonging to other user identities.",
    },
]


class QueryThreatAnalyzer:
    """
    Evaluates query intent for prompt injection, jailbreaks,
    and credential exfiltration patterns.
    """

    def __init__(self, patterns: List[Dict[str, Any]] = None):
        self.patterns = patterns or QUERY_PATTERNS

    def analyze(self, query: str) -> Tuple[float, List[str]]:
        """
        Calculates Query Threat Score S_q in range [0, 100]
        and returns explainable triggered reasons.
        """
        if not query or not query.strip():
            return 0.0, []

        triggered_reasons = []
        max_score = 0.0

        for pat in self.patterns:
            if re.search(pat["pattern"], query):
                triggered_reasons.append(f"[{pat['name']}] {pat['reason']}")
                if pat["score"] > max_score:
                    max_score = pat["score"]

        # Base query length or anomaly heuristics
        if len(query) > 1000:
            triggered_reasons.append("[Query Anomaly] Abnormally long query length exceeding 1000 characters.")
            max_score = max(max_score, 30.0)

        query_score = min(100.0, max_score)
        return query_score, triggered_reasons


# Singleton query analyzer instance
query_analyzer = QueryThreatAnalyzer()
