from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class AgentState:
    src_text: str
    draft_translation: str = ""
    uncertain_words: List[str] = field(default_factory=list)
    dict_evidence: Dict[str, str] = field(default_factory=dict)
    final_translation: str = ""
    logs: List[str] = field(default_factory=list)