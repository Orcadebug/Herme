"""
Basketball multi-agent runtime with optional LLM-backed player, coach, and ref agents.
"""

from __future__ import annotations

import json
import os
import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..models.sports_workspace import SportsWorkspaceManager
from .sports_profiles import load_profile_markdown, render_profile_markdown


class BasketballMultiAgentEngine:
    """Shared-environment basketball simulation with bounded agent actions."""

    def __init__(self, llm_client=None, use_llm_agents: bool = False):
        self.llm_client = llm_client
        self.use_llm_agents = bool(use_llm_agents and llm_client)

    def initialize_state(self, workspace, state) -> None:
        participant_map = self._participant_map(workspace)
        home_players = [item for item in workspace.participants if item["kind"] == "player" and item["team"] == workspace.home_team["name"]]
        away_players = [item for item in workspace.participants if item["kind"] == "player" and item["team"] == workspace.away_team["name"]]
        home_coaches = [item for item in workspace.participants if item["kind"] == "coach" and item["team"] == workspace.home_team["name"]]
        away_coaches = [item for item in workspace.participants if item["kind"] == "coach" and item["team"] == workspace.away_team["name"]]

        lineup_size = int(workspace.rule_pack.get("lineup_size", 5))
        state.simulation_mode = "basketball_llm_multi_agent" if self.use_llm_agents else "basketball_multi_agent"
        state.target_steps = int(workspace.rule_pack.get("target_steps", 320))
        state.home_lineup = self._select_lineup(home_players, lineup_size)
        state.away_lineup = self._select_lineup(away_players, lineup_size)
        state.home_bench = [item["name"] for item in home_players if item["name"] not in state.home_lineup]
        state.away_bench = [item["name"] for item in away_players if item["name"] not in state.away_lineup]
        state.home_coach = home_coaches[0]["name"]
        state.away_coach = away_coaches[0]["name"]
        state.current_segment = "Q1"
        state.quarter = 1
        state.overtime = 0
        state.game_clock = self._seconds_to_clock(int(workspace.rule_pack.get("quarter_minutes", 12)) * 60)
        state.shot_clock = int(workspace.rule_pack.get("shot_clock", 24))
        state.possession_team = "home"
        state.possession_phase = "inbound"
        state.ball_handler = ""
        state.ball_zone = "backcourt"
        state.offense_set = self._coach_family_choice(participant_map[state.home_coach]["profile"], "offense_family_weights", random.Random(workspace.scenario.seed))
        state.defensive_scheme = self._coach_family_choice(participant_map[state.away_coach]["profile"], "defense_family_weights", random.Random(workspace.scenario.seed + 7))
        state.home_team_fouls = 0
        state.away_team_fouls = 0
        state.player_fouls = {
            item["name"]: 0
            for item in workspace.participants
            if item["kind"] == "player"
        }
        initial_fatigue = {"fresh": 0.08, "balanced": 0.15, "fatigued": 0.24}.get(workspace.scenario.fatigue, 0.15)
        state.player_fatigue = {
            item["name"]: round(initial_fatigue + (0.03 if item["profile"]["runtime_card"]["stamina"] < 0.9 else 0.0), 4)
            for item in workspace.participants
            if item["kind"] == "player"
        }
        state.player_hot_cold = {
            item["name"]: 0.0
            for item in workspace.participants
            if item["kind"] == "player"
        }
        state.home_timeouts = int(workspace.rule_pack.get("timeouts_per_team", 7))
        state.away_timeouts = int(workspace.rule_pack.get("timeouts_per_team", 7))
        state.pending_substitutions = {"home": [], "away": []}
        state.last_outcome = ""
        state.advantage_state = "neutral"
        state.game_finished = False
        self.validate_state(workspace, state)

    def step(self, workspace, state, recent_events: List[Any], rng: random.Random) -> Dict[str, Any]:
        self._participant_map(workspace)
        if state.game_finished:
            raise ValueError("Basketball game is already complete")

        start_segment = state.current_segment
        start_clock = state.game_clock
        start_phase = state.possession_phase
        start_home = state.home_score
        start_away = state.away_score
        context = self._build_context(workspace, state)

        phase = state.possession_phase or "inbound"
        if phase == "inbound":
            details = self._run_inbound(workspace, state, context, recent_events, rng)
        elif phase == "bring_up":
            details = self._run_bring_up(workspace, state, context, recent_events, rng)
        elif phase == "set_init":
            details = self._run_set_init(workspace, state, context, recent_events, rng)
        elif phase == "first_action":
            details = self._run_first_action(workspace, state, context, recent_events, rng)
        elif phase == "help_rotation":
            details = self._run_help_rotation(workspace, state, context, recent_events, rng)
        elif phase == "shot_pass_turnover_foul":
            details = self._run_shot_phase(workspace, state, context, recent_events, rng)
        elif phase == "rebound_or_deadball":
            details = self._run_rebound(workspace, state, context, recent_events, rng)
        else:
            details = self._run_reset(workspace, state, context, recent_events, rng)

        self._tick_fatigue(state)
        self._advance_period_if_needed(workspace, state)
        state.updated_at = datetime.now().isoformat()
        self.validate_state(workspace, state)

        actor = details.get("actor", "") or details.get("target", "")
        target = details.get("target", "")
        defender = details.get("defender", "")
        return {
            "segment": start_segment,
            "clock": start_clock,
            "offense_team": context["offense_side"],
            "primary_actor": actor,
            "secondary_actor": target if target and target != actor else defender,
            "coach": context["offense_coach_name"],
            "home_delta": state.home_score - start_home,
            "away_delta": state.away_score - start_away,
            "title": details["title"],
            "play_by_play": details["play_by_play"],
            "next_possession": state.possession_team,
            "warnings": details.get("warnings", []),
            "phase": start_phase,
            "action_type": details.get("action_type", start_phase),
            "actor": actor,
            "target": target,
            "defender": defender,
            "zone": details.get("zone", state.ball_zone),
            "outcome": details.get("outcome", ""),
            "points": max(state.home_score - start_home, state.away_score - start_away),
            "foul_type": details.get("foul_type", ""),
            "turnover_type": details.get("turnover_type", ""),
            "rebound_type": details.get("rebound_type", ""),
            "next_state_snapshot": self.snapshot_state(state),
        }

    def snapshot_state(self, state) -> Dict[str, Any]:
        return {
            "quarter": state.quarter,
            "overtime": state.overtime,
            "current_segment": state.current_segment,
            "game_clock": state.game_clock,
            "shot_clock": state.shot_clock,
            "possession_team": state.possession_team,
            "possession_phase": state.possession_phase,
            "ball_handler": state.ball_handler,
            "ball_zone": state.ball_zone,
            "offense_set": state.offense_set,
            "defensive_scheme": state.defensive_scheme,
            "home_score": state.home_score,
            "away_score": state.away_score,
            "home_lineup": list(state.home_lineup),
            "away_lineup": list(state.away_lineup),
            "home_bench": list(state.home_bench),
            "away_bench": list(state.away_bench),
            "home_team_fouls": state.home_team_fouls,
            "away_team_fouls": state.away_team_fouls,
            "player_fouls": dict(state.player_fouls),
            "home_timeouts": state.home_timeouts,
            "away_timeouts": state.away_timeouts,
            "player_fatigue": dict(state.player_fatigue),
            "player_hot_cold": dict(state.player_hot_cold),
            "pending_substitutions": {
                "home": list(state.pending_substitutions.get("home", [])),
                "away": list(state.pending_substitutions.get("away", [])),
            },
            "last_outcome": state.last_outcome,
            "advantage_state": state.advantage_state,
            "game_finished": state.game_finished,
        }

    def validate_state(self, workspace, state) -> None:
        lineup_size = int(workspace.rule_pack.get("lineup_size", 5))
        if len(state.home_lineup) != lineup_size or len(state.away_lineup) != lineup_size:
            raise ValueError("Basketball state requires five active players per lineup")
        if len(set(state.home_lineup)) != len(state.home_lineup) or len(set(state.away_lineup)) != len(state.away_lineup):
            raise ValueError("Lineups cannot contain duplicate players")
        if set(state.home_lineup) & set(state.home_bench):
            raise ValueError("Home lineup and bench must be disjoint")
        if set(state.away_lineup) & set(state.away_bench):
            raise ValueError("Away lineup and bench must be disjoint")
        if state.possession_team not in {"home", "away"}:
            raise ValueError("Possession team must be home or away")
        if state.possession_phase not in {
            "inbound",
            "bring_up",
            "set_init",
            "first_action",
            "help_rotation",
            "shot_pass_turnover_foul",
            "rebound_or_deadball",
            "reset",
            "final",
        }:
            raise ValueError(f"Unsupported possession phase '{state.possession_phase}'")
        offense_lineup = state.home_lineup if state.possession_team == "home" else state.away_lineup
        if state.ball_handler and state.ball_handler not in offense_lineup:
            raise ValueError("Ball handler must belong to the offense lineup")
        if state.shot_clock < 0 or state.shot_clock > 24:
            raise ValueError("Shot clock must stay between 0 and 24")
        if any(count < 0 for count in state.player_fouls.values()):
            raise ValueError("Player fouls cannot be negative")

    def _build_context(self, workspace, state) -> Dict[str, Any]:
        participant_map = self._participant_map(workspace)
        offense_side = state.possession_team
        defense_side = "away" if offense_side == "home" else "home"
        offense_lineup = list(state.home_lineup if offense_side == "home" else state.away_lineup)
        defense_lineup = list(state.away_lineup if offense_side == "home" else state.home_lineup)
        offense_team = state.home_team if offense_side == "home" else state.away_team
        defense_team = state.away_team if offense_side == "home" else state.home_team
        offense_coach_name = state.home_coach if offense_side == "home" else state.away_coach
        defense_coach_name = state.away_coach if offense_side == "home" else state.home_coach
        return {
            "participants": participant_map,
            "offense_side": offense_side,
            "defense_side": defense_side,
            "offense_lineup": offense_lineup,
            "defense_lineup": defense_lineup,
            "offense_team": offense_team,
            "defense_team": defense_team,
            "offense_coach_name": offense_coach_name,
            "defense_coach_name": defense_coach_name,
            "offense_coach": participant_map[offense_coach_name]["profile"],
            "defense_coach": participant_map[defense_coach_name]["profile"],
        }

    def _state_summary(self, workspace, state, context, recent_events: List[Any]) -> str:
        recent_lines = []
        for event in recent_events[-4:]:
            if isinstance(event, dict):
                recent_lines.append(f"- {event.get('phase', '')}: {event.get('play_by_play', '')}")
            else:
                recent_lines.append(f"- {getattr(event, 'phase', '')}: {getattr(event, 'play_by_play', '')}")
        if not recent_lines:
            recent_lines.append("- no recent events")
        return (
            f"quarter={state.current_segment} game_clock={state.game_clock} shot_clock={state.shot_clock}\n"
            f"score={state.home_team} {state.home_score} - {state.away_score} {state.away_team}\n"
            f"offense_team={context['offense_team']} defense_team={context['defense_team']}\n"
            f"possession_phase={state.possession_phase} ball_handler={state.ball_handler or 'none'} ball_zone={state.ball_zone}\n"
            f"offense_set={state.offense_set} defensive_scheme={state.defensive_scheme}\n"
            f"home_lineup={', '.join(state.home_lineup)}\n"
            f"away_lineup={', '.join(state.away_lineup)}\n"
            f"team_fouls=home:{state.home_team_fouls} away:{state.away_team_fouls}\n"
            f"scenario={json.dumps(workspace.scenario.to_dict(), ensure_ascii=False)}\n"
            f"recent_events:\n" + "\n".join(recent_lines)
        )

    def _normalize_choice(self, value: Any, allowed: List[str]) -> str:
        if value is None:
            return ""
        text = str(value).strip().lower().replace("-", "_").replace(" ", "_")
        alias_map = {item.lower().replace("-", "_").replace(" ", "_"): item for item in allowed}
        return alias_map.get(text, "")

    def _coerce_confidence(self, value: Any) -> float:
        try:
            result = float(value)
        except (TypeError, ValueError):
            return 0.5
        return max(0.0, min(1.0, result))

    def _ask_player_agent(
        self,
        workspace,
        state,
        context,
        recent_events: List[Any],
        player_name: str,
        role_context: str,
        allowed_actions: List[str],
        valid_targets: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if not self.use_llm_agents or not self.llm_client:
            return {}
        participant = context["participants"][player_name]
        fatigue = state.player_fatigue.get(player_name, 0.15)
        hot_cold = state.player_hot_cold.get(player_name, 0.0)
        body = (
            f"agent_type=player\n"
            f"name={player_name}\nteam={participant['team']}\nrole={participant.get('role', 'Player')}\n"
            f"role_context={role_context}\n"
            f"personal_state=fatigue:{fatigue:.3f} hot_cold:{hot_cold:.3f} fouls:{state.player_fouls.get(player_name, 0)}\n"
            f"allowed_actions={json.dumps(allowed_actions)}\n"
            f"valid_targets={json.dumps(valid_targets or [])}\n"
            f"shared_state:\n{self._state_summary(workspace, state, context, recent_events)}\n\n"
            f"dossier_markdown:\n{participant.get('dossier_text', '')}\n\n"
            "Return JSON with keys: action, target, confidence, note."
        )
        try:
            payload = self.llm_client.chat_json(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an autonomous basketball player agent. Stay in character from the supplied markdown dossier. "
                            "Choose exactly one action from the allowed_actions list. Do not narrate. Return JSON only."
                        ),
                    },
                    {"role": "user", "content": body},
                ],
                temperature=min(max(workspace.scenario.randomness, 0.1), 0.45),
                max_tokens=220,
            )
        except Exception:
            return {}
        action = self._normalize_choice(payload.get("action"), allowed_actions)
        target = str(payload.get("target") or "").strip()
        if valid_targets and target not in valid_targets:
            target = ""
        return {
            "action": action,
            "target": target,
            "confidence": self._coerce_confidence(payload.get("confidence")),
            "note": str(payload.get("note") or "").strip(),
        } if action else {}

    def _ask_coach_agent(
        self,
        workspace,
        state,
        context,
        recent_events: List[Any],
        coach_name: str,
        role_context: str,
        allowed_actions: List[str],
        valid_targets: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if not self.use_llm_agents or not self.llm_client:
            return {}
        participant = context["participants"][coach_name]
        body = (
            f"agent_type=coach\nname={coach_name}\nteam={participant['team']}\n"
            f"role_context={role_context}\n"
            f"allowed_actions={json.dumps(allowed_actions)}\n"
            f"valid_targets={json.dumps(valid_targets or [])}\n"
            f"shared_state:\n{self._state_summary(workspace, state, context, recent_events)}\n\n"
            f"dossier_markdown:\n{participant.get('dossier_text', '')}\n\n"
            "Return JSON with keys: action, target, confidence, note."
        )
        try:
            payload = self.llm_client.chat_json(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an autonomous basketball coach agent. Stay grounded in the supplied markdown dossier. "
                            "Choose exactly one action from allowed_actions. Return JSON only."
                        ),
                    },
                    {"role": "user", "content": body},
                ],
                temperature=min(max(workspace.scenario.randomness, 0.1), 0.35),
                max_tokens=220,
            )
        except Exception:
            return {}
        action = self._normalize_choice(payload.get("action"), allowed_actions)
        target = str(payload.get("target") or "").strip()
        if valid_targets and target not in valid_targets:
            target = ""
        return {
            "action": action,
            "target": target,
            "confidence": self._coerce_confidence(payload.get("confidence")),
            "note": str(payload.get("note") or "").strip(),
        } if action else {}

    def _ask_ref_agent(
        self,
        workspace,
        state,
        context,
        recent_events: List[Any],
        role_context: str,
        allowed_actions: List[str],
    ) -> Dict[str, Any]:
        if not self.use_llm_agents or not self.llm_client:
            return {}
        body = (
            f"agent_type=referee\n"
            f"role_context={role_context}\n"
            f"allowed_actions={json.dumps(allowed_actions)}\n"
            f"shared_state:\n{self._state_summary(workspace, state, context, recent_events)}\n\n"
            f"rule_pack={json.dumps(workspace.rule_pack, ensure_ascii=False)}\n\n"
            "Return JSON with keys: action, confidence, note."
        )
        try:
            payload = self.llm_client.chat_json(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are the officiating agent in a basketball simulation. "
                            "Call only from allowed_actions and keep the response to JSON."
                        ),
                    },
                    {"role": "user", "content": body},
                ],
                temperature=0.15,
                max_tokens=180,
            )
        except Exception:
            return {}
        action = self._normalize_choice(payload.get("action"), allowed_actions)
        return {
            "action": action,
            "confidence": self._coerce_confidence(payload.get("confidence")),
            "note": str(payload.get("note") or "").strip(),
        } if action else {}

    def _proposal_weight(self, proposal: Dict[str, Any], preferred: List[str]) -> float:
        if not proposal:
            return 0.0
        action = proposal.get("action", "")
        confidence = float(proposal.get("confidence", 0.5))
        bonus = 1.5 if action in preferred else 0.65
        return max(confidence * bonus, 0.01)

    def _select_from_proposals(
        self,
        rng: random.Random,
        proposals: Dict[str, Dict[str, Any]],
        preferred: List[str],
        fallback: str,
    ) -> str:
        weighted: Dict[str, float] = {}
        for name, proposal in proposals.items():
            weighted[name] = self._proposal_weight(proposal, preferred)
        if not weighted:
            return fallback
        choice = self._weighted_choice(rng, weighted)
        return choice or fallback

    def _choose_named_target(
        self,
        rng: random.Random,
        proposals: Dict[str, Dict[str, Any]],
        valid_targets: List[str],
    ) -> str:
        weighted: Dict[str, float] = {}
        for proposal in proposals.values():
            target = proposal.get("target", "")
            if target and target in valid_targets:
                weighted[target] = weighted.get(target, 0.0) + max(float(proposal.get("confidence", 0.5)), 0.05)
        if not weighted:
            return ""
        return self._weighted_choice(rng, weighted)

    def _participant_map(self, workspace) -> Dict[str, Dict[str, Any]]:
        participant_map: Dict[str, Dict[str, Any]] = {}
        for participant in workspace.participants:
            if not participant.get("profile"):
                profile = None
                if participant.get("profile_path"):
                    profile = SportsWorkspaceManager.read_json(participant["profile_path"])
                if not profile and participant.get("path"):
                    profile = load_profile_markdown(participant["path"])
                participant["profile"] = profile or {
                    "name": participant["name"],
                    "team": participant["team"],
                    "kind": participant["kind"],
                    "runtime_card": {"kind": participant["kind"]},
                }
            if not participant.get("dossier_text"):
                dossier_text = ""
                if participant.get("path") and os.path.exists(participant["path"]):
                    with open(participant["path"], "r", encoding="utf-8") as handle:
                        dossier_text = handle.read()
                else:
                    dossier_text = render_profile_markdown(participant["profile"])
                participant["dossier_text"] = dossier_text
            participant_map[participant["name"]] = participant
        return participant_map

    def _select_lineup(self, players: List[Dict[str, Any]], lineup_size: int) -> List[str]:
        scored = []
        for player in players:
            profile = player.get("profile") or {}
            card = profile.get("runtime_card", {})
            rotation_bonus = {"starter": 3.0, "sixth_man": 2.2, "rotation": 1.2, "bench": 0.6}.get(profile.get("rotation_role"), 1.0)
            score = rotation_bonus + (card.get("usage_factor", 0.5) * 2.5) + (card.get("defense_factor", 1.0) * 0.8)
            scored.append((player["name"], score, self._position_group(profile)))
        scored.sort(key=lambda item: item[1], reverse=True)

        lineup: List[str] = []
        needed_groups = ["guard", "wing", "big"]
        for group in needed_groups:
            candidate = next((name for name, _, player_group in scored if player_group == group and name not in lineup), None)
            if candidate:
                lineup.append(candidate)
        for name, _, _ in scored:
            if name in lineup:
                continue
            lineup.append(name)
            if len(lineup) >= lineup_size:
                break
        return lineup[:lineup_size]

    def _position_group(self, profile: Dict[str, Any]) -> str:
        archetype = str(profile.get("archetype") or "").lower()
        position = str(profile.get("position_label") or "").lower()
        if any(key in archetype for key in ("guard",)) or any(key in position for key in ("pg", "sg", "guard")):
            return "guard"
        if any(key in archetype for key in ("big", "rim", "stretch")) or any(key in position for key in ("center", "c", "pf")):
            return "big"
        return "wing"

    def _run_inbound(self, workspace, state, context, recent_events: List[Any], rng: random.Random) -> Dict[str, Any]:
        offense_proposals = {
            name: self._ask_player_agent(
                workspace,
                state,
                context,
                recent_events,
                name,
                "Choose how you participate in the inbound. One player should inbound, others should get open or screen.",
                ["inbound", "get_open", "come_to_ball", "screen", "space"],
                [player for player in context["offense_lineup"] if player != name],
            )
            for name in context["offense_lineup"]
        }
        defense_proposals = {
            name: self._ask_player_agent(
                workspace,
                state,
                context,
                recent_events,
                name,
                "Choose your defensive action on the inbound.",
                ["deny", "jump_lane", "switch", "contain", "tag"],
                context["offense_lineup"],
            )
            for name in context["defense_lineup"]
        }
        coach_call = self._ask_coach_agent(
            workspace,
            state,
            context,
            recent_events,
            context["offense_coach_name"],
            "Choose the offensive family you want after the inbound.",
            ["spread_pnr", "horns", "five_out", "post_split", "motion", "transition"],
        )
        target = self._choose_named_target(rng, offense_proposals, context["offense_lineup"])
        if not target:
            target = self._select_from_proposals(
                rng,
                {name: proposal for name, proposal in offense_proposals.items() if name != target},
                ["get_open", "come_to_ball"],
                self._select_ball_handler(context["participants"], context["offense_lineup"], rng),
            )
        inbounder = self._select_from_proposals(
            rng,
            {name: proposal for name, proposal in offense_proposals.items() if name != target},
            ["inbound"],
            self._select_inbounder(context["participants"], context["offense_lineup"], target, rng),
        )
        defender = self._select_from_proposals(
            rng,
            defense_proposals,
            ["jump_lane", "deny"],
            self._select_primary_defender(context["participants"], context["defense_lineup"], rng),
        )
        turnover_risk = 0.015 + (self._player_card(context["participants"], defender).get("defense_factor", 1.0) - 1.0) * 0.03
        turnover_risk += max(self._player_fatigue(state, inbounder) - 0.2, 0.0) * 0.1
        turnover_risk += 0.06 if defense_proposals.get(defender, {}).get("action") == "jump_lane" else 0.0
        if rng.random() < turnover_risk:
            self._advance_clocks(state, rng.randint(1, 2), shot_delta=1)
            state.possession_team = context["defense_side"]
            state.possession_phase = "reset"
            state.ball_handler = ""
            state.ball_zone = "frontcourt"
            state.shot_clock = 24
            state.last_outcome = "turnover"
            state.advantage_state = "neutral"
            return {
                "title": "Inbound Turnover",
                "play_by_play": f"{inbounder} tries to hit {target}, but {defender} jumps the passing lane for a live-ball steal.",
                "action_type": "turnover",
                "actor": inbounder,
                "target": target,
                "defender": defender,
                "zone": "backcourt",
                "outcome": "live_ball_turnover",
                "turnover_type": "bad_pass",
            }

        state.ball_handler = target
        state.ball_zone = "backcourt"
        state.offense_set = coach_call.get("action") or self._coach_family_choice(context["offense_coach"], "offense_family_weights", rng)
        state.defensive_scheme = self._coach_family_choice(context["defense_coach"], "defense_family_weights", rng)
        self._advance_clocks(state, rng.randint(1, 2), shot_delta=1)
        state.possession_phase = "first_action" if rng.random() < self._pace_bias(workspace, context["offense_coach"]) * 0.24 else "bring_up"
        state.last_outcome = "inbound_complete"
        state.advantage_state = "neutral"
        return {
            "title": "Inbound Completed",
            "play_by_play": f"{inbounder} triggers the possession and finds {target}, with {context['offense_coach_name']} signaling {state.offense_set.replace('_', ' ')}.",
            "action_type": "inbound",
            "actor": inbounder,
            "target": target,
            "defender": defender,
            "zone": "backcourt",
            "outcome": "inbound_complete",
        }

    def _run_bring_up(self, workspace, state, context, recent_events: List[Any], rng: random.Random) -> Dict[str, Any]:
        actor = state.ball_handler or self._select_ball_handler(context["participants"], context["offense_lineup"], rng)
        handler_call = self._ask_player_agent(
            workspace,
            state,
            context,
            recent_events,
            actor,
            "Choose how you bring the ball up against pressure.",
            ["push", "slow_set", "protect_ball", "attack_early"],
            [],
        )
        defender_proposals = {
            name: self._ask_player_agent(
                workspace,
                state,
                context,
                recent_events,
                name,
                "Choose how you defend the ball in the backcourt or early frontcourt.",
                ["press_ball", "contain", "shade_left", "shade_right"],
                [actor],
            )
            for name in context["defense_lineup"]
        }
        defender = self._select_from_proposals(
            rng,
            defender_proposals,
            ["press_ball", "contain"],
            self._select_primary_defender(context["participants"], context["defense_lineup"], rng),
        )
        pressure = self._player_card(context["participants"], defender).get("defense_factor", 1.0)
        turnover_risk = self._player_card(context["participants"], actor).get("turnover_risk", 0.12) * 0.45
        turnover_risk += max(pressure - 1.0, 0.0) * 0.08
        turnover_risk += max(self._player_fatigue(state, actor) - 0.24, 0.0) * 0.12
        if defender_proposals.get(defender, {}).get("action") == "press_ball":
            turnover_risk += 0.04
        if rng.random() < turnover_risk:
            self._advance_clocks(state, rng.randint(3, 4), shot_delta=3)
            state.possession_team = context["defense_side"]
            state.possession_phase = "reset"
            state.ball_handler = ""
            state.ball_zone = "frontcourt"
            state.shot_clock = 24
            state.last_outcome = "turnover"
            return {
                "title": "Backcourt Pressure",
                "play_by_play": f"{defender} turns up the pressure and forces {actor} into a costly backcourt turnover.",
                "action_type": "turnover",
                "actor": actor,
                "defender": defender,
                "zone": "backcourt",
                "outcome": "ball_pressure_turnover",
                "turnover_type": "ball_pressure",
            }

        self._advance_clocks(state, rng.randint(3, 5), shot_delta=4)
        state.ball_handler = actor
        state.ball_zone = "top"
        aggressive = handler_call.get("action") == "attack_early"
        reset_bias = handler_call.get("action") == "slow_set"
        if aggressive:
            state.possession_phase = "first_action"
        elif reset_bias:
            state.possession_phase = "set_init"
        else:
            state.possession_phase = "set_init" if rng.random() > self._pace_bias(workspace, context["offense_coach"]) * 0.25 else "first_action"
        state.last_outcome = "frontcourt_entry"
        return {
            "title": "Offense Flows Into Shape",
            "play_by_play": f"{actor} brings the ball over cleanly while {defender} shades the ball and the floor tilts toward the top of the arc.",
            "action_type": "advance",
            "actor": actor,
            "defender": defender,
            "zone": "top",
            "outcome": "frontcourt_entry",
        }

    def _run_set_init(self, workspace, state, context, recent_events: List[Any], rng: random.Random) -> Dict[str, Any]:
        actor = state.ball_handler or self._select_ball_handler(context["participants"], context["offense_lineup"], rng)
        off_ball_names = [name for name in context["offense_lineup"] if name != actor]
        partner_proposals = {
            name: self._ask_player_agent(
                workspace,
                state,
                context,
                recent_events,
                name,
                "Choose your off-ball role as the set is initiated.",
                ["screen", "lift", "space", "dive", "seal"],
                [actor],
            )
            for name in off_ball_names
        }
        target = self._select_from_proposals(
            rng,
            partner_proposals,
            ["screen", "dive", "seal"],
            self._select_screening_partner(context["participants"], context["offense_lineup"], actor, rng),
        )
        coach_offense = self._ask_coach_agent(
            workspace,
            state,
            context,
            recent_events,
            context["offense_coach_name"],
            "Pick the play family to initiate now.",
            ["spread_pnr", "horns", "five_out", "post_split", "motion", "transition"],
            [target],
        )
        coach_defense = self._ask_coach_agent(
            workspace,
            state,
            context,
            recent_events,
            context["defense_coach_name"],
            "Pick the defensive coverage for this action.",
            ["man", "switch", "drop", "hedge", "zone"],
            [],
        )
        state.offense_set = coach_offense.get("action") or self._coach_family_choice(context["offense_coach"], "offense_family_weights", rng)
        state.defensive_scheme = coach_defense.get("action") or self._coach_family_choice(context["defense_coach"], "defense_family_weights", rng)
        self._advance_clocks(state, rng.randint(2, 3), shot_delta=2)
        state.ball_zone = "slot" if state.offense_set in {"spread_pnr", "five_out", "motion"} else "elbow"
        state.possession_phase = "first_action"
        state.last_outcome = "set_called"
        return {
            "title": "Set Call",
            "play_by_play": f"{context['offense_coach_name']} calls {state.offense_set.replace('_', ' ')}, with {actor} initiating and {target} anchoring the action.",
            "action_type": "call_set",
            "actor": actor,
            "target": target,
            "zone": state.ball_zone,
            "outcome": state.offense_set,
        }

    def _run_first_action(self, workspace, state, context, recent_events: List[Any], rng: random.Random) -> Dict[str, Any]:
        actor = state.ball_handler or self._select_ball_handler(context["participants"], context["offense_lineup"], rng)
        actor_card = self._player_card(context["participants"], actor)
        off_ball_names = [name for name in context["offense_lineup"] if name != actor]
        off_ball_proposals = {
            name: self._ask_player_agent(
                workspace,
                state,
                context,
                recent_events,
                name,
                "Choose your off-ball action as the possession develops.",
                ["cut", "space", "screen", "relocate", "seal", "spot_up"],
                [actor],
            )
            for name in off_ball_names
        }
        defense_proposals = {
            name: self._ask_player_agent(
                workspace,
                state,
                context,
                recent_events,
                name,
                "Choose your on-ball or gap defensive action.",
                ["contain", "press", "strip", "force_help", "deny_middle"],
                [actor],
            )
            for name in context["defense_lineup"]
        }
        defender = self._select_from_proposals(
            rng,
            defense_proposals,
            ["press", "contain", "strip"],
            self._select_primary_defender(context["participants"], context["defense_lineup"], rng),
        )
        player_call = self._ask_player_agent(
            workspace,
            state,
            context,
            recent_events,
            actor,
            "Choose the first ball action from the current set.",
            ["drive", "swing", "handoff", "post_entry", "pick_and_roll", "pull_up"],
            off_ball_names,
        )
        target = player_call.get("target") if player_call.get("target") in off_ball_names else self._choose_named_target(rng, off_ball_proposals, off_ball_names)
        if not target and off_ball_names:
            target = self._select_from_proposals(
                rng,
                off_ball_proposals,
                ["cut", "screen", "spot_up", "seal"],
                self._select_action_target(context["participants"], context["offense_lineup"], actor, rng),
            )
        action = player_call.get("action")
        if not action:
            action_weights = {
                "drive": actor_card.get("rim_bias", 0.3) * actor_card.get("aggression", 1.0),
                "swing": actor_card.get("pass_bias", 0.3),
                "handoff": 0.16 if state.offense_set in {"motion", "five_out"} else 0.08,
                "post_entry": actor_card.get("post_bias", 0.12) + (0.08 if state.offense_set == "post_split" else 0.0),
                "pick_and_roll": 0.24 if state.offense_set in {"spread_pnr", "horns"} else 0.12,
                "pull_up": actor_card.get("three_bias", 0.2) * 0.4,
            }
            action = self._weighted_choice(rng, action_weights)
        turnover_risk = actor_card.get("turnover_risk", 0.12) * (0.34 if action in {"drive", "pick_and_roll"} else 0.22)
        turnover_risk += max(self._player_card(context["participants"], defender).get("defense_factor", 1.0) - 1.0, 0.0) * 0.05
        if defense_proposals.get(defender, {}).get("action") == "strip":
            turnover_risk += 0.05
        if rng.random() < turnover_risk:
            self._advance_clocks(state, rng.randint(2, 4), shot_delta=3)
            state.possession_team = context["defense_side"]
            state.possession_phase = "reset"
            state.ball_handler = ""
            state.ball_zone = "frontcourt"
            state.shot_clock = 24
            state.last_outcome = "turnover"
            state.advantage_state = "neutral"
            return {
                "title": "Action Disrupted",
                "play_by_play": f"{defender} sniffs out the {action.replace('_', ' ')} and strips {actor} before the action can unfold.",
                "action_type": "turnover",
                "actor": actor,
                "target": target,
                "defender": defender,
                "zone": state.ball_zone,
                "outcome": "forced_turnover",
                "turnover_type": action,
            }

        self._advance_clocks(state, rng.randint(2, 4), shot_delta=3)
        if action in {"swing", "handoff", "post_entry"} and target:
            state.ball_handler = target
        else:
            state.ball_handler = actor
        state.ball_zone = {
            "drive": "paint",
            "post_entry": "mid_post",
            "pull_up": "top",
            "pick_and_roll": "slot",
            "handoff": "wing",
            "swing": "wing",
        }[action]
        state.possession_phase = "shot_pass_turnover_foul" if action == "pull_up" else "help_rotation"
        state.last_outcome = action
        return {
            "title": "First Action",
            "play_by_play": f"{actor} triggers a {action.replace('_', ' ')}, forcing {defender} and the weak side to react.",
            "action_type": action,
            "actor": actor,
            "target": target,
            "defender": defender,
            "zone": state.ball_zone,
            "outcome": action,
        }

    def _run_help_rotation(self, workspace, state, context, recent_events: List[Any], rng: random.Random) -> Dict[str, Any]:
        actor = state.ball_handler or self._select_ball_handler(context["participants"], context["offense_lineup"], rng)
        help_proposals = {
            name: self._ask_player_agent(
                workspace,
                state,
                context,
                recent_events,
                name,
                "Choose your help-side rotation.",
                ["tag", "switch", "stunt", "dig", "late_help"],
                [actor],
            )
            for name in context["defense_lineup"]
        }
        defender = self._select_from_proposals(
            rng,
            help_proposals,
            ["switch", "tag", "stunt", "dig"],
            self._select_help_defender(context["participants"], context["defense_lineup"], rng),
        )
        scheme = state.defensive_scheme
        help_action = help_proposals.get(defender, {}).get("action")
        if not help_action:
            help_weights = {
                "tag": 0.24,
                "switch": 0.22 if scheme == "switch" else 0.08,
                "stunt": 0.2,
                "dig": 0.16 if state.ball_zone in {"mid_post", "paint"} else 0.08,
                "late_help": 0.16,
            }
            help_action = self._weighted_choice(rng, help_weights)
        if help_action == "switch":
            advantage = "switch_mismatch"
        elif help_action in {"tag", "stunt"}:
            advantage = "tagged"
        elif help_action == "dig":
            advantage = "paint_crowded"
        else:
            advantage = "scramble"
        self._advance_clocks(state, rng.randint(1, 2), shot_delta=1)
        state.possession_phase = "shot_pass_turnover_foul"
        state.advantage_state = advantage
        return {
            "title": "Defense Rotates",
            "play_by_play": f"{defender} shows {help_action.replace('_', ' ')} help out of the {scheme}, leaving the possession in a {advantage.replace('_', ' ')} state.",
            "action_type": "help_rotate",
            "actor": actor,
            "defender": defender,
            "zone": state.ball_zone,
            "outcome": advantage,
        }

    def _run_shot_phase(self, workspace, state, context, recent_events: List[Any], rng: random.Random) -> Dict[str, Any]:
        handler = state.ball_handler or self._select_ball_handler(context["participants"], context["offense_lineup"], rng)
        handler_card = self._player_card(context["participants"], handler)
        off_ball_names = [name for name in context["offense_lineup"] if name != handler]
        shot_call = self._ask_player_agent(
            workspace,
            state,
            context,
            recent_events,
            handler,
            "Choose the final action of the possession.",
            ["shoot", "pass", "reset"],
            off_ball_names,
        )
        defense_proposals = {
            name: self._ask_player_agent(
                workspace,
                state,
                context,
                recent_events,
                name,
                "Choose your contest on the shot or late-clock play.",
                ["contest", "body_up", "strip", "verticality", "foul"],
                [handler],
            )
            for name in context["defense_lineup"]
        }
        defender = self._select_from_proposals(
            rng,
            defense_proposals,
            ["contest", "body_up", "strip", "foul"],
            self._select_primary_defender(context["participants"], context["defense_lineup"], rng),
        )
        defender_card = self._player_card(context["participants"], defender)
        target = shot_call.get("target") if shot_call.get("target") in off_ball_names else ""

        if shot_call.get("action") == "pass" and target:
            receiver_call = self._ask_player_agent(
                workspace,
                state,
                context,
                recent_events,
                target,
                "You just received the ball late in the possession. Choose your immediate reaction.",
                ["shoot", "drive", "swing"],
                [name for name in context["offense_lineup"] if name not in {target}],
            )
            shooter = target
            shot_mode = receiver_call.get("action") or "shoot"
        elif shot_call.get("action") == "reset":
            shooter = handler
            shot_mode = "reset"
        else:
            shooter = handler
            shot_mode = shot_call.get("action") or "shoot"
        shooter_card = self._player_card(context["participants"], shooter)
        shot_zone, shot_value = self._choose_shot_location(shooter_card, state.ball_zone, state.advantage_state, rng)

        if shot_mode == "reset":
            self._advance_clocks(state, rng.randint(1, 2), shot_delta=1)
            state.ball_handler = handler
            state.possession_phase = "set_init"
            state.ball_zone = "top"
            state.last_outcome = "reset_ball"
            return {
                "title": "Reset Called",
                "play_by_play": f"{handler} pulls the ball back out and resets the action before forcing the shot.",
                "action_type": "reset_ball",
                "actor": handler,
                "target": target,
                "defender": defender,
                "zone": "top",
                "outcome": "reset_ball",
            }

        turnover_risk = shooter_card.get("turnover_risk", 0.12) * 0.24
        turnover_risk += max(defender_card.get("defense_factor", 1.0) - 1.0, 0.0) * 0.05
        if defense_proposals.get(defender, {}).get("action") == "strip":
            turnover_risk += 0.05
        if rng.random() < turnover_risk:
            self._advance_clocks(state, rng.randint(2, 3), shot_delta=2)
            state.possession_team = context["defense_side"]
            state.possession_phase = "reset"
            state.ball_handler = ""
            state.ball_zone = "frontcourt"
            state.shot_clock = 24
            state.last_outcome = "turnover"
            state.advantage_state = "neutral"
            return {
                "title": "Possession Lost",
                "play_by_play": f"{defender} crowds {shooter} into a late mistake, and the possession dies before the shot can get up.",
                "action_type": "turnover",
                "actor": shooter,
                "target": target or handler,
                "defender": defender,
                "zone": shot_zone,
                "outcome": "late_clock_turnover",
                "turnover_type": "strip_or_bad_handle",
            }

        contact = 0.1 + (0.12 if shot_zone in {"paint", "mid_post"} else 0.04)
        contact += max(shooter_card.get("aggression", 1.0) - 1.0, 0.0) * 0.18
        ref_call = self._ask_ref_agent(
            workspace,
            state,
            context,
            recent_events,
            (
                f"Potential contact on {shooter} by {defender} in zone={shot_zone}. "
                f"Defender action={defense_proposals.get(defender, {}).get('action', 'contest')}."
            ),
            ["no_call", "shooting_foul", "play_on"],
        )
        foul_called = (
            ref_call.get("action") == "shooting_foul"
            if ref_call
            else self._ref_whistle(workspace, contact, defender_card.get("foul_risk", 1.0), rng)
        )
        made_probability = self._shot_make_probability(workspace, state, shooter, shooter_card, defender_card, shot_zone)
        made = rng.random() < made_probability

        self._advance_clocks(state, rng.randint(2, 4), shot_delta=2)
        self._touch_hot_cold(state, shooter, 0.06 if made else -0.05)

        if foul_called and made:
            foul_points = shot_value + 1
            self._record_foul(state, context["defense_side"], defender)
            self._add_points(state, context["offense_side"], foul_points)
            state.possession_team = context["defense_side"]
            state.possession_phase = "reset"
            state.ball_handler = ""
            state.ball_zone = "backcourt"
            state.shot_clock = 24
            state.last_outcome = "and_one"
            state.advantage_state = "neutral"
            return {
                "title": "And-One Finish",
                "play_by_play": f"{shooter} absorbs contact from {defender}, finishes from {shot_zone}, and cashes the extra point.",
                "action_type": "shot",
                "actor": shooter,
                "target": target or handler,
                "defender": defender,
                "zone": shot_zone,
                "outcome": f"made_{shot_value}_plus_one",
                "foul_type": "shooting",
            }

        if foul_called:
            foul_points = self._free_throw_points(shot_value, rng)
            self._record_foul(state, context["defense_side"], defender)
            self._add_points(state, context["offense_side"], foul_points)
            state.possession_team = context["defense_side"]
            state.possession_phase = "reset"
            state.ball_handler = ""
            state.ball_zone = "backcourt"
            state.shot_clock = 24
            state.last_outcome = "shooting_foul"
            state.advantage_state = "neutral"
            return {
                "title": "Whistle On The Shot",
                "play_by_play": f"{defender} clips {shooter} on the attempt. The whistle comes, and {shooter} turns the trip into {foul_points} point{'s' if foul_points != 1 else ''}.",
                "action_type": "foul",
                "actor": shooter,
                "target": target or handler,
                "defender": defender,
                "zone": shot_zone,
                "outcome": f"shooting_foul_{foul_points}",
                "foul_type": "shooting",
            }

        if made:
            self._add_points(state, context["offense_side"], shot_value)
            state.possession_team = context["defense_side"]
            state.possession_phase = "reset"
            state.ball_handler = ""
            state.ball_zone = "backcourt"
            state.shot_clock = 24
            state.last_outcome = "made_shot"
            state.advantage_state = "neutral"
            assist_text = f" after the feed from {handler}" if target and handler != shooter else ""
            return {
                "title": "Basket",
                "play_by_play": f"{shooter} buries the {shot_value}-pointer from {shot_zone}{assist_text}.",
                "action_type": "shot",
                "actor": shooter,
                "target": target or handler,
                "defender": defender,
                "zone": shot_zone,
                "outcome": f"made_{shot_value}",
            }

        state.possession_phase = "rebound_or_deadball"
        state.ball_handler = ""
        state.ball_zone = shot_zone
        state.last_outcome = "missed_shot"
        return {
            "title": "Shot Missed",
            "play_by_play": f"{shooter} fires from {shot_zone}, but {defender} contests and the shot kicks off the rim.",
            "action_type": "shot",
            "actor": shooter,
            "target": target or handler,
            "defender": defender,
            "zone": shot_zone,
            "outcome": "missed_shot",
        }

    def _run_rebound(self, workspace, state, context, recent_events: List[Any], rng: random.Random) -> Dict[str, Any]:
        if state.last_outcome != "missed_shot":
            state.possession_phase = "reset"
            return {
                "title": "Dead Ball Reset",
                "play_by_play": "The play is dead and both sides reset their spacing for the next possession.",
                "action_type": "deadball",
                "zone": state.ball_zone,
                "outcome": "deadball",
            }

        offense_rebound_calls = {
            name: self._ask_player_agent(
                workspace,
                state,
                context,
                recent_events,
                name,
                "Choose your rebounding action after the miss.",
                ["crash", "tip", "get_back"],
                [],
            )
            for name in context["offense_lineup"]
        }
        defense_rebound_calls = {
            name: self._ask_player_agent(
                workspace,
                state,
                context,
                recent_events,
                name,
                "Choose your defensive rebounding action after the miss.",
                ["box_out", "secure", "leak_out"],
                [],
            )
            for name in context["defense_lineup"]
        }
        offense_strength = self._team_rebound_strength(context["participants"], context["offense_lineup"], context["offense_coach"], offense=True)
        defense_strength = self._team_rebound_strength(context["participants"], context["defense_lineup"], context["defense_coach"], offense=False)
        offense_strength += sum(0.12 for proposal in offense_rebound_calls.values() if proposal.get("action") in {"crash", "tip"})
        defense_strength += sum(0.12 for proposal in defense_rebound_calls.values() if proposal.get("action") in {"box_out", "secure"})
        offense_prob = max(0.12, min(0.42, offense_strength / (offense_strength + defense_strength)))

        if rng.random() < offense_prob:
            rebounder = self._select_from_proposals(
                rng,
                offense_rebound_calls,
                ["crash", "tip"],
                self._weighted_player(
                    context["participants"],
                    context["offense_lineup"],
                    rng,
                    lambda participant: participant["profile"]["runtime_card"].get("rebound_factor", 1.0),
                ),
            )
            state.possession_team = context["offense_side"]
            state.possession_phase = "first_action"
            state.ball_handler = rebounder
            state.ball_zone = "paint"
            state.shot_clock = min(state.shot_clock, 14)
            state.last_outcome = "offensive_rebound"
            state.advantage_state = "scramble"
            self._advance_clocks(state, rng.randint(1, 2), shot_delta=0)
            return {
                "title": "Offensive Board",
                "play_by_play": f"{rebounder} keeps the possession alive on the glass and turns the miss into a scramble opportunity.",
                "action_type": "rebound",
                "actor": rebounder,
                "zone": "paint",
                "outcome": "offensive_rebound",
                "rebound_type": "offensive",
            }

        rebounder = self._select_from_proposals(
            rng,
            defense_rebound_calls,
            ["secure", "box_out"],
            self._weighted_player(
                context["participants"],
                context["defense_lineup"],
                rng,
                lambda participant: participant["profile"]["runtime_card"].get("rebound_factor", 1.0),
            ),
        )
        state.possession_team = context["defense_side"]
        state.possession_phase = "reset"
        state.ball_handler = ""
        state.ball_zone = "backcourt"
        state.shot_clock = 24
        state.last_outcome = "defensive_rebound"
        state.advantage_state = "neutral"
        self._advance_clocks(state, rng.randint(1, 2), shot_delta=0)
        return {
            "title": "Defensive Rebound",
            "play_by_play": f"{rebounder} secures the stop and pulls the ball down to finish the possession.",
            "action_type": "rebound",
            "actor": rebounder,
            "zone": "paint",
            "outcome": "defensive_rebound",
            "rebound_type": "defensive",
        }

    def _run_reset(self, workspace, state, context, recent_events: List[Any], rng: random.Random) -> Dict[str, Any]:
        offense_side = state.possession_team
        defense_side = "away" if offense_side == "home" else "home"
        offense_coach_name = state.home_coach if offense_side == "home" else state.away_coach
        defense_coach_name = state.away_coach if offense_side == "home" else state.home_coach
        offense_coach = context["participants"][offense_coach_name]["profile"]
        defense_coach = context["participants"][defense_coach_name]["profile"]
        offense_call = self._ask_coach_agent(
            workspace,
            state,
            context,
            recent_events,
            offense_coach_name,
            "Choose the next offensive macro action before the inbound.",
            ["spread_pnr", "horns", "five_out", "post_split", "motion", "transition", "timeout", "substitute"],
        )
        defense_call = self._ask_coach_agent(
            workspace,
            state,
            context,
            recent_events,
            defense_coach_name,
            "Choose the next defensive macro action before the inbound.",
            ["man", "switch", "drop", "hedge", "zone", "timeout", "substitute"],
        )
        state.offense_set = offense_call.get("action") if offense_call.get("action") in {"spread_pnr", "horns", "five_out", "post_split", "motion", "transition"} else self._coach_family_choice(offense_coach, "offense_family_weights", rng)
        state.defensive_scheme = defense_call.get("action") if defense_call.get("action") in {"man", "switch", "drop", "hedge", "zone"} else self._coach_family_choice(defense_coach, "defense_family_weights", rng)
        state.ball_handler = ""
        state.ball_zone = "backcourt"
        state.shot_clock = 24
        state.possession_phase = "inbound"
        state.pending_substitutions = {
            "home": self._apply_substitutions(workspace, state, "home"),
            "away": self._apply_substitutions(workspace, state, "away"),
        }
        if offense_call.get("action") == "substitute":
            state.pending_substitutions[offense_side].extend(self._apply_substitutions(workspace, state, offense_side))
        if defense_call.get("action") == "substitute":
            state.pending_substitutions[defense_side].extend(self._apply_substitutions(workspace, state, defense_side))
        timeout_side = self._maybe_timeout(state, offense_side, recent_events, rng)
        if not timeout_side:
            if offense_call.get("action") == "timeout":
                timeout_side = offense_side
            elif defense_call.get("action") == "timeout":
                timeout_side = defense_side
        if timeout_side:
            if timeout_side == "home":
                state.home_timeouts = max(state.home_timeouts - 1, 0)
            else:
                state.away_timeouts = max(state.away_timeouts - 1, 0)
            return {
                "title": "Timeout Called",
                "play_by_play": f"{state.home_team if timeout_side == 'home' else state.away_team} calls time to settle the floor before the next inbound.",
                "action_type": "timeout",
                "zone": "deadball",
                "outcome": "timeout",
                "warnings": self._substitution_warnings(state),
            }

        substitutions = self._substitution_warnings(state)
        if substitutions:
            return {
                "title": "Lineups Adjust",
                "play_by_play": " ; ".join(substitutions),
                "action_type": "substitution",
                "zone": "deadball",
                "outcome": "substitution",
                "warnings": substitutions,
            }

        return {
            "title": "Teams Reset",
            "play_by_play": f"{offense_coach_name} resets into {state.offense_set.replace('_', ' ')}, while {defense_coach_name} readies {state.defensive_scheme}.",
            "action_type": "reset",
            "zone": "deadball",
            "outcome": "reset",
        }

    def _coach_family_choice(self, coach_profile: Dict[str, Any], field: str, rng: random.Random) -> str:
        weights = coach_profile.get("runtime_card", {}).get(field) or coach_profile.get(field) or {}
        return self._weighted_choice(rng, weights) if weights else "man"

    def _select_ball_handler(self, participants: Dict[str, Dict[str, Any]], lineup: List[str], rng: random.Random) -> str:
        return self._weighted_player(
            participants,
            lineup,
            rng,
            lambda participant: (
                participant["profile"]["runtime_card"].get("playmaking_factor", 0.5) * 1.6
                + participant["profile"]["runtime_card"].get("usage_factor", 0.5)
            ),
        )

    def _select_inbounder(self, participants: Dict[str, Dict[str, Any]], lineup: List[str], target: str, rng: random.Random) -> str:
        candidates = [name for name in lineup if name != target] or list(lineup)
        return self._weighted_player(
            participants,
            candidates,
            rng,
            lambda participant: max(0.2, 1.1 - participant["profile"]["runtime_card"].get("usage_factor", 0.6)),
        )

    def _select_primary_defender(self, participants: Dict[str, Dict[str, Any]], lineup: List[str], rng: random.Random) -> str:
        return self._weighted_player(
            participants,
            lineup,
            rng,
            lambda participant: participant["profile"]["runtime_card"].get("defense_factor", 1.0),
        )

    def _select_help_defender(self, participants: Dict[str, Dict[str, Any]], lineup: List[str], rng: random.Random) -> str:
        return self._weighted_player(
            participants,
            lineup,
            rng,
            lambda participant: participant["profile"]["runtime_card"].get("defense_factor", 1.0)
            + participant["profile"]["runtime_card"].get("rebound_factor", 1.0) * 0.2,
        )

    def _select_screening_partner(self, participants: Dict[str, Dict[str, Any]], lineup: List[str], actor: str, rng: random.Random) -> str:
        candidates = [name for name in lineup if name != actor]
        return self._weighted_player(
            participants,
            candidates or lineup,
            rng,
            lambda participant: 1.2 if self._position_group(participant["profile"]) == "big" else 0.7,
        )

    def _select_action_target(self, participants: Dict[str, Dict[str, Any]], lineup: List[str], actor: str, rng: random.Random) -> str:
        candidates = [name for name in lineup if name != actor]
        return self._weighted_player(
            participants,
            candidates or lineup,
            rng,
            lambda participant: participant["profile"]["runtime_card"].get("usage_factor", 0.5)
            + participant["profile"]["runtime_card"].get("three_bias", 0.2),
        )

    def _select_spacing_target(self, participants: Dict[str, Dict[str, Any]], lineup: List[str], actor: str, rng: random.Random) -> str:
        candidates = [name for name in lineup if name != actor]
        return self._weighted_player(
            participants,
            candidates or lineup,
            rng,
            lambda participant: participant["profile"]["runtime_card"].get("three_bias", 0.2)
            + participant["profile"]["runtime_card"].get("usage_factor", 0.5),
        )

    def _player_card(self, participants: Dict[str, Dict[str, Any]], name: str) -> Dict[str, Any]:
        return participants[name]["profile"]["runtime_card"]

    def _player_fatigue(self, state, name: str) -> float:
        return float(state.player_fatigue.get(name, 0.15))

    def _team_rebound_strength(self, participants, lineup: List[str], coach_profile: Dict[str, Any], *, offense: bool) -> float:
        total = sum(participants[name]["profile"]["runtime_card"].get("rebound_factor", 1.0) for name in lineup)
        crash_bias = {"low": 0.88, "balanced": 1.0, "high": 1.12}.get(coach_profile.get("crash_glass_bias", "balanced"), 1.0)
        return total * (crash_bias if offense else 1.0)

    def _choose_shot_location(self, shooter_card: Dict[str, Any], current_zone: str, advantage_state: str, rng: random.Random) -> Tuple[str, int]:
        perimeter_bias = shooter_card.get("three_bias", 0.2) + (0.08 if advantage_state == "scramble" else 0.0)
        interior_bias = shooter_card.get("rim_bias", 0.3) + (0.08 if advantage_state == "switch_mismatch" else 0.0)
        if current_zone in {"paint", "mid_post"} and interior_bias >= perimeter_bias:
            return ("paint", 2) if current_zone == "paint" else ("mid_post", 2)
        if rng.random() < perimeter_bias:
            return rng.choice(["wing", "corner", "top"]), 3
        if shooter_card.get("post_bias", 0.1) > 0.25 and rng.random() < 0.4:
            return "mid_post", 2
        return ("paint", 2) if interior_bias > 0.3 else ("elbow", 2)

    def _shot_make_probability(self, workspace, state, shooter_name: str, shooter_card, defender_card, zone: str) -> float:
        base = {
            "paint": 0.61,
            "mid_post": 0.48,
            "elbow": 0.43,
            "wing": 0.37,
            "corner": 0.39,
            "top": 0.35,
        }.get(zone, 0.42)
        base += (shooter_card.get("usage_factor", 0.5) - 0.6) * 0.05
        base += (state.player_hot_cold.get(shooter_name, 0.0)) * 0.04
        base -= max(state.player_fatigue.get(shooter_name, 0.15) - 0.2, 0.0) * 0.14
        base -= max(defender_card.get("defense_factor", 1.0) - 1.0, 0.0) * 0.08
        base += {
            "switch_mismatch": 0.05,
            "scramble": 0.04,
            "tagged": -0.03,
            "paint_crowded": -0.06,
        }.get(state.advantage_state, 0.0)
        randomness = float(workspace.scenario.randomness or 0.35)
        base += (randomness - 0.35) * 0.08
        return max(0.18, min(0.82, base))

    def _ref_whistle(self, workspace, contact: float, foul_risk: float, rng: random.Random) -> bool:
        officiating = {"tight": 1.24, "standard": 1.0, "lenient": 0.78}.get(workspace.scenario.officiating, 1.0)
        threshold = contact * foul_risk * officiating
        return rng.random() < max(0.04, min(0.55, threshold))

    def _free_throw_points(self, shot_value: int, rng: random.Random) -> int:
        if shot_value == 3:
            roll = rng.random()
            if roll < 0.58:
                return 3
            if roll < 0.82:
                return 2
            if roll < 0.95:
                return 1
            return 0
        roll = rng.random()
        if roll < 0.68:
            return 2
        if roll < 0.93:
            return 1
        return 0

    def _record_foul(self, state, defense_side: str, defender: str) -> None:
        state.player_fouls[defender] = state.player_fouls.get(defender, 0) + 1
        if defense_side == "home":
            state.home_team_fouls += 1
        else:
            state.away_team_fouls += 1

    def _add_points(self, state, side: str, points: int) -> None:
        if side == "home":
            state.home_score += points
        else:
            state.away_score += points

    def _tick_fatigue(self, state) -> None:
        for name in list(state.home_lineup) + list(state.away_lineup):
            state.player_fatigue[name] = round(min(0.95, state.player_fatigue.get(name, 0.15) + 0.0045), 4)

    def _touch_hot_cold(self, state, name: str, delta: float) -> None:
        state.player_hot_cold[name] = round(max(-1.0, min(1.0, state.player_hot_cold.get(name, 0.0) + delta)), 4)

    def _advance_clocks(self, state, game_seconds: int, *, shot_delta: int) -> None:
        game_remaining = max(0, self._clock_to_seconds(state.game_clock) - max(game_seconds, 0))
        state.game_clock = self._seconds_to_clock(game_remaining)
        state.shot_clock = max(0, min(24, state.shot_clock - max(shot_delta, 0)))

    def _advance_period_if_needed(self, workspace, state) -> None:
        if state.game_clock != "00:00":
            return
        state.home_team_fouls = 0
        state.away_team_fouls = 0
        state.ball_handler = ""
        state.ball_zone = "backcourt"
        state.shot_clock = int(workspace.rule_pack.get("shot_clock", 24))
        state.possession_phase = "reset" if not state.game_finished else "final"
        state.advantage_state = "neutral"
        if state.quarter < 4:
            state.quarter += 1
            state.current_segment = f"Q{state.quarter}"
            state.game_clock = self._seconds_to_clock(int(workspace.rule_pack.get("quarter_minutes", 12)) * 60)
            state.last_outcome = "period_break"
            return
        if state.home_score == state.away_score and state.overtime < int(workspace.rule_pack.get("max_overtimes", 2)):
            state.overtime += 1
            state.current_segment = f"OT{state.overtime}"
            state.game_clock = "05:00"
            state.target_steps += 24
            state.last_outcome = "overtime"
            return
        state.game_finished = True
        state.possession_phase = "final"
        state.last_outcome = "final"

    def _apply_substitutions(self, workspace, state, side: str) -> List[str]:
        participant_map = self._participant_map(workspace)
        lineup = state.home_lineup if side == "home" else state.away_lineup
        bench = state.home_bench if side == "home" else state.away_bench
        results: List[str] = []
        if not bench:
            return results

        foul_limit = int(workspace.rule_pack.get("foul_out_limit", 6))
        for current in list(lineup):
            fatigue = state.player_fatigue.get(current, 0.15)
            fouls = state.player_fouls.get(current, 0)
            if fatigue < 0.54 and fouls < foul_limit - 1:
                continue
            replacement = self._best_replacement(participant_map, current, bench)
            if not replacement:
                continue
            lineup[lineup.index(current)] = replacement
            bench.remove(replacement)
            bench.append(current)
            state.player_fatigue[current] = round(max(0.08, state.player_fatigue.get(current, 0.15) - 0.12), 4)
            results.append(f"{replacement} checks in for {current}")
            if len(results) >= 2:
                break
        return results

    def _best_replacement(self, participant_map: Dict[str, Dict[str, Any]], current: str, bench: List[str]) -> Optional[str]:
        current_group = self._position_group(participant_map[current]["profile"])
        candidates = []
        for bench_player in bench:
            profile = participant_map[bench_player]["profile"]
            card = profile["runtime_card"]
            score = 0.0
            if self._position_group(profile) == current_group:
                score += 1.0
            score += card.get("stamina", 1.0)
            score += card.get("usage_factor", 0.5) * 0.4
            candidates.append((bench_player, score))
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[1], reverse=True)
        return candidates[0][0]

    def _maybe_timeout(self, state, offense_side: str, recent_events: List[Any], rng: random.Random) -> Optional[str]:
        if offense_side == "home" and state.home_timeouts <= 0:
            return None
        if offense_side == "away" and state.away_timeouts <= 0:
            return None
        if len(recent_events) < 3:
            return None
        recent_points = 0
        for event in recent_events[-3:]:
            if offense_side == "home":
                recent_points += int(getattr(event, "away_delta", 0))
            else:
                recent_points += int(getattr(event, "home_delta", 0))
        if recent_points >= 6 and rng.random() < 0.45:
            return offense_side
        return None

    def _substitution_warnings(self, state) -> List[str]:
        warnings: List[str] = []
        for side in ("home", "away"):
            for text in state.pending_substitutions.get(side, []):
                warnings.append(text)
        return warnings

    def _pace_bias(self, workspace, coach_profile: Dict[str, Any]) -> float:
        scenario = {"slow": 0.84, "balanced": 1.0, "fast": 1.14}.get(workspace.scenario.pace, 1.0)
        coach = coach_profile.get("runtime_card", {}).get("pace_factor", 1.0)
        return scenario * coach

    def _weighted_player(self, participants, lineup: List[str], rng: random.Random, weight_fn) -> str:
        weights: Dict[str, float] = {}
        for name in lineup:
            participant = participants[name]
            weights[name] = max(float(weight_fn(participant)), 0.01)
        return self._weighted_choice(rng, weights)

    def _weighted_choice(self, rng: random.Random, weights: Dict[str, float]) -> str:
        cleaned = [(key, max(float(value), 0.0)) for key, value in weights.items()]
        total = sum(value for _, value in cleaned)
        if total <= 0:
            return cleaned[0][0]
        roll = rng.random() * total
        cursor = 0.0
        for key, value in cleaned:
            cursor += value
            if roll <= cursor:
                return key
        return cleaned[-1][0]

    def _clock_to_seconds(self, clock: str) -> int:
        try:
            minutes, seconds = clock.split(":")
            return max(int(minutes) * 60 + int(seconds), 0)
        except Exception:
            return 0

    def _seconds_to_clock(self, total_seconds: int) -> str:
        total_seconds = max(int(total_seconds), 0)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
