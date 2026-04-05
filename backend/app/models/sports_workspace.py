"""
Sports workspace persistence models.
"""

import json
import os
import re
import secrets
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ..config import Config


SPORTS_WORKSPACE_CONTRACT_VERSION = 4


def slugify(value: str) -> str:
    """Create a filesystem-safe slug."""
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value or "").strip("-").lower()
    return value or "item"


def _default_seed() -> int:
    return secrets.randbelow(1_000_000) + 1


class SportsWorkspaceStatus(str, Enum):
    """Lifecycle for a sports workspace."""

    CREATED = "created"
    PLANNING = "planning"
    READY = "ready"
    SIMULATING = "simulating"
    SIMULATED = "simulated"
    REPORT_READY = "report_ready"
    FAILED = "failed"


@dataclass
class SportsScenario:
    """Scenario overrides used during match simulation."""

    venue: str = "home"
    weather: str = "standard"
    pace: str = "balanced"
    randomness: float = 0.35
    fatigue: str = "balanced"
    officiating: str = "standard"
    injuries: str = ""
    notes: str = ""
    seed: int = field(default_factory=_default_seed)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "SportsScenario":
        if not data:
            return cls()
        venue = str(data.get("venue", "home"))
        if venue not in {"home", "away", "neutral"}:
            raise ValueError("Scenario venue must be one of: home, away, neutral")

        pace = str(data.get("pace", "balanced"))
        if pace not in {"slow", "balanced", "fast"}:
            raise ValueError("Scenario pace must be one of: slow, balanced, fast")

        fatigue = str(data.get("fatigue", "balanced"))
        if fatigue not in {"fresh", "balanced", "fatigued"}:
            raise ValueError("Scenario fatigue must be one of: fresh, balanced, fatigued")

        officiating = str(data.get("officiating", "standard"))
        if officiating not in {"standard", "tight", "lenient"}:
            raise ValueError("Scenario officiating must be one of: standard, tight, lenient")

        randomness = float(data.get("randomness", 0.35))
        if randomness < 0 or randomness > 1:
            raise ValueError("Scenario randomness must be between 0 and 1")

        seed = data.get("seed", _default_seed())
        try:
            seed = int(seed)
        except (TypeError, ValueError) as exc:
            raise ValueError("Scenario seed must be an integer") from exc
        if seed <= 0:
            raise ValueError("Scenario seed must be positive")

        return cls(
            venue=venue,
            weather=str(data.get("weather", "standard")),
            pace=pace,
            randomness=randomness,
            fatigue=fatigue,
            officiating=officiating,
            injuries=str(data.get("injuries", "")),
            notes=str(data.get("notes", "")),
            seed=seed,
        )


@dataclass
class SportsWorkspace:
    """Persisted planning and simulation context for a sports matchup."""

    workspace_id: str
    contract_version: int
    sport: str
    league: str
    home_team_query: str
    away_team_query: str
    game_context: str
    created_at: str
    updated_at: str
    status: SportsWorkspaceStatus = SportsWorkspaceStatus.CREATED
    scenario: SportsScenario = field(default_factory=SportsScenario)
    planning_task_id: Optional[str] = None
    latest_simulation_id: Optional[str] = None
    latest_report_task_id: Optional[str] = None
    latest_report_id: Optional[str] = None
    home_team: Optional[Dict[str, Any]] = None
    away_team: Optional[Dict[str, Any]] = None
    participants: List[Dict[str, Any]] = field(default_factory=list)
    rule_pack: Dict[str, Any] = field(default_factory=dict)
    dossier_index: List[Dict[str, Any]] = field(default_factory=list)
    matchup_summary: str = ""
    source_links: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value if isinstance(self.status, SportsWorkspaceStatus) else self.status
        data["scenario"] = self.scenario.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SportsWorkspace":
        status = data.get("status", SportsWorkspaceStatus.CREATED.value)
        if isinstance(status, str):
            status = SportsWorkspaceStatus(status)
        return cls(
            workspace_id=data["workspace_id"],
            contract_version=int(data.get("contract_version", 1)),
            sport=data.get("sport", ""),
            league=data.get("league", ""),
            home_team_query=data.get("home_team_query", ""),
            away_team_query=data.get("away_team_query", ""),
            game_context=data.get("game_context", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            status=status,
            scenario=SportsScenario.from_dict(data.get("scenario")),
            planning_task_id=data.get("planning_task_id"),
            latest_simulation_id=data.get("latest_simulation_id"),
            latest_report_task_id=data.get("latest_report_task_id"),
            latest_report_id=data.get("latest_report_id"),
            home_team=data.get("home_team"),
            away_team=data.get("away_team"),
            participants=data.get("participants", []),
            rule_pack=data.get("rule_pack", {}),
            dossier_index=data.get("dossier_index", []),
            matchup_summary=data.get("matchup_summary", ""),
            source_links=data.get("source_links", []),
            warnings=data.get("warnings", []),
            error=data.get("error"),
        )


class SportsWorkspaceManager:
    """Filesystem-backed manager for sports workspaces."""

    ROOT_DIR = os.path.join(Config.UPLOAD_FOLDER, "sports")
    WORKSPACES_DIR = os.path.join(ROOT_DIR, "workspaces")

    @classmethod
    def _ensure_root(cls) -> None:
        os.makedirs(cls.WORKSPACES_DIR, exist_ok=True)

    @classmethod
    def create_workspace(
        cls,
        sport: str,
        league: str,
        home_team: str,
        away_team: str,
        game_context: str = "",
    ) -> SportsWorkspace:
        cls._ensure_root()
        workspace_id = f"sports_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        workspace = SportsWorkspace(
            workspace_id=workspace_id,
            contract_version=SPORTS_WORKSPACE_CONTRACT_VERSION,
            sport=sport,
            league=league,
            home_team_query=home_team,
            away_team_query=away_team,
            game_context=game_context,
            created_at=now,
            updated_at=now,
        )
        os.makedirs(cls.get_workspace_dir(workspace_id), exist_ok=True)
        for dirname in ("dossiers", "reports", "simulations"):
            os.makedirs(os.path.join(cls.get_workspace_dir(workspace_id), dirname), exist_ok=True)
        cls.save_workspace(workspace)
        return workspace

    @classmethod
    def get_workspace_dir(cls, workspace_id: str) -> str:
        return os.path.join(cls.WORKSPACES_DIR, workspace_id)

    @classmethod
    def get_dossiers_dir(cls, workspace_id: str) -> str:
        return os.path.join(cls.get_workspace_dir(workspace_id), "dossiers")

    @classmethod
    def get_dossier_category_dir(cls, workspace_id: str, category: str) -> str:
        return os.path.join(cls.get_dossiers_dir(workspace_id), slugify(category))

    @classmethod
    def get_reports_dir(cls, workspace_id: str) -> str:
        return os.path.join(cls.get_workspace_dir(workspace_id), "reports")

    @classmethod
    def get_simulations_dir(cls, workspace_id: str) -> str:
        return os.path.join(cls.get_workspace_dir(workspace_id), "simulations")

    @classmethod
    def _workspace_path(cls, workspace_id: str) -> str:
        return os.path.join(cls.get_workspace_dir(workspace_id), "workspace.json")

    @classmethod
    def save_workspace(cls, workspace: SportsWorkspace) -> None:
        cls._ensure_root()
        workspace.updated_at = datetime.now().isoformat()
        with open(cls._workspace_path(workspace.workspace_id), "w", encoding="utf-8") as f:
            json.dump(workspace.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def get_workspace(cls, workspace_id: str) -> Optional[SportsWorkspace]:
        path = cls._workspace_path(workspace_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return SportsWorkspace.from_dict(json.load(f))

    @classmethod
    def list_workspaces(cls, limit: int = 50) -> List[SportsWorkspace]:
        cls._ensure_root()
        results: List[SportsWorkspace] = []
        for workspace_id in os.listdir(cls.WORKSPACES_DIR):
            workspace = cls.get_workspace(workspace_id)
            if workspace:
                results.append(workspace)
        results.sort(key=lambda item: item.created_at, reverse=True)
        return results[:limit]

    @classmethod
    def write_dossier(
        cls,
        workspace_id: str,
        category: str,
        name: str,
        content: str,
    ) -> str:
        base_dir = cls.get_dossier_category_dir(workspace_id, category)
        os.makedirs(base_dir, exist_ok=True)
        path = os.path.join(base_dir, f"{slugify(name)}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    @classmethod
    def write_dossier_json(
        cls,
        workspace_id: str,
        category: str,
        name: str,
        data: Dict[str, Any],
    ) -> str:
        base_dir = cls.get_dossier_category_dir(workspace_id, category)
        path = os.path.join(base_dir, f"{slugify(name)}.json")
        cls.write_json(path, data)
        return path

    @classmethod
    def write_json(cls, path: str, data: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def read_json(cls, path: str) -> Optional[Dict[str, Any]]:
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
