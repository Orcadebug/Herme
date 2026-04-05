"""
Sports commentator agent system.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger

logger = get_logger("hermes.sports_commentator_agents")

_COMMENTATOR_PROFILES = {
    "play_by_play": [
        {
            "name": "Kevin Harlan",
            "style": "factual, energetic, excited during big plays, concise on routine plays",
            "signature": "Clear, rapid-fire delivery that escalates with the action",
        },
        {
            "name": "Ian Eagle",
            "style": "smooth, professional, builds excitement naturally, measured on routine plays",
            "signature": "Polished voice that rises with the moment",
        },
        {
            "name": "Brian Anderson",
            "style": "enthusiastic, descriptive, paints the picture, brief on mundane plays",
            "signature": "Vivid play-by-play with escalating energy",
        },
    ],
    "color": [
        {
            "name": "Reggie Miller",
            "style": "analytical, opinionated, draws on playing experience, candid about mistakes",
            "signature": "Sharp shooter's perspective with strong opinions",
        },
        {
            "name": "JJ Redick",
            "style": "tactical, modern analytics-minded, breaks down schemes and reads",
            "signature": "Coach's-eye view with data-backed analysis",
        },
        {
            "name": "Doris Burke",
            "style": "insightful, balanced, focuses on matchups and adjustments, respectful but honest",
            "signature": "Deep tactical knowledge delivered with clarity",
        },
    ],
}

_BIG_PLAY_ACTIONS = {"shot", "turnover", "foul", "timeout", "substitution", "rebound"}
_BIG_PLAY_OUTCOMES = {
    "made_3",
    "made_4",
    "and_one",
    "shooting_foul",
    "offensive_rebound",
    "live_ball_turnover",
    "forced_turnover",
}


class CommentatorAgent:
    """A single commentator agent with a distinct broadcasting style."""

    def __init__(self, role: str, name: str, style: str, signature: str):
        self.role = role
        self.name = name
        self.style = style
        self.signature = signature

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "name": self.name,
            "style": self.style,
            "signature": self.signature,
        }


class SportsCommentatorTeam:
    """A broadcast team with a play-by-play announcer and a color commentator."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client
        self.pbp = self._create_commentator("play_by_play")
        self.color = self._create_commentator("color")

    def _create_commentator(self, role: str) -> CommentatorAgent:
        profiles = _COMMENTATOR_PROFILES.get(role, [])
        profile = (
            profiles[0]
            if profiles
            else {
                "name": "Announcer",
                "style": "professional",
                "signature": "Standard broadcast",
            }
        )
        return CommentatorAgent(
            role=role,
            name=profile["name"],
            style=profile["style"],
            signature=profile["signature"],
        )

    def generate_commentary(
        self,
        event: Dict[str, Any],
        game_state: Dict[str, Any],
        recent_events: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        commentary = []
        is_big_play = self._is_big_play(event)

        pbp_text = self._generate_pbp(event, game_state, recent_events, is_big_play)
        commentary.append(
            {
                "commentator_name": self.pbp.name,
                "commentary_text": pbp_text,
                "type": "play_by_play",
                "timestamp": datetime.now().isoformat(),
                "event_reference": {
                    "title": event.get("title", ""),
                    "actor": event.get("primary_actor") or event.get("actor", ""),
                    "points": event.get("points", 0),
                },
            }
        )

        if is_big_play:
            color_text = self._generate_color(event, game_state, recent_events)
            commentary.append(
                {
                    "commentator_name": self.color.name,
                    "commentary_text": color_text,
                    "type": "color",
                    "timestamp": datetime.now().isoformat(),
                    "event_reference": {
                        "title": event.get("title", ""),
                        "actor": event.get("primary_actor") or event.get("actor", ""),
                        "points": event.get("points", 0),
                    },
                }
            )

        return commentary

    def _is_big_play(self, event: Dict[str, Any]) -> bool:
        action_type = event.get("action_type", "") or ""
        outcome = event.get("outcome", "") or ""
        points = event.get("points", 0) or 0
        if action_type in _BIG_PLAY_ACTIONS:
            return True
        if outcome in _BIG_PLAY_OUTCOMES:
            return True
        if points >= 3:
            return True
        return False

    def _generate_pbp(
        self,
        event: Dict[str, Any],
        game_state: Dict[str, Any],
        recent_events: Optional[List[Dict[str, Any]]],
        is_big_play: bool,
    ) -> str:
        play_by_play = event.get("play_by_play", event.get("title", ""))
        if not self.llm_client:
            return self._pbp_fallback(event, game_state, is_big_play)

        score = f"{game_state.get('home_team', 'Home')} {game_state.get('home_score', 0)} - {game_state.get('away_score', 0)} {game_state.get('away_team', 'Away')}"
        segment = game_state.get("current_segment", "")
        clock = game_state.get("game_clock", "")

        try:
            if is_big_play:
                response = self.llm_client.chat(
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                f"You are {self.pbp.name}, a play-by-play announcer. "
                                f"Style: {self.pbp.style}. Signature: {self.pbp.signature}. "
                                "Write a brief play-by-play call (1-2 sentences). "
                                "Be factual but let your excitement show on big plays. "
                                "Do not include your name. Just the call."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Game: {score}\n"
                                f"Period: {segment} Clock: {clock}\n"
                                f"Play: {play_by_play}\n"
                                "Call this play."
                            ),
                        },
                    ],
                    temperature=0.6,
                    max_tokens=80,
                )
                return response.strip()
            else:
                return self._pbp_fallback(event, game_state, is_big_play)
        except Exception as exc:
            logger.warning("Play-by-play commentary failed: %s", exc)
            return self._pbp_fallback(event, game_state, is_big_play)

    def _pbp_fallback(
        self, event: Dict[str, Any], game_state: Dict[str, Any], is_big_play: bool
    ) -> str:
        play_by_play = event.get("play_by_play", event.get("title", ""))
        segment = game_state.get("current_segment", "")
        clock = game_state.get("game_clock", "")
        if segment and clock:
            return f"[{segment} {clock}] {play_by_play}"
        return play_by_play

    def _generate_color(
        self,
        event: Dict[str, Any],
        game_state: Dict[str, Any],
        recent_events: Optional[List[Dict[str, Any]]],
    ) -> str:
        if not self.llm_client:
            return self._color_fallback(event, game_state)

        play_by_play = event.get("play_by_play", event.get("title", ""))
        score = f"{game_state.get('home_team', 'Home')} {game_state.get('home_score', 0)} - {game_state.get('away_score', 0)} {game_state.get('away_team', 'Away')}"
        segment = game_state.get("current_segment", "")
        clock = game_state.get("game_clock", "")

        recent_summary = ""
        if recent_events:
            lines = []
            for ev in recent_events[-3:]:
                pbp = (
                    ev.get("play_by_play", "")
                    if isinstance(ev, dict)
                    else getattr(ev, "play_by_play", "")
                )
                if pbp:
                    lines.append(f"- {pbp}")
            if lines:
                recent_summary = "\n".join(lines)

        try:
            response = self.llm_client.chat(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are {self.color.name}, a color commentator. "
                            f"Style: {self.color.style}. Signature: {self.color.signature}. "
                            "Provide analytical insight on the play (1-2 sentences). "
                            "Focus on what the play reveals about strategy, execution, or matchups. "
                            "Be opinionated but grounded. Do not include your name."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Game: {score}\n"
                            f"Period: {segment} Clock: {clock}\n"
                            f"Play: {play_by_play}\n"
                            f"Recent context:\n{recent_summary}\n"
                            "Analyze this play."
                        ),
                    },
                ],
                temperature=0.5,
                max_tokens=100,
            )
            return response.strip()
        except Exception as exc:
            logger.warning("Color commentary failed: %s", exc)
            return self._color_fallback(event, game_state)

    def _color_fallback(self, event: Dict[str, Any], game_state: Dict[str, Any]) -> str:
        action_type = event.get("action_type", "")
        points = event.get("points", 0) or 0
        actor = event.get("primary_actor") or event.get("actor", "")

        if action_type == "shot" and points > 0:
            return f"Great execution by {actor}. That's {points} points on a well-run possession."
        if action_type == "turnover":
            return f"Costly turnover. The defense forced a bad decision there."
        if action_type == "foul":
            return f"Physical play. The referee had no choice but to blow the whistle."
        if action_type == "rebound":
            return f"Winning the glass is winning the game. That's effort basketball."
        return f"Interesting sequence. Both teams making adjustments."
