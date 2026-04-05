"""
Sports match simulation runtime.
"""

import json
import os
import random
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ..models.sports_workspace import (
    SPORTS_WORKSPACE_CONTRACT_VERSION,
    SportsWorkspace,
    SportsWorkspaceManager,
    SportsWorkspaceStatus,
)
from .basketball_multi_agent import BasketballMultiAgentEngine
from .sports_rule_packs import normalize_sport_key
from .sports_fan_agents import SportsFanAgentPool
from .sports_commentator_agents import SportsCommentatorTeam
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger

logger = get_logger("hermes.sports_simulator")


class SportsSimulationStatus(str, Enum):
    """Simulation lifecycle."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SportsEvent:
    """A single structured game event."""

    step: int
    segment: str
    clock: str
    offense_team: str
    primary_actor: str
    secondary_actor: str
    coach: str
    home_delta: int
    away_delta: int
    title: str
    play_by_play: str
    next_possession: str
    warnings: List[str] = field(default_factory=list)
    phase: str = ""
    action_type: str = ""
    actor: str = ""
    target: str = ""
    defender: str = ""
    zone: str = ""
    outcome: str = ""
    points: int = 0
    foul_type: str = ""
    turnover_type: str = ""
    rebound_type: str = ""
    next_state_snapshot: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SportsSimulationState:
    """Persisted state for a sports match simulation."""

    simulation_id: str
    workspace_id: str
    status: SportsSimulationStatus
    home_team: str
    away_team: str
    sport: str
    current_step: int = 0
    target_steps: int = 0
    current_segment: str = ""
    possession_team: str = "home"
    home_score: int = 0
    away_score: int = 0
    events_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None
    home_lineup: List[str] = field(default_factory=list)
    away_lineup: List[str] = field(default_factory=list)
    home_bench: List[str] = field(default_factory=list)
    away_bench: List[str] = field(default_factory=list)
    home_coach: str = ""
    away_coach: str = ""
    simulation_mode: str = "legacy"
    quarter: int = 1
    overtime: int = 0
    game_clock: str = ""
    shot_clock: int = 0
    possession_phase: str = ""
    ball_handler: str = ""
    ball_zone: str = ""
    offense_set: str = ""
    defensive_scheme: str = ""
    home_team_fouls: int = 0
    away_team_fouls: int = 0
    player_fouls: Dict[str, int] = field(default_factory=dict)
    home_timeouts: int = 0
    away_timeouts: int = 0
    player_fatigue: Dict[str, float] = field(default_factory=dict)
    player_hot_cold: Dict[str, float] = field(default_factory=dict)
    pending_substitutions: Dict[str, List[str]] = field(default_factory=dict)
    last_outcome: str = ""
    advantage_state: str = ""
    game_finished: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = (
            self.status.value
            if isinstance(self.status, SportsSimulationStatus)
            else self.status
        )
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SportsSimulationState":
        status = data.get("status", SportsSimulationStatus.CREATED.value)
        if isinstance(status, str):
            status = SportsSimulationStatus(status)
        return cls(
            simulation_id=data["simulation_id"],
            workspace_id=data["workspace_id"],
            status=status,
            home_team=data.get("home_team", ""),
            away_team=data.get("away_team", ""),
            sport=data.get("sport", ""),
            current_step=int(data.get("current_step", 0)),
            target_steps=int(data.get("target_steps", 0)),
            current_segment=data.get("current_segment", ""),
            possession_team=data.get("possession_team", "home"),
            home_score=int(data.get("home_score", 0)),
            away_score=int(data.get("away_score", 0)),
            events_count=int(data.get("events_count", 0)),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            completed_at=data.get("completed_at"),
            warnings=data.get("warnings", []),
            error=data.get("error"),
            home_lineup=data.get("home_lineup", []),
            away_lineup=data.get("away_lineup", []),
            home_bench=data.get("home_bench", []),
            away_bench=data.get("away_bench", []),
            home_coach=data.get("home_coach", ""),
            away_coach=data.get("away_coach", ""),
            simulation_mode=data.get("simulation_mode", "legacy"),
            quarter=int(data.get("quarter", 1)),
            overtime=int(data.get("overtime", 0)),
            game_clock=data.get("game_clock", ""),
            shot_clock=int(data.get("shot_clock", 0)),
            possession_phase=data.get("possession_phase", ""),
            ball_handler=data.get("ball_handler", ""),
            ball_zone=data.get("ball_zone", ""),
            offense_set=data.get("offense_set", ""),
            defensive_scheme=data.get("defensive_scheme", ""),
            home_team_fouls=int(data.get("home_team_fouls", 0)),
            away_team_fouls=int(data.get("away_team_fouls", 0)),
            player_fouls=data.get("player_fouls", {}),
            home_timeouts=int(data.get("home_timeouts", 0)),
            away_timeouts=int(data.get("away_timeouts", 0)),
            player_fatigue=data.get("player_fatigue", {}),
            player_hot_cold=data.get("player_hot_cold", {}),
            pending_substitutions=data.get("pending_substitutions", {}),
            last_outcome=data.get("last_outcome", ""),
            advantage_state=data.get("advantage_state", ""),
            game_finished=bool(data.get("game_finished", False)),
        )


class SportsSimulationService:
    """Manage asynchronous match simulations."""

    _state_cache: Dict[str, SportsSimulationState] = {}
    _events_cache: Dict[str, List[SportsEvent]] = {}

    def __init__(self):
        self.llm_client = None
        self.llm_error = None
        try:
            self.llm_client = LLMClient()
        except Exception as exc:
            self.llm_error = str(exc)
        self.basketball_engine = BasketballMultiAgentEngine(
            llm_client=self.llm_client,
            use_llm_agents=True,
        )
        self.fan_pool = SportsFanAgentPool(llm_client=self.llm_client)
        self.commentator_team = SportsCommentatorTeam(llm_client=self.llm_client)

    def start_simulation_async(self, workspace_id: str) -> str:
        workspace = SportsWorkspaceManager.get_workspace(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace {workspace_id} not found")
        if workspace.contract_version < SPORTS_WORKSPACE_CONTRACT_VERSION:
            raise ValueError(
                "Workspace was generated by an older fallback-based planner. Re-plan the matchup before simulating."
            )
        if not self.llm_client:
            if self._is_basketball_workspace(workspace):
                raise RuntimeError(
                    f"Basketball simulation requires a configured OpenRouter-compatible LLM client for per-player agents: {self.llm_error or 'unknown error'}"
                )
            raise RuntimeError(
                f"Simulation requires a configured LLM client: {self.llm_error or 'unknown error'}"
            )
        if workspace.status not in (
            SportsWorkspaceStatus.READY,
            SportsWorkspaceStatus.SIMULATED,
            SportsWorkspaceStatus.REPORT_READY,
        ):
            raise ValueError("Workspace is not ready for simulation")
        if not workspace.rule_pack:
            raise ValueError("Workspace does not contain a validated rule pack")

        simulation_id = f"sim_{uuid.uuid4().hex[:12]}"
        state = self._create_state(simulation_id, workspace)
        self._save_state(state)
        self._save_events(simulation_id, [])
        workspace.latest_simulation_id = simulation_id
        workspace.status = SportsWorkspaceStatus.SIMULATING
        SportsWorkspaceManager.save_workspace(workspace)

        thread = threading.Thread(
            target=self._run_worker, args=(workspace_id, simulation_id), daemon=True
        )
        thread.start()
        return simulation_id

    def get_state(
        self, workspace_id: str, simulation_id: Optional[str] = None
    ) -> Optional[SportsSimulationState]:
        workspace = SportsWorkspaceManager.get_workspace(workspace_id)
        if not workspace:
            return None
        simulation_id = simulation_id or workspace.latest_simulation_id
        if not simulation_id:
            return None
        if simulation_id in self._state_cache:
            return self._state_cache[simulation_id]
        path = self._state_path(workspace_id, simulation_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            state = SportsSimulationState.from_dict(json.load(f))
        self._state_cache[simulation_id] = state
        return state

    def get_events(
        self, workspace_id: str, simulation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        workspace = SportsWorkspaceManager.get_workspace(workspace_id)
        if not workspace:
            return []
        simulation_id = simulation_id or workspace.latest_simulation_id
        if not simulation_id:
            return []
        if simulation_id in self._events_cache:
            return [event.to_dict() for event in self._events_cache[simulation_id]]
        path = self._events_path(workspace_id, simulation_id)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            events = [SportsEvent(**item) for item in json.load(f)]
        self._events_cache[simulation_id] = events
        return [event.to_dict() for event in events]

    def _create_state(
        self, simulation_id: str, workspace: SportsWorkspace
    ) -> SportsSimulationState:
        players = [item for item in workspace.participants if item["kind"] == "player"]
        coaches = [item for item in workspace.participants if item["kind"] == "coach"]
        home_players = [
            item["name"]
            for item in players
            if item["team"] == workspace.home_team["name"]
        ]
        away_players = [
            item["name"]
            for item in players
            if item["team"] == workspace.away_team["name"]
        ]
        home_coaches = [
            item["name"]
            for item in coaches
            if item["team"] == workspace.home_team["name"]
        ]
        away_coaches = [
            item["name"]
            for item in coaches
            if item["team"] == workspace.away_team["name"]
        ]
        lineup_size = int(workspace.rule_pack.get("lineup_size", 7))
        if len(home_players) < lineup_size or len(away_players) < lineup_size:
            raise ValueError(
                f"Simulation requires at least {lineup_size} players per team, but the planner did not produce enough real roster data."
            )
        if not home_coaches or not away_coaches:
            raise ValueError("Simulation requires at least one coach dossier per team.")
        state = SportsSimulationState(
            simulation_id=simulation_id,
            workspace_id=workspace.workspace_id,
            status=SportsSimulationStatus.CREATED,
            home_team=workspace.home_team["name"],
            away_team=workspace.away_team["name"],
            sport=workspace.sport,
            target_steps=int(workspace.rule_pack.get("target_steps", 30)),
            current_segment=self._segment_for_step(workspace.rule_pack, 1),
            possession_team="home",
            home_lineup=home_players[:lineup_size],
            away_lineup=away_players[:lineup_size],
            home_coach=home_coaches[0],
            away_coach=away_coaches[0],
        )
        if self._is_basketball_workspace(workspace):
            self.basketball_engine.initialize_state(workspace, state)
        return state

    def _run_worker(self, workspace_id: str, simulation_id: str) -> None:
        workspace = SportsWorkspaceManager.get_workspace(workspace_id)
        state = self.get_state(workspace_id, simulation_id)
        if not workspace or not state:
            return

        events: List[SportsEvent] = []
        try:
            state.status = SportsSimulationStatus.RUNNING
            self._save_state(state)
            rng = random.Random(workspace.scenario.seed)

            step = 0
            while step < state.target_steps:
                if self._is_basketball_state(state) and state.game_finished:
                    break
                step += 1
                state.current_step = step
                if self._is_basketball_state(state):
                    event_payload = self.basketball_engine.step(
                        workspace, state, events[-6:], rng
                    )
                    event = SportsEvent(step=step, **event_payload)
                else:
                    state.current_segment = self._segment_for_step(
                        workspace.rule_pack, step
                    )
                    event = self._generate_event(workspace, state, events[-3:])
                    self._apply_event(state, event, workspace.rule_pack)
                events.append(event)
                state.events_count = len(events)
                self._save_state(state)
                self._save_events(simulation_id, events)

                self._generate_reactions_for_event(
                    workspace_id, simulation_id, event, state, events[-6:], rng
                )

            state.status = SportsSimulationStatus.COMPLETED
            state.completed_at = datetime.now().isoformat()
            workspace.status = SportsWorkspaceStatus.SIMULATED
            workspace.error = None
            SportsWorkspaceManager.save_workspace(workspace)
            self._save_state(state)
        except Exception as exc:
            logger.exception("Sports simulation failed")
            state.status = SportsSimulationStatus.FAILED
            state.error = str(exc)
            workspace.status = SportsWorkspaceStatus.FAILED
            workspace.error = str(exc)
            SportsWorkspaceManager.save_workspace(workspace)
            self._save_state(state)

    def _generate_event(
        self,
        workspace: SportsWorkspace,
        state: SportsSimulationState,
        recent_events: List[SportsEvent],
    ) -> SportsEvent:
        if not self.llm_client:
            raise RuntimeError("Simulation requires a configured LLM client")
        last_error = None
        for attempt in range(1, 4):
            try:
                return self._generate_event_with_llm(
                    workspace,
                    state,
                    recent_events,
                    validation_error=last_error,
                    attempt=attempt,
                )
            except Exception as exc:
                last_error = str(exc)
                logger.warning("Event generation attempt %s failed: %s", attempt, exc)
        raise RuntimeError(
            f"Simulation event generation failed after retries: {last_error}"
        )

    def _is_basketball_workspace(self, workspace: SportsWorkspace) -> bool:
        return normalize_sport_key(workspace.sport) == "basketball"

    def _is_basketball_state(self, state: SportsSimulationState) -> bool:
        return state.simulation_mode in {
            "basketball_multi_agent",
            "basketball_llm_multi_agent",
        }

    def _generate_event_with_llm(
        self,
        workspace: SportsWorkspace,
        state: SportsSimulationState,
        recent_events: List[SportsEvent],
        validation_error: Optional[str] = None,
        attempt: int = 1,
    ) -> SportsEvent:
        offense_label = state.possession_team
        defense_label = "away" if offense_label == "home" else "home"
        home_excerpt = self._lineup_excerpt(
            workspace, state.home_lineup[:3], state.home_coach
        )
        away_excerpt = self._lineup_excerpt(
            workspace, state.away_lineup[:3], state.away_coach
        )
        recent_summary = (
            "\n".join(f"- {event.play_by_play}" for event in recent_events)
            or "- No recent events"
        )
        rule_pack = workspace.rule_pack
        payload = self.llm_client.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a sports match engine. Return one JSON object only with keys: "
                        "segment, clock, offense_team, primary_actor, secondary_actor, coach, "
                        "home_delta, away_delta, title, play_by_play, next_possession, warnings. "
                        "Follow the supplied rule pack exactly. Do not omit fields. Do not invent names "
                        "outside the provided lineups and coaches. Do not return markdown. "
                        "The offense_team and next_possession fields must be the literal strings "
                        "'home' or 'away', not team names. Exactly one of home_delta or away_delta may be positive."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Sport: {workspace.sport}\nLeague: {workspace.league}\n"
                        f"Rule pack: {json.dumps(rule_pack, ensure_ascii=False)}\n"
                        f"Scenario: {json.dumps(workspace.scenario.to_dict(), ensure_ascii=False)}\n"
                        f"Step: {state.current_step} of {state.target_steps}\n"
                        f"Current segment: {state.current_segment}\n"
                        f"Score: {state.home_team} {state.home_score} - {state.away_score} {state.away_team}\n"
                        f"Current possession: {offense_label}\n"
                        f"Required offense coach: {state.home_coach if offense_label == 'home' else state.away_coach}\n"
                        f"Home lineup:\n{home_excerpt}\n\n"
                        f"Away lineup:\n{away_excerpt}\n\n"
                        f"Recent events:\n{recent_summary}\n\n"
                        f"Offense should be {offense_label}. Defense is {defense_label}. "
                        f"Scenario seed: {workspace.scenario.seed}\n"
                        f"Attempt: {attempt}\n"
                        f"Previous validation error: {validation_error or 'none'}\n"
                        "Every response must include non-empty values for segment, clock, title, play_by_play, "
                        "offense_team, primary_actor, coach, next_possession, home_delta, away_delta.\n"
                        "Keep the event realistic for the sport and matchup."
                    ),
                },
            ],
            temperature=min(max(workspace.scenario.randomness, 0.05), 0.35),
            max_tokens=500,
        )
        return self._event_from_payload(workspace, state, payload)

    def _event_from_payload(
        self,
        workspace: SportsWorkspace,
        state: SportsSimulationState,
        payload: Dict[str, Any],
    ) -> SportsEvent:
        if not isinstance(payload, dict):
            raise ValueError("LLM event payload must be a JSON object")

        segment = self._required_str(payload, "segment")
        if segment != state.current_segment:
            raise ValueError(
                f"Event segment '{segment}' does not match current segment '{state.current_segment}'"
            )

        offense_team = self._normalize_side_label(
            self._required_str(payload, "offense_team"),
            state,
            "offense_team",
        )
        if offense_team != state.possession_team:
            raise ValueError(
                f"Event offense_team '{offense_team}' does not match current possession '{state.possession_team}'"
            )

        offense_team_name = (
            state.home_team if offense_team == "home" else state.away_team
        )
        offense_players = set(
            state.home_lineup if offense_team == "home" else state.away_lineup
        )
        offense_coaches = {
            item["name"]
            for item in workspace.participants
            if item["team"] == offense_team_name and item["kind"] == "coach"
        }
        all_participants = {item["name"] for item in workspace.participants}

        primary_actor = self._required_str(payload, "primary_actor")
        if primary_actor not in offense_players:
            raise ValueError(
                f"Primary actor '{primary_actor}' is not a player on the offense team"
            )

        secondary_actor = str(payload.get("secondary_actor", "") or "").strip()
        if secondary_actor and secondary_actor not in all_participants:
            raise ValueError(
                f"Secondary actor '{secondary_actor}' is not a known participant"
            )

        coach = self._required_str(payload, "coach")
        if coach not in offense_coaches:
            raise ValueError(
                f"Coach '{coach}' is not a known coach for the offense team"
            )

        home_delta = self._required_int(payload, "home_delta")
        away_delta = self._required_int(payload, "away_delta")
        title = self._required_str(payload, "title")
        play_by_play = self._required_str(payload, "play_by_play")
        clock = self._required_str(payload, "clock")
        next_possession = self._normalize_side_label(
            self._required_str(payload, "next_possession"),
            state,
            "next_possession",
        )

        warnings_payload = payload.get("warnings", [])
        if warnings_payload is None:
            warnings_payload = []
        elif isinstance(warnings_payload, str):
            warnings_payload = [warnings_payload] if warnings_payload.strip() else []
        elif not isinstance(warnings_payload, list):
            raise ValueError("Event warnings must be a JSON array or string")

        return SportsEvent(
            step=state.current_step,
            segment=segment,
            clock=clock,
            offense_team=offense_team,
            primary_actor=primary_actor,
            secondary_actor=secondary_actor,
            coach=coach,
            home_delta=home_delta,
            away_delta=away_delta,
            title=title,
            play_by_play=play_by_play,
            next_possession=next_possession,
            warnings=[str(item) for item in warnings_payload],
        )

    def _apply_event(
        self,
        state: SportsSimulationState,
        event: SportsEvent,
        rule_pack: Dict[str, Any],
    ) -> None:
        allowed_values = sorted(
            int(value) for value in rule_pack.get("allowed_score_values", [0, 1, 2, 3])
        )
        max_delta = int(rule_pack.get("max_delta_per_step", max(allowed_values)))
        if event.segment != state.current_segment:
            raise ValueError(
                f"Event segment '{event.segment}' does not match current segment '{state.current_segment}'"
            )
        if event.offense_team not in ("home", "away"):
            raise ValueError("Event offense team must be 'home' or 'away'")
        if event.offense_team != state.possession_team:
            raise ValueError(
                f"Event offense team '{event.offense_team}' does not match possession '{state.possession_team}'"
            )
        if event.home_delta > 0 and event.away_delta > 0:
            raise ValueError("Both teams cannot score on the same event")
        if event.home_delta < 0 or event.away_delta < 0:
            raise ValueError("Negative score deltas are not allowed")

        total_delta = event.home_delta or event.away_delta
        if total_delta > max_delta:
            raise ValueError(f"Score delta {total_delta} exceeds max delta {max_delta}")
        if total_delta not in allowed_values:
            raise ValueError(f"Score delta {total_delta} is not allowed for this sport")
        if event.next_possession not in ("home", "away"):
            raise ValueError("Event next_possession must be 'home' or 'away'")

        state.home_score += event.home_delta
        state.away_score += event.away_delta
        state.possession_team = event.next_possession
        state.updated_at = datetime.now().isoformat()
        state.warnings.extend(event.warnings)

    def _segment_for_step(self, rule_pack: Dict[str, Any], step: int) -> str:
        segments = rule_pack.get("segments") or ["Match"]
        target_steps = max(int(rule_pack.get("target_steps", 30)), 1)
        bucket = max(target_steps // len(segments), 1)
        index = min((step - 1) // bucket, len(segments) - 1)
        return segments[index]

    def _lineup_excerpt(
        self, workspace: SportsWorkspace, lineup: List[str], coach_name: str
    ) -> str:
        excerpts = [f"Coach: {coach_name}"]
        for player_name in lineup:
            participant = next(
                (
                    item
                    for item in workspace.participants
                    if item["name"] == player_name
                ),
                None,
            )
            line = f"- {player_name}"
            if participant and participant.get("role"):
                line += f" ({participant['role']})"
            excerpts.append(line)
        return "\n".join(excerpts)

    def _required_str(self, payload: Dict[str, Any], key: str) -> str:
        value = payload.get(key)
        if value is None:
            raise ValueError(f"Event field '{key}' is required")
        text = str(value).strip()
        if not text:
            raise ValueError(f"Event field '{key}' cannot be empty")
        return text

    def _required_int(self, payload: Dict[str, Any], key: str) -> int:
        if key not in payload:
            raise ValueError(f"Event field '{key}' is required")
        try:
            return int(payload[key])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Event field '{key}' must be an integer") from exc

    def _normalize_side_label(
        self, value: str, state: SportsSimulationState, field_name: str
    ) -> str:
        normalized = value.strip().lower()
        if normalized in {"home", "away"}:
            return normalized

        aliases = {
            state.home_team.strip().lower(): "home",
            state.away_team.strip().lower(): "away",
            "home team": "home",
            "away team": "away",
        }
        if normalized in aliases:
            return aliases[normalized]

        raise ValueError(f"Event {field_name} must resolve to 'home' or 'away'")

    def _state_path(self, workspace_id: str, simulation_id: str) -> str:
        return os.path.join(
            SportsWorkspaceManager.get_simulations_dir(workspace_id),
            simulation_id,
            "state.json",
        )

    def _events_path(self, workspace_id: str, simulation_id: str) -> str:
        return os.path.join(
            SportsWorkspaceManager.get_simulations_dir(workspace_id),
            simulation_id,
            "events.json",
        )

    def _save_state(self, state: SportsSimulationState) -> None:
        os.makedirs(
            os.path.dirname(self._state_path(state.workspace_id, state.simulation_id)),
            exist_ok=True,
        )
        with open(
            self._state_path(state.workspace_id, state.simulation_id),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
        self._state_cache[state.simulation_id] = state

    def _save_events(self, simulation_id: str, events: List[SportsEvent]) -> None:
        if not events:
            state = self._state_cache.get(simulation_id)
            if not state:
                return
            path = self._events_path(state.workspace_id, simulation_id)
        else:
            path = self._events_path(
                self._state_cache[simulation_id].workspace_id, simulation_id
            )
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                [event.to_dict() for event in events], f, ensure_ascii=False, indent=2
            )
        self._events_cache[simulation_id] = events

    def _generate_reactions_for_event(
        self,
        workspace_id: str,
        simulation_id: str,
        event: SportsEvent,
        state: SportsSimulationState,
        recent_events: List[SportsEvent],
        rng: random.Random,
    ) -> None:
        """Generate fan and commentator reactions after a game event."""
        event_dict = event.to_dict()
        game_state = state.to_dict()
        recent_dicts = [e.to_dict() for e in recent_events[-3:]]

        try:
            fan_reactions = self.fan_pool.generate_reaction(
                event=event_dict,
                game_state=game_state,
                recent_events=recent_dicts,
            )
            self.fan_pool.store_reactions(simulation_id, fan_reactions, workspace_id)
        except Exception as exc:
            logger.debug("Fan reaction generation skipped: %s", exc)

        try:
            commentary_entries = self.commentator_team.generate_commentary(
                event=event_dict,
                game_state=game_state,
                recent_events=recent_dicts,
            )
            commentary_dicts = [
                {
                    "commentator_name": c["commentator_name"],
                    "commentary_text": c["commentary_text"],
                    "type": c["type"],
                    "timestamp": c["timestamp"],
                    "event_reference": c.get("event_reference", {}),
                }
                for c in commentary_entries
            ]
            self.fan_pool.store_reactions(simulation_id, commentary_dicts, workspace_id)
        except Exception as exc:
            logger.debug("Commentary generation skipped: %s", exc)
