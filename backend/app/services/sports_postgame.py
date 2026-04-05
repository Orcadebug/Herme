"""
Post-game content generation service for sports simulations.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.sports_workspace import SportsWorkspace, SportsWorkspaceManager
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger

logger = get_logger("hermes.sports_postgame")


class SportsPostgameService:
    """Generate post-game content including press conferences, interviews, and analysis."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client

    def generate_postgame_content(self, workspace_id: str) -> Dict[str, Any]:
        """Generate and store post-game content for a workspace."""
        workspace = SportsWorkspaceManager.get_workspace(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace {workspace_id} not found")

        if not self.llm_client:
            raise RuntimeError("Postgame generation requires a configured LLM client")

        simulation_id = workspace.latest_simulation_id
        if not simulation_id:
            raise ValueError("Workspace has no completed simulation")

        state = self._load_state(workspace_id, simulation_id)
        events = self._load_events(workspace_id, simulation_id)

        if not state:
            raise ValueError("Simulation state not found")

        content = self._build_postgame(workspace, state, events)

        postgame_path = os.path.join(
            SportsWorkspaceManager.get_workspace_dir(workspace_id),
            "postgame.json",
        )
        os.makedirs(os.path.dirname(postgame_path), exist_ok=True)
        with open(postgame_path, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)

        logger.info("Postgame content generated for workspace %s", workspace_id)
        return content

    def get_postgame_content(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve existing post-game content."""
        postgame_path = os.path.join(
            SportsWorkspaceManager.get_workspace_dir(workspace_id),
            "postgame.json",
        )
        if not os.path.exists(postgame_path):
            return None
        with open(postgame_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_postgame(
        self,
        workspace: SportsWorkspace,
        state: Dict[str, Any],
        events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate post-game content using LLM."""
        home_name = state.get("home_team", "Home")
        away_name = state.get("away_team", "Away")
        home_score = state.get("home_score", 0)
        away_score = state.get("away_score", 0)
        winner = home_name if home_score > away_score else away_name

        game_summary = self._build_game_summary(state, events)
        key_events_text = self._format_key_events(events)

        try:
            payload = self.llm_client.chat_json(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a sports post-game analyst and reporter. Generate JSON with these exact keys: "
                            "coach_press_conference (object with winning_coach_quote and losing_coach_quote, "
                            "each having coach_name and quote), player_interviews (list of 2-3 objects with "
                            "player_name, team, quote), media_reaction (list of 3-4 strings), "
                            "statistical_breakdown (object with key_stats as list of strings), "
                            "game_ball_mvp (object with player_name, team, reason). Return JSON only."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Final Score: {home_name} {home_score} - {away_score} {away_name}\n"
                            f"Winner: {winner}\n"
                            f"Sport: {workspace.sport}\n"
                            f"Game summary:\n{game_summary}\n\n"
                            f"Key events:\n{key_events_text}\n\n"
                            "Generate post-game content based on this simulation."
                        ),
                    },
                ],
                temperature=0.5,
                max_tokens=800,
            )
        except Exception as exc:
            logger.warning("LLM postgame generation failed: %s", exc)
            payload = self._fallback_postgame(state, events, winner)

        return {
            "generated_at": datetime.now().isoformat(),
            "final_score": f"{home_name} {home_score} - {away_score} {away_name}",
            "winner": winner,
            "coach_press_conference": payload.get("coach_press_conference", {}),
            "player_interviews": payload.get("player_interviews", []),
            "media_reaction": payload.get("media_reaction", []),
            "statistical_breakdown": payload.get("statistical_breakdown", {}),
            "game_ball_mvp": payload.get("game_ball_mvp", {}),
        }

    def _build_game_summary(
        self,
        state: Dict[str, Any],
        events: List[Dict[str, Any]],
    ) -> str:
        """Build a concise game summary from state and events."""
        lines = []
        lines.append(
            f"{state.get('home_team', 'Home')} {state.get('home_score', 0)} - "
            f"{state.get('away_score', 0)} {state.get('away_team', 'Away')}"
        )

        scoring_players: Dict[str, int] = {}
        turnovers = 0
        fouls = 0
        for event in events:
            points = event.get("points", 0)
            actor = event.get("actor", "") or event.get("primary_actor", "")
            if actor and points > 0:
                scoring_players[actor] = scoring_players.get(actor, 0) + points
            if event.get("action_type") == "turnover":
                turnovers += 1
            if event.get("foul_type"):
                fouls += 1

        top_scorers = sorted(scoring_players.items(), key=lambda x: x[1], reverse=True)[
            :3
        ]
        if top_scorers:
            lines.append(
                "Top scorers: "
                + ", ".join(f"{name} ({pts}pts)" for name, pts in top_scorers)
            )

        lines.append(f"Turnovers: {turnovers}, Fouls: {fouls}")

        if state.get("quarter"):
            lines.append(
                f"Periods: Q{state['quarter']}"
                + (f" OT{state['overtime']}" if state.get("overtime") else "")
            )

        return "\n".join(lines)

    def _format_key_events(self, events: List[Dict[str, Any]]) -> str:
        """Format key events for the LLM prompt."""
        key_events = []
        for event in events[-15:]:
            play = event.get("play_by_play", "")
            points = event.get("points", 0)
            action = event.get("action_type", "")
            segment = event.get("segment", "")
            clock = event.get("clock", "")
            if play:
                key_events.append(
                    f"[{segment} {clock}] {action}: {play}"
                    + (f" (+{points})" if points > 0 else "")
                )
        return "\n".join(key_events) if key_events else "No detailed events available."

    def _load_state(
        self, workspace_id: str, simulation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Load simulation state from disk."""
        state_path = os.path.join(
            SportsWorkspaceManager.get_simulations_dir(workspace_id),
            simulation_id,
            "state.json",
        )
        if not os.path.exists(state_path):
            return None
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_events(
        self, workspace_id: str, simulation_id: str
    ) -> List[Dict[str, Any]]:
        """Load simulation events from disk."""
        events_path = os.path.join(
            SportsWorkspaceManager.get_simulations_dir(workspace_id),
            simulation_id,
            "events.json",
        )
        if not os.path.exists(events_path):
            return []
        with open(events_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _fallback_postgame(
        self,
        state: Dict[str, Any],
        events: List[Dict[str, Any]],
        winner: str,
    ) -> Dict[str, Any]:
        """Fallback post-game content without LLM."""
        home_name = state.get("home_team", "Home")
        away_name = state.get("away_team", "Away")
        home_coach = state.get("home_coach", "Coach")
        away_coach = state.get("away_coach", "Coach")
        is_home_winner = winner == home_name

        return {
            "coach_press_conference": {
                "winning_coach_quote": {
                    "coach_name": home_coach if is_home_winner else away_coach,
                    "quote": f"Proud of the effort tonight. The team executed well when it mattered.",
                },
                "losing_coach_quote": {
                    "coach_name": away_coach if is_home_winner else home_coach,
                    "quote": "We had our chances but couldn't close. Credit to them for making plays.",
                },
            },
            "player_interviews": [
                {
                    "player_name": "Top scorer",
                    "team": winner,
                    "quote": "We stayed focused and played our game. That's all we could ask for.",
                }
            ],
            "media_reaction": [
                f"{winner} delivers a solid performance at home.",
                "A competitive matchup that came down to execution.",
                "Both teams showed flashes of brilliance throughout.",
            ],
            "statistical_breakdown": {
                "key_stats": [
                    f"Final: {home_name} {state.get('home_score', 0)} - {state.get('away_score', 0)} {away_name}",
                    f"Team fouls: Home {state.get('home_team_fouls', 0)} - Away {state.get('away_team_fouls', 0)}",
                ]
            },
            "game_ball_mvp": {
                "player_name": "Team effort",
                "team": winner,
                "reason": "Balanced contribution across the roster in a hard-fought win.",
            },
        }
