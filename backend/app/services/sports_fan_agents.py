"""
Sports fan agent reaction system.
"""

from __future__ import annotations

import json
import os
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger

logger = get_logger("hermes.sports_fan_agents")

FAN_ARCHETYPES = [
    "superfan_home",
    "superfan_away",
    "skeptic",
    "stats_nerd",
    "troll_fan",
    "neutral_analyst",
]

_ARCHETYPE_PERSONAS: Dict[str, Dict[str, Any]] = {
    "superfan_home": {
        "bio": "Die-hard home team fan who bleeds the team colors.",
        "personality": "passionate, loyal, overly optimistic, emotional",
        "tone": "excited, biased toward home team",
    },
    "superfan_away": {
        "bio": "Die-hard away team fan who travels to every road game.",
        "personality": "passionate, loyal, dismissive of home team, emotional",
        "tone": "excited, biased toward away team",
    },
    "skeptic": {
        "bio": "Has seen it all and trusts nothing until the final buzzer.",
        "personality": "cynical, cautious, unimpressed by hype",
        "tone": "doubtful, measured, dry humor",
    },
    "stats_nerd": {
        "bio": "Advanced analytics enthusiast who sees the game through numbers.",
        "personality": "analytical, detail-oriented, loves advanced metrics",
        "tone": "data-driven, precise, slightly pedantic",
    },
    "troll_fan": {
        "bio": "Here for the memes and the chaos. Loves to stir the pot.",
        "personality": "provocative, humorous, sarcastic, attention-seeking",
        "tone": "snarky, playful, intentionally inflammatory",
    },
    "neutral_analyst": {
        "bio": "Objective observer who appreciates good basketball from both sides.",
        "personality": "fair, thoughtful, appreciative of skill",
        "tone": "balanced, insightful, professional",
    },
}

_FAN_NAMES: Dict[str, List[str]] = {
    "superfan_home": [
        "Mike The Faithful",
        "HomeCourtHero",
        "BleedTheColors",
        "RideOrDie",
        "CourtSideCarl",
    ],
    "superfan_away": [
        "RoadWarrior",
        "AwayDayAndy",
        "TravelingFan",
        "OpposingForce",
        "VisitorVince",
    ],
    "skeptic": [
        "NotImpressed",
        "SeenItBefore",
        "RealistRay",
        "ShowMeTheRing",
        "ColdTakes",
    ],
    "stats_nerd": [
        "PER_Wizard",
        "TrueShooter",
        "BoxPlusMinus",
        "AdvancedAndy",
        "StatSheetSam",
    ],
    "troll_fan": [
        "TrashTalkTim",
        "MemeLord",
        "ChaosKevin",
        "HotTakeHannah",
        "TrollPatrol",
    ],
    "neutral_analyst": [
        "CourtVision",
        "BalancedBob",
        "HoopsScholar",
        "GameBreakdown",
        "NeutralNate",
    ],
}


class FanAgent:
    """A single fan agent with a persona."""

    def __init__(
        self, archetype: str, name: str, handle: str, team_allegiance: str = "neutral"
    ):
        self.archetype = archetype
        self.name = name
        self.handle = handle
        self.team_allegiance = team_allegiance
        persona_info = _ARCHETYPE_PERSONAS.get(archetype, {})
        self.bio = persona_info.get("bio", "A sports fan.")
        self.personality = persona_info.get("personality", "passionate")
        self.tone = persona_info.get("tone", "enthusiastic")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "archetype": self.archetype,
            "name": self.name,
            "handle": self.handle,
            "team_allegiance": self.team_allegiance,
            "bio": self.bio,
            "personality": self.personality,
            "tone": self.tone,
        }


class SportsFanAgentPool:
    """Manages a pool of fan agents that generate social media-style reactions."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client
        self._pool: List[FanAgent] = []
        self._reactions: Dict[str, List[Dict[str, Any]]] = {}
        self._init_pool()

    def _init_pool(self) -> None:
        for archetype in FAN_ARCHETYPES:
            names = _FAN_NAMES.get(archetype, ["Fan"])
            for name in names:
                handle = "@" + name.lower().replace(" ", "_").replace("'", "")
                allegiance = (
                    "home"
                    if "home" in archetype
                    else ("away" if "away" in archetype else "neutral")
                )
                self._pool.append(FanAgent(archetype, name, handle, allegiance))

    def _select_fans(
        self, game_state: Dict[str, Any], count: int = 4
    ) -> List[FanAgent]:
        scored_fans = []
        for fan in self._pool:
            weight = 1.0
            if fan.team_allegiance == "home":
                weight = 1.5
            elif fan.team_allegiance == "away":
                weight = 1.5
            elif fan.archetype == "neutral_analyst":
                weight = 1.2
            scored_fans.append((fan, weight))
        scored_fans.sort(key=lambda x: x[1], reverse=True)
        selected = [fan for fan, _ in scored_fans[:count]]
        random.shuffle(selected)
        return selected

    def generate_reaction(
        self,
        event: Dict[str, Any],
        game_state: Dict[str, Any],
        recent_events: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        if not self.llm_client:
            return self._generate_fallback_reactions(event, game_state)

        selected_fans = self._select_fans(game_state)
        recent_summary = ""
        if recent_events:
            recent_lines = []
            for ev in recent_events[-3:]:
                pbp = (
                    ev.get("play_by_play", "")
                    if isinstance(ev, dict)
                    else getattr(ev, "play_by_play", "")
                )
                if pbp:
                    recent_lines.append("- " + pbp)
            recent_summary = (
                "\n".join(recent_lines) if recent_lines else "No recent events"
            )

        reactions = []
        for fan in selected_fans:
            try:
                reaction_text = self._llm_reaction(
                    fan, event, game_state, recent_summary
                )
                sentiment = self._infer_sentiment(fan, game_state, event)
                reactions.append(
                    {
                        "fan_name": fan.name,
                        "handle": fan.handle,
                        "archetype": fan.archetype,
                        "reaction_text": reaction_text,
                        "sentiment": sentiment,
                        "timestamp": datetime.now().isoformat(),
                        "event_reference": {
                            "title": event.get("title", ""),
                            "actor": event.get("primary_actor")
                            or event.get("actor", ""),
                            "points": event.get("points", 0),
                        },
                    }
                )
            except Exception as exc:
                logger.warning(
                    "Fan agent %s failed to generate reaction: %s", fan.name, exc
                )
                fallback = self._single_fallback(fan, event, game_state)
                reactions.append(fallback)

        return reactions

    def _llm_reaction(
        self,
        fan: FanAgent,
        event: Dict[str, Any],
        game_state: Dict[str, Any],
        recent_summary: str,
    ) -> str:
        event_desc = event.get("play_by_play", event.get("title", "A play happened"))
        score = "{} {} - {} {}".format(
            game_state.get("home_team", "Home"),
            game_state.get("home_score", 0),
            game_state.get("away_score", 0),
            game_state.get("away_team", "Away"),
        )
        prompt = (
            "You are {} ({}), a {} fan.\n"
            "Bio: {}\n"
            "Personality: {}\n"
            "Tone: {}\n"
            "Team allegiance: {}\n\n"
            "Current game: {}\n"
            "Just happened: {}\n"
            "Recent context:\n{}\n\n"
            "Write a short social media-style reaction (1-3 sentences) to this play. "
            "Stay in character. Be specific about the play. "
            "Do not include your name or handle in the text - just the reaction."
        ).format(
            fan.name,
            fan.handle,
            fan.archetype.replace("_", " "),
            fan.bio,
            fan.personality,
            fan.tone,
            fan.team_allegiance,
            score,
            event_desc,
            recent_summary,
        )
        response = self.llm_client.chat(
            messages=[
                {
                    "role": "system",
                    "content": "You are a sports fan posting on social media. Keep it concise and in character.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=120,
        )
        return response.strip()

    def _infer_sentiment(
        self, fan: FanAgent, game_state: Dict[str, Any], event: Dict[str, Any]
    ) -> str:
        points = event.get("points", 0)
        action_type = event.get("action_type", "")
        if action_type == "turnover":
            if fan.team_allegiance == "home":
                return "negative"
            elif fan.team_allegiance == "away":
                return "positive"
            return "neutral"
        if action_type == "shot" and points > 0:
            if fan.team_allegiance == "home":
                return "positive"
            elif fan.team_allegiance == "away":
                return "negative"
            return "neutral"
        if action_type == "foul":
            return "negative"
        return "neutral"

    def _generate_fallback_reactions(
        self,
        event: Dict[str, Any],
        game_state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        selected_fans = self._select_fans(game_state, count=3)
        reactions = []
        for fan in selected_fans:
            reactions.append(self._single_fallback(fan, event, game_state))
        return reactions

    def _single_fallback(
        self, fan: FanAgent, event: Dict[str, Any], game_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        event_title = event.get("title", "A play")
        actor = event.get("primary_actor") or event.get("actor", "Someone")
        points = event.get("points", 0)
        action_type = event.get("action_type", "")

        if action_type == "shot" and points > 0:
            text = "{} with the {}-pointer! {}.".format(actor, points, event_title)
        elif action_type == "turnover":
            text = "Turnover! {}. {} loses it.".format(event_title, actor)
        elif action_type == "foul":
            text = "Whistle blows. {}.".format(event_title)
        else:
            text = "{} - {} involved.".format(event_title, actor)

        sentiment = self._infer_sentiment(fan, game_state, event)
        return {
            "fan_name": fan.name,
            "handle": fan.handle,
            "archetype": fan.archetype,
            "reaction_text": text,
            "sentiment": sentiment,
            "timestamp": datetime.now().isoformat(),
            "event_reference": {
                "title": event_title,
                "actor": actor,
                "points": points,
            },
        }

    def get_reactions(
        self,
        workspace_id: str,
        simulation_id: str,
        filter_by: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Load reactions from the reactions.jsonl file."""
        from ..models.sports_workspace import SportsWorkspaceManager

        sim_dir = os.path.join(
            SportsWorkspaceManager.get_simulations_dir(workspace_id), simulation_id
        )
        path = os.path.join(sim_dir, "reactions.jsonl")
        if not os.path.exists(path):
            return []

        reactions: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if filter_by is None:
                        reactions.append(data)
                    elif (
                        data.get("sentiment") == filter_by
                        or data.get("archetype") == filter_by
                    ):
                        reactions.append(data)
                except json.JSONDecodeError:
                    continue

        self._reactions[simulation_id] = reactions
        return reactions

    def store_reactions(
        self, simulation_id: str, reactions: List[Dict[str, Any]], workspace_id: str
    ) -> str:
        from ..models.sports_workspace import SportsWorkspaceManager

        sim_dir = os.path.join(
            SportsWorkspaceManager.get_simulations_dir(workspace_id), simulation_id
        )
        os.makedirs(sim_dir, exist_ok=True)
        path = os.path.join(sim_dir, "reactions.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            for reaction in reactions:
                f.write(json.dumps(reaction, ensure_ascii=False) + "\n")
        self._reactions.setdefault(simulation_id, []).extend(reactions)
        return path

    def load_reactions(
        self, workspace_id: str, simulation_id: str
    ) -> List[Dict[str, Any]]:
        from ..models.sports_workspace import SportsWorkspaceManager

        sim_dir = os.path.join(
            SportsWorkspaceManager.get_simulations_dir(workspace_id), simulation_id
        )
        path = os.path.join(sim_dir, "reactions.jsonl")
        if not os.path.exists(path):
            return []
        reactions = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    reactions.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        self._reactions[simulation_id] = reactions
        return reactions
        reactions = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    reactions.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        self._reactions[simulation_id] = reactions
        return reactions
