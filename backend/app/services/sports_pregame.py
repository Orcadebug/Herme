"""
Pre-game content generation service for sports simulations.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.sports_workspace import SportsWorkspace, SportsWorkspaceManager
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger

logger = get_logger("hermes.sports_pregame")


class SportsPregameService:
    """Generate pre-game content including storylines, predictions, and matchups."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client

    def generate_pregame_content(self, workspace_id: str) -> Dict[str, Any]:
        """Generate and store pre-game content for a workspace."""
        workspace = SportsWorkspaceManager.get_workspace(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace {workspace_id} not found")

        if not self.llm_client:
            raise RuntimeError("Pregame generation requires a configured LLM client")

        content = self._build_pregame(workspace)

        pregame_path = os.path.join(
            SportsWorkspaceManager.get_workspace_dir(workspace_id),
            "pregame.json",
        )
        os.makedirs(os.path.dirname(pregame_path), exist_ok=True)
        with open(pregame_path, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)

        logger.info("Pregame content generated for workspace %s", workspace_id)
        return content

    def get_pregame_content(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve existing pre-game content."""
        pregame_path = os.path.join(
            SportsWorkspaceManager.get_workspace_dir(workspace_id),
            "pregame.json",
        )
        if not os.path.exists(pregame_path):
            return None
        with open(pregame_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_pregame(self, workspace: SportsWorkspace) -> Dict[str, Any]:
        """Generate pre-game content using LLM with workspace context."""
        home_team = workspace.home_team or {}
        away_team = workspace.away_team or {}
        home_name = home_team.get("name", workspace.home_team_query)
        away_name = away_team.get("name", workspace.away_team_query)

        research_context = self._build_research_context(workspace)
        scenario_context = json.dumps(workspace.scenario.to_dict(), ensure_ascii=False)

        try:
            payload = self.llm_client.chat_json(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a sports pre-game analyst. Generate JSON with these exact keys: "
                            "key_storylines (list of 3-5 strings), media_predictions (object with "
                            "predicted_winner, predicted_spread, confidence), key_matchups (list of "
                            "objects with player1, player2, description), what_to_watch (list of 3-5 strings). "
                            "Return JSON only."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Matchup: {home_name} vs {away_name}\n"
                            f"Sport: {workspace.sport}\n"
                            f"League: {workspace.league}\n"
                            f"Scenario: {scenario_context}\n"
                            f"Research context:\n{research_context}\n\n"
                            "Generate compelling pre-game content based on this matchup."
                        ),
                    },
                ],
                temperature=0.5,
                max_tokens=600,
            )
        except Exception as exc:
            logger.warning("LLM pregame generation failed: %s", exc)
            payload = self._fallback_pregame(home_name, away_name, workspace)

        return {
            "generated_at": datetime.now().isoformat(),
            "home_team": home_name,
            "away_team": away_name,
            "sport": workspace.sport,
            "league": workspace.league,
            "key_storylines": payload.get("key_storylines", []),
            "media_predictions": payload.get("media_predictions", {}),
            "key_matchups": payload.get("key_matchups", []),
            "what_to_watch": payload.get("what_to_watch", []),
        }

    def _build_research_context(self, workspace: SportsWorkspace) -> str:
        """Build context string from workspace research data."""
        lines = []
        if workspace.matchup_summary:
            lines.append(f"Matchup summary: {workspace.matchup_summary}")

        home_team = workspace.home_team or {}
        away_team = workspace.away_team or {}
        if home_team.get("description"):
            lines.append(f"{home_team['name']}: {home_team['description']}")
        if away_team.get("description"):
            lines.append(f"{away_team['name']}: {away_team['description']}")

        participants = workspace.participants or []
        coaches = [p for p in participants if p.get("kind") == "coach"]
        for coach in coaches:
            if coach.get("description"):
                lines.append(
                    f"Coach {coach['name']} ({coach['team']}): {coach['description']}"
                )

        if workspace.source_links:
            lines.append(f"Sources: {', '.join(workspace.source_links[:5])}")

        return "\n".join(lines) if lines else "Limited research data available."

    def _fallback_pregame(
        self,
        home_name: str,
        away_name: str,
        workspace: SportsWorkspace,
    ) -> Dict[str, Any]:
        """Fallback pre-game content without LLM."""
        return {
            "key_storylines": [
                f"{home_name} looks to defend home court against {away_name}",
                f"Key battle in the paint will decide this matchup",
                f"Coaching adjustments could be the difference maker",
            ],
            "media_predictions": {
                "predicted_winner": home_name,
                "predicted_spread": "close game",
                "confidence": "medium",
            },
            "key_matchups": [
                {
                    "player1": f"{home_name} starting lineup",
                    "player2": f"{away_name} starting lineup",
                    "description": "The opening tip sets the tone for the game",
                }
            ],
            "what_to_watch": [
                "Pace of play and transition defense",
                "Bench production and depth",
                "Free throw shooting in close moments",
            ],
        }
