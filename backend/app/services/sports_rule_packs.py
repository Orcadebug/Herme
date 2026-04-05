"""
Canonical sport rule packs for the production sports workflow.
"""

from copy import deepcopy
from typing import Any, Dict, List, Optional


_SPORT_RULE_PACKS: Dict[str, Dict[str, Any]] = {
    "basketball": {
        "sport": "Basketball",
        "step_unit": "phase",
        "target_steps": 320,
        "lineup_size": 5,
        "segments": ["Q1", "Q2", "Q3", "Q4"],
        "phases": [
            "inbound",
            "bring_up",
            "set_init",
            "first_action",
            "help_rotation",
            "shot_pass_turnover_foul",
            "rebound_or_deadball",
            "reset",
        ],
        "shot_clock": 24,
        "quarter_minutes": 12,
        "timeouts_per_team": 7,
        "bonus_threshold": 5,
        "foul_out_limit": 6,
        "max_overtimes": 2,
        "allowed_score_values": [0, 1, 2, 3, 4],
        "max_delta_per_step": 4,
        "validation_rules": [
            "Only one team may receive positive points on a single possession.",
            "Score changes must remain within basketball scoring values.",
            "Events must stay aligned with the current quarter and possession owner.",
            "The environment must enforce a single legal ball handler and five-player lineups.",
            "Shot clock, fouls, and dead-ball transitions must be coherent across phases.",
        ],
        "summary": "Phase-based basketball flow with shared environment state, bounded player actions, coach policies, and referee-controlled whistles.",
    },
    "soccer": {
        "sport": "Soccer",
        "step_unit": "phase",
        "target_steps": 36,
        "lineup_size": 11,
        "segments": ["1st Half", "2nd Half"],
        "allowed_score_values": [0, 1],
        "max_delta_per_step": 1,
        "validation_rules": [
            "Only one team may score in a single phase.",
            "Soccer phases may only change the score by 0 or 1.",
            "Events must remain in the active half and respect the current attacking side.",
        ],
        "summary": "Phase-based soccer flow with low-scoring transitions and tactical buildup.",
    },
    "american_football": {
        "sport": "American Football",
        "step_unit": "drive",
        "target_steps": 24,
        "lineup_size": 11,
        "segments": ["Q1", "Q2", "Q3", "Q4"],
        "allowed_score_values": [0, 2, 3, 6, 7, 8],
        "max_delta_per_step": 8,
        "validation_rules": [
            "Only one team may receive positive points on a single drive.",
            "Drive scoring must remain within football scoring values.",
            "Events must stay aligned with quarter order and current possession.",
        ],
        "summary": "Drive-based American football flow with quarter structure and high-leverage scoring swings.",
    },
}

_SPORT_ALIASES = {
    "basketball": "basketball",
    "soccer": "soccer",
    "association football": "soccer",
    "american football": "american_football",
    "gridiron football": "american_football",
}


def normalize_sport_key(value: str) -> Optional[str]:
    """Map user or provider sport strings to a supported internal key."""
    normalized = " ".join((value or "").strip().lower().split())
    if not normalized:
        return None
    if normalized in _SPORT_RULE_PACKS:
        return normalized
    return _SPORT_ALIASES.get(normalized)


def get_rule_pack(sport: str) -> Dict[str, Any]:
    """Return a deep copy of the canonical rule pack for a supported sport."""
    sport_key = normalize_sport_key(sport)
    if not sport_key or sport_key not in _SPORT_RULE_PACKS:
        raise ValueError(
            f"Unsupported sport '{sport}'. Supported sports: "
            f"{', '.join(item['sport'] for item in list_supported_sports())}"
        )
    return deepcopy(_SPORT_RULE_PACKS[sport_key])


def list_supported_sports() -> List[Dict[str, str]]:
    """Return supported sports for UI and API consumers."""
    return [
        {"key": key, "sport": value["sport"]}
        for key, value in _SPORT_RULE_PACKS.items()
    ]
