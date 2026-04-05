import random
import json
import re
from datetime import datetime

from app.models.sports_workspace import SPORTS_WORKSPACE_CONTRACT_VERSION, SportsWorkspace
from app.services.basketball_multi_agent import BasketballMultiAgentEngine
from app.services.sports_profiles import build_participant_profile
from app.services.sports_rule_packs import get_rule_pack
from app.services.sports_simulator import SportsSimulationState, SportsSimulationStatus


def _player(name: str, position: str, description: str, team_name: str, idx: int):
    team = {"name": team_name, "description": f"{team_name} basketball profile."}
    raw = {"name": name, "position": position, "description": description, "source_url": "https://example.com"}
    profile = build_participant_profile(raw, team, "player", team_focus=["play fast"], roster_index=idx)
    return {
        "id": f"{team_name}-{idx}",
        "name": name,
        "team": team_name,
        "role": position,
        "kind": "player",
        "profile": profile,
        "path": "",
        "profile_path": "",
    }


def _coach(name: str, team_name: str):
    team = {"name": team_name, "description": f"{team_name} basketball profile."}
    raw = {"name": name, "position": "Head Coach", "description": "Likes pace, spacing, and switching.", "source_url": "https://example.com"}
    profile = build_participant_profile(raw, team, "coach", team_focus=["play fast", "switch 1-4"], roster_index=0)
    return {
        "id": f"{team_name}-coach",
        "name": name,
        "team": team_name,
        "role": "Head Coach",
        "kind": "coach",
        "profile": profile,
        "path": "",
        "profile_path": "",
    }


class FakeLLMClient:
    def chat_json(self, messages, temperature=0.3, max_tokens=4096):
        content = messages[-1]["content"]
        allowed_actions = self._extract_json_list(content, "allowed_actions")
        valid_targets = self._extract_json_list(content, "valid_targets")
        action = self._pick_action(content, allowed_actions)
        target = valid_targets[0] if valid_targets else ""
        return {
            "action": action,
            "target": target,
            "confidence": 0.82,
            "note": "test-double",
        }

    def _extract_json_list(self, content: str, field: str):
        match = re.search(rf"{field}=(\[[^\n]*\])", content)
        if not match:
            return []
        return json.loads(match.group(1))

    def _pick_action(self, content: str, allowed_actions):
        if not allowed_actions:
            return ""
        if "agent_type=coach" in content:
            for option in ("spread_pnr", "switch", "man", "motion"):
                if option in allowed_actions:
                    return option
        if "agent_type=referee" in content:
            for option in ("play_on", "no_call"):
                if option in allowed_actions:
                    return option
        for option in (
            "come_to_ball",
            "get_open",
            "contain",
            "screen",
            "shoot",
            "secure",
            "box_out",
            "tag",
            "reset",
        ):
            if option in allowed_actions:
                return option
        return allowed_actions[0]


def test_basketball_engine_initializes_and_steps():
    home_team = {"name": "Metro City", "description": "Fast-paced offense."}
    away_team = {"name": "Harbor Town", "description": "Physical defensive team."}
    participants = [
        _coach("Home Coach", home_team["name"]),
        _coach("Away Coach", away_team["name"]),
    ]
    participants.extend(
        _player(f"Home Player {idx}", position, description, home_team["name"], idx)
        for idx, (position, description) in enumerate(
            [
                ("Point Guard", "Lead playmaker and transition engine."),
                ("Shooting Guard", "Movement shooter with pull-up range."),
                ("Small Forward", "Two-way wing who attacks closeouts."),
                ("Power Forward", "Connector forward and secondary passer."),
                ("Center", "Rim protector and offensive rebounder."),
                ("Guard", "Bench creator who changes pace."),
            ]
        )
    )
    participants.extend(
        _player(f"Away Player {idx}", position, description, away_team["name"], idx)
        for idx, (position, description) in enumerate(
            [
                ("Point Guard", "Steady organizer and point-of-attack defender."),
                ("Shooting Guard", "Spot-up wing and chaser."),
                ("Small Forward", "Switchable wing with slashing ability."),
                ("Power Forward", "Physical rebounder who screens hard."),
                ("Center", "Drop big and interior finisher."),
                ("Forward", "Bench energy piece."),
            ]
        )
    )

    workspace = SportsWorkspace(
        workspace_id="sports_test",
        contract_version=SPORTS_WORKSPACE_CONTRACT_VERSION,
        sport="Basketball",
        league="NBA",
        home_team_query=home_team["name"],
        away_team_query=away_team["name"],
        game_context="",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        home_team=home_team,
        away_team=away_team,
        participants=participants,
        rule_pack=get_rule_pack("basketball"),
    )
    state = SportsSimulationState(
        simulation_id="sim_test",
        workspace_id=workspace.workspace_id,
        status=SportsSimulationStatus.CREATED,
        home_team=home_team["name"],
        away_team=away_team["name"],
        sport="Basketball",
    )

    engine = BasketballMultiAgentEngine(llm_client=FakeLLMClient(), use_llm_agents=True)
    engine.initialize_state(workspace, state)

    assert state.simulation_mode == "basketball_llm_multi_agent"
    assert len(state.home_lineup) == 5
    assert len(state.away_lineup) == 5
    assert state.shot_clock == 24
    assert state.possession_phase == "inbound"
    assert all(participant.get("dossier_text") for participant in participants)

    event = engine.step(workspace, state, [], random.Random(7))

    assert event["phase"] == "inbound"
    assert event["action_type"] in {"inbound", "turnover"}
    assert state.current_segment in {"Q1", "Q2", "Q3", "Q4", "OT1"}
