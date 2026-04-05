"""
Basketball persona dossier rendering and parsing helpers.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Tuple

import yaml


PROFILE_VERSION = 1
_FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def _clean_text(value: Any, default: str = "") -> str:
    return " ".join(str(value or default).strip().split())


def _clean_list(values: Any) -> List[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, list):
        return []
    cleaned: List[str] = []
    seen = set()
    for item in values:
        text = _clean_text(item)
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(text)
    return cleaned


def _lower_text(value: Any) -> str:
    return _clean_text(value).lower()


def _contains(text: str, *keywords: str) -> bool:
    return any(keyword in text for keyword in keywords)


def _enum_or_default(value: Any, allowed: List[str], default: str) -> str:
    cleaned = _lower_text(value)
    return cleaned if cleaned in allowed else default


def _normalize_weights(raw: Any, defaults: Dict[str, float]) -> Dict[str, float]:
    weights = {key: float(value) for key, value in defaults.items()}
    if isinstance(raw, dict):
        for key, value in raw.items():
            if key not in defaults:
                continue
            try:
                weights[key] = max(float(value), 0.0)
            except (TypeError, ValueError):
                continue
    total = sum(weights.values()) or 1.0
    return {key: round(value / total, 4) for key, value in weights.items()}


def _profile_sections(kind: str, compiled: Dict[str, Any], person: Dict[str, Any], team_info: Dict[str, Any]) -> Dict[str, str]:
    if kind == "coach":
        team_focus = ", ".join(compiled.get("team_focus", [])[:4]) or "balanced half-court execution"
        return {
            "Background": (
                f"{compiled['name']} coaches {team_info['name']}. "
                f"{_clean_text(person.get('description') or team_info.get('description') or 'Current head coach researched for this matchup.')}"
            ),
            "Coaching Identity": (
                f"Pace preference: {compiled['pace_preference']}. Rotation approach: {compiled['rotation_tightness']}. "
                f"Primary tactical emphasis: {team_focus}."
            ),
            "Offensive Preferences": (
                "Preferred families: "
                + ", ".join(
                    f"{name.replace('_', ' ')} {int(weight * 100)}%"
                    for name, weight in compiled["offense_family_weights"].items()
                )
                + "."
            ),
            "Defensive Preferences": (
                "Preferred coverages: "
                + ", ".join(
                    f"{name.replace('_', ' ')} {int(weight * 100)}%"
                    for name, weight in compiled["defense_family_weights"].items()
                )
                + f". Switch policy: {compiled['switch_policy']}. PnR coverage: {compiled['pnr_coverage']}."
            ),
            "Rotation Logic": (
                f"Substitution pattern: {compiled['substitution_pattern']}. "
                f"Timeout bias: {compiled['timeout_bias']}. "
                f"Foul tolerance: {compiled['foul_tolerance']}."
            ),
            "Adjustment Triggers": (
                "Adjust on foul trouble, prolonged cold stretches, defensive breakdowns, and pace mismatches. "
                "Use dead balls to stabilize matchups and redistribute touches."
            ),
            "Roleplaying Notes": (
                "Speak like a head coach making concise tactical calls. "
                "Reference pace, matchups, coverages, substitutions, and role discipline rather than narrating possessions."
            ),
            "Research Notes": _clean_text(team_info.get("research_notes"), "Live research-backed summary generated at planning time."),
        }

    preferred = ", ".join(compiled.get("preferred_zones", [])) or "top, wing, paint"
    avoid = ", ".join(compiled.get("avoid_zones", [])) or "no strong avoid zones"
    tags = ", ".join(compiled.get("play_tags", [])) or "connector"
    return {
        "Profile": (
            f"{compiled['name']} plays for {team_info['name']} as a {compiled['position_label']}. "
            f"{_clean_text(person.get('description'), 'Research provider returned a limited scouting note for this player.')}"
        ),
        "Playstyle": (
            f"Archetype: {compiled['archetype']}. Usage: {compiled['usage_band']}. "
            f"Decision style: {compiled['decision_style']}. Play tags: {tags}."
        ),
        "Offensive Tendencies": (
            f"Shot profile: {compiled['shot_profile']}. Playmaking: {compiled['playmaking_band']}. "
            f"Preferred zones: {preferred}. Avoid zones: {avoid}."
        ),
        "Defensive Tendencies": (
            f"Defense style: {compiled['defense_style']}. Rebounding style: {compiled['rebounding_style']}. "
            f"Foul tendency: {compiled['foul_tendency']}."
        ),
        "Transition Behavior": (
            f"Transition role leans {compiled['transition_role']}. "
            f"Stamina band: {compiled['stamina_band']}."
        ),
        "Late Clock Behavior": (
            f"In late-clock situations this player trends {compiled['late_clock_role']} with {compiled['decision_style']} risk tolerance."
        ),
        "Roleplaying Notes": (
            "Respond like a player describing reads, comfort zones, matchups, and role discipline. "
            "Stay grounded in the researched playstyle instead of generic star-player narration."
        ),
        "Research Notes": _clean_text(person.get("research_notes"), "Live research-backed summary generated at planning time."),
    }


def _player_defaults(person: Dict[str, Any], team_info: Dict[str, Any], roster_index: int) -> Dict[str, Any]:
    position = _lower_text(person.get("position"))
    description = _lower_text(person.get("description"))
    team_description = _lower_text(team_info.get("description"))
    text = " ".join(item for item in (position, description, team_description) if item)

    if _contains(text, "point guard", " pg ", " floor general", "lead guard"):
        archetype = "lead_guard"
        playmaking_band = "lead"
        defense_style = "point_of_attack"
        shot_profile = "balanced"
        preferred_zones = ["top", "slot", "paint"]
    elif _contains(text, "shooting guard", " sg ", "movement shooter", "sniper", "three-point"):
        archetype = "wing_scorer"
        playmaking_band = "secondary"
        defense_style = "switchable"
        shot_profile = "spot_up"
        preferred_zones = ["wing", "corner", "top"]
    elif _contains(text, "small forward", " sf ", "wing", "two-way"):
        archetype = "two_way_wing"
        playmaking_band = "secondary"
        defense_style = "switchable"
        shot_profile = "balanced"
        preferred_zones = ["wing", "corner", "slot"]
    elif _contains(text, "power forward", " pf ", "stretch", "forward"):
        archetype = "connector_forward" if _contains(text, "pass", "connector", "playmaker") else "stretch_big"
        playmaking_band = "connective"
        defense_style = "helper"
        shot_profile = "balanced" if _contains(text, "attack", "drive") else "spot_up"
        preferred_zones = ["slot", "corner", "elbow"]
    else:
        archetype = "rim_big"
        playmaking_band = "limited"
        defense_style = "rim_protector"
        shot_profile = "paint_finisher"
        preferred_zones = ["paint", "dunker", "elbow"]

    if _contains(text, "all-star", "star", "go-to", "high-usage", "leading scorer"):
        usage_band = "primary"
    elif _contains(text, "playmaker", "creator", "combo", "secondary scorer"):
        usage_band = "secondary"
    elif _contains(text, "starter", "rotation"):
        usage_band = "tertiary"
    else:
        usage_band = "low" if roster_index >= 8 else "tertiary"

    if roster_index < 5 or usage_band in {"primary", "secondary"}:
        rotation_role = "starter"
    elif roster_index == 5:
        rotation_role = "sixth_man"
    elif roster_index < 9:
        rotation_role = "rotation"
    else:
        rotation_role = "bench"

    if _contains(text, "sniper", "three-point", "shooter", "spacing"):
        shot_profile = "spot_up" if not _contains(text, "pull-up", "off-the-dribble") else "pull_up_heavy"
        preferred_zones = ["wing", "corner", "top"]
    elif _contains(text, "rim", "paint", "lob", "roller", "finisher"):
        shot_profile = "rim_pressure" if archetype != "rim_big" else "paint_finisher"
        preferred_zones = ["paint", "dunker"]
    elif _contains(text, "post", "interior", "hook"):
        shot_profile = "post_heavy"
        preferred_zones = ["mid_post", "paint", "elbow"]

    rebounding_style = "crash" if _contains(text, "rebound", "glass", "physical") or archetype in {"rim_big", "stretch_big"} else "positional"
    if _contains(text, "guard rebound", "push after rebound"):
        rebounding_style = "guard_glass"

    if _contains(text, "gambler", "steal", "disruptive"):
        defense_style = "gambler"
    elif _contains(text, "drop", "rim protector", "block"):
        defense_style = "rim_protector"
    elif _contains(text, "switch", "versatile", "two-way"):
        defense_style = "switchable"

    if _contains(text, "aggressive", "attacks", "relentless"):
        decision_style = "aggressive"
    elif _contains(text, "steady", "safe", "connector", "veteran"):
        decision_style = "conservative"
    else:
        decision_style = "balanced"

    if _contains(text, "foul prone", "physical", "aggressive defender"):
        foul_tendency = "high"
    elif archetype in {"rim_big", "stretch_big"}:
        foul_tendency = "medium"
    else:
        foul_tendency = "low"

    if _contains(text, "high motor", "stamina", "transition", "minutes eater"):
        stamina_band = "high"
    elif _contains(text, "limited", "injury", "veteran workload"):
        stamina_band = "low"
    else:
        stamina_band = "medium"

    late_clock_role = "shot-maker" if usage_band in {"primary", "secondary"} else "release valve"
    transition_role = "push" if _contains(text, "guard", "transition", "speed") else "fill_lane"
    play_tags = [archetype.replace("_", " ")]
    if shot_profile in {"spot_up", "pull_up_heavy"}:
        play_tags.append("perimeter spacing")
    if shot_profile in {"rim_pressure", "paint_finisher", "post_heavy"}:
        play_tags.append("paint pressure")
    if playmaking_band in {"lead", "secondary"}:
        play_tags.append("playmaking")
    if defense_style in {"switchable", "point_of_attack", "rim_protector"}:
        play_tags.append("defense")

    avoid_zones = ["midrange"] if shot_profile in {"spot_up", "paint_finisher"} else ["backcourt"]
    return {
        "profile_version": PROFILE_VERSION,
        "kind": "player",
        "name": _clean_text(person.get("name")),
        "team": _clean_text(team_info.get("name")),
        "position_label": _clean_text(person.get("position"), "Player"),
        "jersey": _clean_text(person.get("jersey")),
        "handedness": "unknown",
        "rotation_role": rotation_role,
        "archetype": archetype,
        "usage_band": usage_band,
        "shot_profile": shot_profile,
        "playmaking_band": playmaking_band,
        "defense_style": defense_style,
        "rebounding_style": rebounding_style,
        "foul_tendency": foul_tendency,
        "stamina_band": stamina_band,
        "decision_style": decision_style,
        "transition_role": transition_role,
        "late_clock_role": late_clock_role,
        "preferred_zones": preferred_zones,
        "avoid_zones": avoid_zones,
        "play_tags": _clean_list(play_tags),
        "source_urls": _clean_list(person.get("source_urls") or person.get("source_url")),
        "research_confidence": "medium",
    }


def _coach_defaults(person: Dict[str, Any], team_info: Dict[str, Any], team_focus: List[str] | None = None) -> Dict[str, Any]:
    description = _lower_text(person.get("description") or team_info.get("description"))
    focus_text = " ".join(_clean_list(team_focus))
    combined = " ".join(item for item in (description, focus_text.lower()) if item)

    pace_preference = "fast" if _contains(combined, "transition", "pace", "push", "tempo") else "slow" if _contains(combined, "grind", "half-court", "control") else "balanced"
    rotation_tightness = "tight" if _contains(combined, "starters", "short bench", "heavy minutes") else "deep" if _contains(combined, "depth", "bench", "waves") else "balanced"
    substitution_pattern = "hot_hand" if _contains(combined, "hot hand", "ride the") else "early_stagger" if _contains(combined, "stagger", "balance lineups") else "starters_heavy" if rotation_tightness == "tight" else "hockey_shifts"
    switch_policy = "aggressive" if _contains(combined, "switch", "versatile") else "avoid" if _contains(combined, "drop", "rim protection") else "matchup"
    pnr_coverage = "ice" if _contains(combined, "ice", "side pick-and-roll") else "hedge" if _contains(combined, "hedge", "show") else "switch" if switch_policy == "aggressive" else "drop"
    crash_glass_bias = "high" if _contains(combined, "rebound", "glass", "second chance") else "low" if _contains(combined, "get back", "transition defense") else "balanced"
    foul_tolerance = "low" if _contains(combined, "discipline", "avoid fouls") else "high" if _contains(combined, "physical", "aggressive") else "medium"
    timeout_bias = "proactive" if _contains(combined, "settle", "runs", "stop momentum") else "late" if _contains(combined, "save timeouts", "endgame") else "balanced"

    offense_defaults = {
        "spread_pnr": 0.24,
        "horns": 0.16,
        "five_out": 0.14,
        "post_split": 0.12,
        "motion": 0.18,
        "transition": 0.16,
    }
    defense_defaults = {
        "man": 0.35,
        "switch": 0.2,
        "drop": 0.25,
        "hedge": 0.1,
        "zone": 0.1,
    }
    if pace_preference == "fast":
        offense_defaults["transition"] += 0.12
        offense_defaults["spread_pnr"] += 0.06
    if _contains(combined, "spacing", "shoot", "five-out"):
        offense_defaults["five_out"] += 0.15
        offense_defaults["motion"] += 0.08
    if _contains(combined, "post", "interior", "size", "big"):
        offense_defaults["post_split"] += 0.16
        offense_defaults["horns"] += 0.08
    if switch_policy == "aggressive":
        defense_defaults["switch"] += 0.22
    if pnr_coverage == "drop":
        defense_defaults["drop"] += 0.18
    if _contains(combined, "zone", "pack paint"):
        defense_defaults["zone"] += 0.18

    return {
        "profile_version": PROFILE_VERSION,
        "kind": "coach",
        "name": _clean_text(person.get("name")),
        "team": _clean_text(team_info.get("name")),
        "role": _clean_text(person.get("position"), "Head Coach"),
        "pace_preference": pace_preference,
        "rotation_tightness": rotation_tightness,
        "substitution_pattern": substitution_pattern,
        "offense_family_weights": _normalize_weights(None, offense_defaults),
        "defense_family_weights": _normalize_weights(None, defense_defaults),
        "switch_policy": switch_policy,
        "pnr_coverage": pnr_coverage,
        "crash_glass_bias": crash_glass_bias,
        "foul_tolerance": foul_tolerance,
        "timeout_bias": timeout_bias,
        "source_urls": _clean_list(person.get("source_urls") or person.get("source_url") or team_info.get("source_url")),
        "research_confidence": "medium",
        "team_focus": _clean_list(team_focus),
    }


def build_participant_profile(
    person: Dict[str, Any],
    team_info: Dict[str, Any],
    kind: str,
    *,
    team_focus: List[str] | None = None,
    roster_index: int = 0,
) -> Dict[str, Any]:
    if kind == "coach":
        compiled = _coach_defaults(person, team_info, team_focus=team_focus)
    else:
        compiled = _player_defaults(person, team_info, roster_index)
    compiled["sections"] = _profile_sections(kind, compiled, person, team_info)
    compiled["runtime_card"] = build_runtime_card(compiled)
    return compiled


def build_runtime_card(profile: Dict[str, Any]) -> Dict[str, Any]:
    kind = _enum_or_default(profile.get("kind"), ["player", "coach"], "player")
    if kind == "coach":
        pace_factor = {"slow": 0.9, "balanced": 1.0, "fast": 1.12}[profile.get("pace_preference", "balanced")]
        rotation_factor = {"tight": 0.82, "balanced": 1.0, "deep": 1.14}[profile.get("rotation_tightness", "balanced")]
        timeout_factor = {"proactive": 1.2, "balanced": 1.0, "late": 0.85}[profile.get("timeout_bias", "balanced")]
        return {
            "kind": "coach",
            "pace_factor": pace_factor,
            "rotation_factor": rotation_factor,
            "timeout_factor": timeout_factor,
            "offense_family_weights": _normalize_weights(
                profile.get("offense_family_weights"),
                {
                    "spread_pnr": 0.24,
                    "horns": 0.16,
                    "five_out": 0.14,
                    "post_split": 0.12,
                    "motion": 0.18,
                    "transition": 0.16,
                },
            ),
            "defense_family_weights": _normalize_weights(
                profile.get("defense_family_weights"),
                {
                    "man": 0.35,
                    "switch": 0.2,
                    "drop": 0.25,
                    "hedge": 0.1,
                    "zone": 0.1,
                },
            ),
        }

    usage_factor = {"primary": 1.0, "secondary": 0.82, "tertiary": 0.62, "low": 0.42}[profile.get("usage_band", "tertiary")]
    playmaking_factor = {"lead": 1.0, "secondary": 0.76, "connective": 0.55, "limited": 0.3}[profile.get("playmaking_band", "limited")]
    aggression = {"aggressive": 1.08, "balanced": 1.0, "conservative": 0.88}[profile.get("decision_style", "balanced")]
    stamina = {"high": 1.1, "medium": 1.0, "low": 0.86}[profile.get("stamina_band", "medium")]
    foul_risk = {"low": 0.88, "medium": 1.0, "high": 1.18}[profile.get("foul_tendency", "medium")]
    rebound = {"crash": 1.15, "positional": 1.0, "guard_glass": 0.92}[profile.get("rebounding_style", "positional")]
    defense = {
        "point_of_attack": 1.06,
        "switchable": 1.04,
        "helper": 0.98,
        "rim_protector": 1.1,
        "gambler": 1.02,
        "drop_big": 1.0,
    }.get(profile.get("defense_style"), 1.0)
    shot_profile = profile.get("shot_profile", "balanced")
    three_bias = 0.42 if shot_profile in {"spot_up", "pull_up_heavy"} else 0.14 if shot_profile in {"paint_finisher", "post_heavy"} else 0.28
    rim_bias = 0.48 if shot_profile in {"rim_pressure", "paint_finisher"} else 0.2 if shot_profile == "spot_up" else 0.32
    post_bias = 0.44 if shot_profile == "post_heavy" else 0.12
    return {
        "kind": "player",
        "usage_factor": round(usage_factor, 4),
        "playmaking_factor": round(playmaking_factor, 4),
        "aggression": round(aggression, 4),
        "stamina": round(stamina, 4),
        "foul_risk": round(foul_risk, 4),
        "rebound_factor": round(rebound, 4),
        "defense_factor": round(defense, 4),
        "three_bias": round(three_bias, 4),
        "rim_bias": round(rim_bias, 4),
        "post_bias": round(post_bias, 4),
        "pass_bias": round(min(playmaking_factor * 0.72, 0.9), 4),
        "turnover_risk": round(max(0.08, 0.24 - (playmaking_factor * 0.09)), 4),
    }


def render_profile_markdown(profile: Dict[str, Any]) -> str:
    profile = normalize_profile(profile)
    sections = profile.pop("sections")
    frontmatter = {key: value for key, value in profile.items() if key != "runtime_card"}
    yaml_block = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
    title = frontmatter.get("name", "Profile")
    ordered_sections = sections.items()
    body = [f"# {title}", ""]
    for heading, content in ordered_sections:
        body.append(f"## {heading}")
        body.append("")
        body.append(_clean_text(content, "Unavailable"))
        body.append("")
    profile["sections"] = sections
    return f"---\n{yaml_block}\n---\n\n" + "\n".join(body).rstrip() + "\n"


def parse_profile_markdown(content: str) -> Dict[str, Any]:
    text = content or ""
    frontmatter: Dict[str, Any] = {}
    body = text
    match = _FRONT_MATTER_RE.match(text)
    if match:
        loaded = yaml.safe_load(match.group(1)) or {}
        if isinstance(loaded, dict):
            frontmatter = loaded
        body = text[match.end():]

    sections: Dict[str, str] = {}
    current_heading = ""
    current_lines: List[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if current_heading:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = _clean_text(line[3:])
            current_lines = []
            continue
        if current_heading:
            current_lines.append(line)
    if current_heading:
        sections[current_heading] = "\n".join(current_lines).strip()

    frontmatter["sections"] = sections
    return normalize_profile(frontmatter)


def load_profile_markdown(path: str) -> Dict[str, Any]:
    if not path or not os.path.exists(path):
        raise ValueError(f"Profile dossier does not exist: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        return parse_profile_markdown(handle.read())


def normalize_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(profile or {})
    kind = _enum_or_default(normalized.get("kind"), ["player", "coach"], "player")
    normalized["profile_version"] = int(normalized.get("profile_version") or PROFILE_VERSION)
    normalized["kind"] = kind
    normalized["name"] = _clean_text(normalized.get("name"), "Unknown")
    normalized["team"] = _clean_text(normalized.get("team"), "Unknown Team")
    normalized["source_urls"] = _clean_list(normalized.get("source_urls"))
    normalized["research_confidence"] = _enum_or_default(normalized.get("research_confidence"), ["low", "medium", "high"], "medium")
    normalized["sections"] = normalized.get("sections") if isinstance(normalized.get("sections"), dict) else {}

    if kind == "coach":
        normalized["role"] = _clean_text(normalized.get("role"), "Head Coach")
        normalized["pace_preference"] = _enum_or_default(normalized.get("pace_preference"), ["slow", "balanced", "fast"], "balanced")
        normalized["rotation_tightness"] = _enum_or_default(normalized.get("rotation_tightness"), ["tight", "balanced", "deep"], "balanced")
        normalized["substitution_pattern"] = _enum_or_default(
            normalized.get("substitution_pattern"),
            ["early_stagger", "hockey_shifts", "starters_heavy", "hot_hand"],
            "early_stagger",
        )
        normalized["switch_policy"] = _enum_or_default(normalized.get("switch_policy"), ["avoid", "matchup", "aggressive"], "matchup")
        normalized["pnr_coverage"] = _enum_or_default(normalized.get("pnr_coverage"), ["drop", "switch", "hedge", "ice", "blitz", "mixed"], "drop")
        normalized["crash_glass_bias"] = _enum_or_default(normalized.get("crash_glass_bias"), ["low", "balanced", "high"], "balanced")
        normalized["foul_tolerance"] = _enum_or_default(normalized.get("foul_tolerance"), ["low", "medium", "high"], "medium")
        normalized["timeout_bias"] = _enum_or_default(normalized.get("timeout_bias"), ["proactive", "balanced", "late"], "balanced")
        normalized["team_focus"] = _clean_list(normalized.get("team_focus"))
        normalized["offense_family_weights"] = _normalize_weights(
            normalized.get("offense_family_weights"),
            {
                "spread_pnr": 0.24,
                "horns": 0.16,
                "five_out": 0.14,
                "post_split": 0.12,
                "motion": 0.18,
                "transition": 0.16,
            },
        )
        normalized["defense_family_weights"] = _normalize_weights(
            normalized.get("defense_family_weights"),
            {
                "man": 0.35,
                "switch": 0.2,
                "drop": 0.25,
                "hedge": 0.1,
                "zone": 0.1,
            },
        )
    else:
        normalized["position_label"] = _clean_text(normalized.get("position_label"), "Player")
        normalized["jersey"] = _clean_text(normalized.get("jersey"))
        normalized["handedness"] = _clean_text(normalized.get("handedness"), "unknown")
        normalized["rotation_role"] = _enum_or_default(normalized.get("rotation_role"), ["starter", "sixth_man", "rotation", "bench"], "rotation")
        normalized["archetype"] = _clean_text(normalized.get("archetype"), "connector_forward")
        normalized["usage_band"] = _enum_or_default(normalized.get("usage_band"), ["primary", "secondary", "tertiary", "low"], "tertiary")
        normalized["shot_profile"] = _enum_or_default(
            normalized.get("shot_profile"),
            ["balanced", "rim_pressure", "pull_up_heavy", "spot_up", "post_heavy", "paint_finisher", "offscreen"],
            "balanced",
        )
        normalized["playmaking_band"] = _enum_or_default(normalized.get("playmaking_band"), ["lead", "secondary", "connective", "limited"], "limited")
        normalized["defense_style"] = _enum_or_default(
            normalized.get("defense_style"),
            ["point_of_attack", "switchable", "helper", "rim_protector", "gambler", "drop_big"],
            "helper",
        )
        normalized["rebounding_style"] = _enum_or_default(normalized.get("rebounding_style"), ["crash", "positional", "guard_glass"], "positional")
        normalized["foul_tendency"] = _enum_or_default(normalized.get("foul_tendency"), ["low", "medium", "high"], "medium")
        normalized["stamina_band"] = _enum_or_default(normalized.get("stamina_band"), ["high", "medium", "low"], "medium")
        normalized["decision_style"] = _enum_or_default(normalized.get("decision_style"), ["conservative", "balanced", "aggressive"], "balanced")
        normalized["transition_role"] = _enum_or_default(normalized.get("transition_role"), ["push", "fill_lane", "trail", "rim_run"], "fill_lane")
        normalized["late_clock_role"] = _enum_or_default(normalized.get("late_clock_role"), ["shot-maker", "release valve", "screener"], "release valve")
        normalized["preferred_zones"] = _clean_list(normalized.get("preferred_zones"))
        normalized["avoid_zones"] = _clean_list(normalized.get("avoid_zones"))
        normalized["play_tags"] = _clean_list(normalized.get("play_tags"))

    normalized["runtime_card"] = build_runtime_card(normalized)
    return normalized


def profile_json_filename(markdown_path: str) -> str:
    base, _ = os.path.splitext(markdown_path)
    return f"{base}.json"


def parse_frontmatter_and_body(content: str) -> Tuple[Dict[str, Any], str]:
    parsed = parse_profile_markdown(content)
    sections = parsed.pop("sections", {})
    body = "\n".join(f"## {heading}\n\n{section}".strip() for heading, section in sections.items())
    parsed["sections"] = sections
    return parsed, body
