"""
Sports matchup planner and dossier generator.
"""

import secrets
import threading
from typing import Any, Dict, List, Tuple

from ..models.sports_workspace import SportsWorkspace, SportsWorkspaceManager, SportsWorkspaceStatus, slugify
from ..models.task import TaskManager, TaskStatus
from ..utils.logger import get_logger
from ..utils.llm_client import LLMClient
from .sports_data_provider import SportsDataProvider
from .sports_profiles import build_participant_profile, render_profile_markdown
from .sports_rule_packs import get_rule_pack, list_supported_sports, normalize_sport_key

logger = get_logger("hermes.sports_planner")


class SportsPlannerService:
    """Resolve teams, build a rule pack, and persist participant dossiers."""

    def __init__(self):
        self.task_manager = TaskManager()
        self.provider = None
        self.provider_error = None
        self.planning_llm = None
        self.planning_llm_error = None
        try:
            self.provider = SportsDataProvider()
        except Exception as exc:
            self.provider_error = str(exc)
        try:
            self.planning_llm = LLMClient()
        except Exception as exc:
            self.planning_llm_error = str(exc)

    def plan_match_async(
        self,
        sport: str,
        league: str,
        home_team: str,
        away_team: str,
        game_context: str = "",
    ) -> Tuple[str, str]:
        if not self.provider:
            raise RuntimeError(
                f"Sports planning requires a configured research provider: {self.provider_error or 'unknown error'}"
            )
        if not self.planning_llm:
            raise RuntimeError(
                f"Sports planning requires a configured planning LLM: {self.planning_llm_error or 'unknown error'}"
            )
        workspace = SportsWorkspaceManager.create_workspace(
            sport=sport,
            league=league,
            home_team=home_team,
            away_team=away_team,
            game_context=game_context,
        )
        task_id = self.task_manager.create_task(
            task_type="sports_plan",
            metadata={"workspace_id": workspace.workspace_id},
        )
        workspace.status = SportsWorkspaceStatus.PLANNING
        workspace.planning_task_id = task_id
        SportsWorkspaceManager.save_workspace(workspace)
        thread = threading.Thread(
            target=self._plan_worker,
            args=(workspace.workspace_id, task_id),
            daemon=True,
        )
        thread.start()
        return workspace.workspace_id, task_id

    def _plan_worker(self, workspace_id: str, task_id: str) -> None:
        workspace = SportsWorkspaceManager.get_workspace(workspace_id)
        if not workspace:
            self.task_manager.fail_task(task_id, f"Workspace {workspace_id} not found")
            return

        try:
            self.task_manager.update_task(task_id, status=TaskStatus.PROCESSING, progress=5, message="Resolving teams")
            home_team = self.provider.search_team(workspace.home_team_query, workspace.sport, workspace.league)
            away_team = self.provider.search_team(workspace.away_team_query, workspace.sport, workspace.league)
            if not home_team or not away_team:
                raise ValueError("Could not resolve one or both teams from the configured sports research provider")

            workspace.home_team = home_team
            workspace.away_team = away_team
            rule_pack = self._build_rule_pack(workspace, home_team, away_team)
            workspace.sport = rule_pack["sport"]
            workspace.league = workspace.league or home_team.get("league") or away_team.get("league") or ""
            workspace.rule_pack = rule_pack
            workspace.source_links = list(
                dict.fromkeys(
                    (home_team.get("source_urls") or [home_team["source_url"]]) +
                    (away_team.get("source_urls") or [away_team["source_url"]])
                )
            )
            SportsWorkspaceManager.save_workspace(workspace)

            self.task_manager.update_task(task_id, progress=25, message="Loading current rosters")
            home_roster = self.provider.get_roster(home_team["id"])
            away_roster = self.provider.get_roster(away_team["id"])

            home_coaches, home_players = self._split_roster(home_roster, home_team)
            away_coaches, away_players = self._split_roster(away_roster, away_team)
            lineup_size = int(rule_pack["lineup_size"])
            if len(home_players) < lineup_size or len(away_players) < lineup_size:
                raise ValueError(
                    f"Roster data is incomplete for {workspace.home_team_query} vs {workspace.away_team_query}. "
                    f"Each team needs at least {lineup_size} players for {workspace.sport}."
                )
            if not home_coaches or not away_coaches:
                raise ValueError(
                    f"Coach data is incomplete for {workspace.home_team_query} vs {workspace.away_team_query}. "
                    "The configured data source must provide at least one coach per team."
                )

            self.task_manager.update_task(task_id, progress=45, message="Building sport rule pack")
            workspace.scenario.seed = secrets.randbelow(1_000_000) + 1
            SportsWorkspaceManager.save_workspace(workspace)

            self.task_manager.update_task(task_id, progress=55, message="Creating planning brief")
            planning_brief = self._build_planning_brief(
                workspace,
                rule_pack,
                home_team,
                away_team,
                home_players,
                away_players,
                home_coaches,
                away_coaches,
            )
            matchup_summary = self._format_planning_summary(planning_brief)

            self.task_manager.update_task(task_id, progress=65, message="Writing basketball persona dossiers")
            dossier_index: List[Dict[str, Any]] = []
            participants: List[Dict[str, Any]] = []
            for team_info, coaches, players in (
                (home_team, home_coaches, home_players),
                (away_team, away_coaches, away_players),
            ):
                team_focus = (
                    planning_brief["home_focus"]
                    if team_info["name"] == home_team["name"]
                    else planning_brief["away_focus"]
                )
                team_path = SportsWorkspaceManager.write_dossier(
                    workspace_id,
                    "teams",
                    team_info["name"],
                    self._render_team_dossier(team_info, team_focus),
                )
                dossier_index.append({"type": "team", "name": team_info["name"], "path": team_path})

                for coach_index, coach in enumerate(coaches):
                    participant, index_entry = self._build_participant_record(
                        workspace_id=workspace_id,
                        person=coach,
                        team_info=team_info,
                        kind="coach",
                        team_focus=team_focus,
                        roster_index=coach_index,
                    )
                    participants.append(participant)
                    dossier_index.append(index_entry)

                for player_index, player in enumerate(players):
                    participant, index_entry = self._build_participant_record(
                        workspace_id=workspace_id,
                        person=player,
                        team_info=team_info,
                        kind="player",
                        team_focus=team_focus,
                        roster_index=player_index,
                    )
                    participants.append(participant)
                    dossier_index.append(index_entry)

            rule_path = SportsWorkspaceManager.write_dossier(
                workspace_id,
                "rules",
                f"{workspace.sport}-rules",
                self._render_rule_dossier(workspace, rule_pack),
            )
            matchup_path = SportsWorkspaceManager.write_dossier(
                workspace_id,
                "matchup",
                f"{workspace.home_team_query}-vs-{workspace.away_team_query}",
                self._render_matchup_dossier(
                    workspace,
                    home_players,
                    away_players,
                    home_coaches,
                    away_coaches,
                    matchup_summary,
                ),
            )
            dossier_index.append({"type": "rules", "name": f"{workspace.sport} rules", "path": rule_path})
            dossier_index.append({"type": "matchup", "name": "matchup summary", "path": matchup_path})

            workspace.dossier_index = dossier_index
            workspace.participants = participants
            workspace.matchup_summary = matchup_summary
            workspace.warnings = list(planning_brief["swing_factors"])
            workspace.status = SportsWorkspaceStatus.READY
            workspace.error = None
            SportsWorkspaceManager.save_workspace(workspace)
            self.task_manager.complete_task(
                task_id,
                {
                    "workspace_id": workspace_id,
                    "participants_count": len(participants),
                    "dossiers_count": len(dossier_index),
                },
            )
        except Exception as exc:
            logger.exception("Sports planning failed")
            workspace.status = SportsWorkspaceStatus.FAILED
            workspace.error = str(exc)
            SportsWorkspaceManager.save_workspace(workspace)
            self.task_manager.fail_task(task_id, str(exc))

    def _split_roster(self, roster: List[Dict[str, Any]], team_info: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        coaches: List[Dict[str, Any]] = []
        players: List[Dict[str, Any]] = []
        seen_player_ids = set()
        seen_coach_names = set()
        for person in roster:
            position = (person.get("position") or "").lower()
            if any(keyword in position for keyword in ("coach", "manager", "assistant")):
                coach_name = (person.get("name") or "").strip()
                if coach_name and coach_name not in seen_coach_names:
                    coaches.append(person)
                    seen_coach_names.add(coach_name)
            else:
                player_id = person.get("id")
                if player_id and player_id not in seen_player_ids:
                    players.append(person)
                    seen_player_ids.add(player_id)

        manager_name = (team_info.get("manager") or "").strip()
        if not coaches and manager_name:
            coaches.append(
                {
                    "id": f"coach-{slugify(team_info['name'])}",
                    "name": manager_name,
                    "position": "Head Coach",
                    "description": team_info.get("description", ""),
                    "source_url": team_info.get("source_url"),
                    "sport": team_info.get("sport"),
                    "team": team_info.get("name"),
                }
            )
        return coaches, players

    def _build_rule_pack(
        self,
        workspace: SportsWorkspace,
        home_team: Dict[str, Any],
        away_team: Dict[str, Any],
    ) -> Dict[str, Any]:
        requested_sport = ""
        for candidate in (workspace.sport, home_team.get("sport"), away_team.get("sport")):
            if normalize_sport_key(candidate or ""):
                requested_sport = candidate or ""
                break
        if not requested_sport:
            unsupported = workspace.sport or home_team.get("sport") or away_team.get("sport") or ""
            raise ValueError(
                f"Unsupported sport '{unsupported}'. Supported sports: "
                f"{', '.join(item['sport'] for item in list_supported_sports())}"
            )
        return get_rule_pack(requested_sport)

    def _render_team_dossier(self, team_info: Dict[str, Any], planning_focus: List[str]) -> str:
        focus_block = "\n".join(f"- {item}" for item in planning_focus)
        return (
            f"# {team_info['name']}\n\n"
            f"- Sport: {team_info.get('sport') or 'Unavailable'}\n"
            f"- League: {team_info.get('league') or 'Unavailable'}\n"
            f"- Country: {team_info.get('country') or 'Unavailable'}\n"
            f"- Stadium: {team_info.get('stadium') or 'Unavailable'}\n"
            f"- Founded: {team_info.get('founded') or 'Unavailable'}\n"
            f"- Source: {team_info.get('source_url') or 'Unavailable'}\n\n"
            "## Background\n\n"
            f"{team_info.get('description') or 'Unavailable from the configured sports research provider at planning time.'}\n\n"
            "## Planning Focus\n\n"
            f"{focus_block}\n"
        )

    def _build_participant_record(
        self,
        *,
        workspace_id: str,
        person: Dict[str, Any],
        team_info: Dict[str, Any],
        kind: str,
        team_focus: List[str],
        roster_index: int,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        profile = build_participant_profile(
            person,
            team_info,
            kind,
            team_focus=team_focus,
            roster_index=roster_index,
        )
        filename = f"{person['name']}-{team_info['name']}"
        category = "coaches" if kind == "coach" else "players"
        dossier_path = SportsWorkspaceManager.write_dossier(
            workspace_id,
            category,
            filename,
            render_profile_markdown(profile),
        )
        profile_path = SportsWorkspaceManager.write_dossier_json(
            workspace_id,
            category,
            filename,
            profile,
        )
        participant = {
            "id": person["id"],
            "name": person["name"],
            "team": team_info["name"],
            "role": person.get("position", kind.title()),
            "kind": kind,
            "path": dossier_path,
            "profile_path": profile_path,
            "profile": profile,
            "source_urls": profile.get("source_urls", []),
        }
        return participant, {
            "type": kind,
            "name": person["name"],
            "path": dossier_path,
            "profile_path": profile_path,
        }

    def _render_rule_dossier(self, workspace: SportsWorkspace, rule_pack: Dict[str, Any]) -> str:
        segments = "\n".join(f"- {segment}" for segment in rule_pack.get("segments", []))
        phases = "\n".join(f"- {phase}" for phase in rule_pack.get("phases", []))
        score_values = ", ".join(str(value) for value in rule_pack.get("allowed_score_values", []))
        validation = "\n".join(f"- {rule}" for rule in rule_pack.get("validation_rules", []))
        basketball_details = ""
        if rule_pack.get("phases"):
            basketball_details = (
                f"- Shot clock: {rule_pack.get('shot_clock', 'Unavailable')}\n"
                f"- Quarter minutes: {rule_pack.get('quarter_minutes', 'Unavailable')}\n"
                f"- Timeouts per team: {rule_pack.get('timeouts_per_team', 'Unavailable')}\n"
                f"- Bonus threshold: {rule_pack.get('bonus_threshold', 'Unavailable')}\n"
                f"- Foul-out limit: {rule_pack.get('foul_out_limit', 'Unavailable')}\n\n"
                "## Possession Phases\n\n"
                f"{phases}\n\n"
            )
        return (
            f"# {workspace.sport} Rule Pack\n\n"
            f"- Step unit: {rule_pack['step_unit']}\n"
            f"- Target steps: {rule_pack['target_steps']}\n"
            f"- Lineup size: {rule_pack['lineup_size']}\n"
            f"- Allowed score values: {score_values}\n"
            f"- Max delta per step: {rule_pack['max_delta_per_step']}\n\n"
            f"{basketball_details}"
            "## Segments\n\n"
            f"{segments}\n\n"
            "## Validation Rules\n\n"
            f"{validation}\n\n"
            "## Summary\n\n"
            f"{rule_pack['summary']}\n"
        )

    def _render_matchup_dossier(
        self,
        workspace: SportsWorkspace,
        home_players: List[Dict[str, Any]],
        away_players: List[Dict[str, Any]],
        home_coaches: List[Dict[str, Any]],
        away_coaches: List[Dict[str, Any]],
        matchup_summary: str,
    ) -> str:
        return (
            f"# {workspace.home_team_query} vs {workspace.away_team_query}\n\n"
            f"- Sport: {workspace.sport}\n"
            f"- League: {workspace.league or 'Unavailable'}\n"
            f"- Game context: {workspace.game_context or 'Not provided'}\n"
            f"- Home coaches: {', '.join(coach['name'] for coach in home_coaches[:3])}\n"
            f"- Away coaches: {', '.join(coach['name'] for coach in away_coaches[:3])}\n"
            f"- Home roster size: {len(home_players)} players\n"
            f"- Away roster size: {len(away_players)} players\n\n"
            "## Planner Summary\n\n"
            f"{matchup_summary}\n"
        )

    def _build_planning_brief(
        self,
        workspace: SportsWorkspace,
        rule_pack: Dict[str, Any],
        home_team: Dict[str, Any],
        away_team: Dict[str, Any],
        home_players: List[Dict[str, Any]],
        away_players: List[Dict[str, Any]],
        home_coaches: List[Dict[str, Any]],
        away_coaches: List[Dict[str, Any]],
    ) -> Dict[str, List[str] | str]:
        if not self.planning_llm:
            raise RuntimeError("Sports planning requires a configured planning LLM")

        payload = self.planning_llm.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a sports matchup planner. Use only the supplied researched facts. "
                        "Return one JSON object with keys: summary, home_focus, away_focus, swing_factors. "
                        "summary must be a concise paragraph. home_focus, away_focus, and swing_factors must each "
                        "be arrays of 2 to 4 short strings. Do not invent injuries, starters, stats, or people "
                        "outside the supplied teams, coaches, and players."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Sport: {workspace.sport}\n"
                        f"League: {workspace.league or 'Unavailable'}\n"
                        f"Game context: {workspace.game_context or 'None provided'}\n"
                        f"Rule pack summary: {rule_pack.get('summary', '')}\n"
                        f"Home team: {home_team['name']}\n"
                        f"Home team background: {home_team.get('description') or 'Unavailable'}\n"
                        f"Home coaches: {self._compact_participant_brief(home_coaches[:3])}\n"
                        f"Home players: {self._compact_participant_brief(home_players[:10])}\n"
                        f"Away team: {away_team['name']}\n"
                        f"Away team background: {away_team.get('description') or 'Unavailable'}\n"
                        f"Away coaches: {self._compact_participant_brief(away_coaches[:3])}\n"
                        f"Away players: {self._compact_participant_brief(away_players[:10])}\n"
                    ),
                },
            ],
            temperature=0.2,
            max_tokens=900,
        )
        if not isinstance(payload, dict):
            raise ValueError("Planning brief payload must be a JSON object")
        summary = str(payload.get("summary") or "").strip()
        if not summary:
            raise ValueError("Planning brief is missing 'summary'")
        return {
            "summary": summary,
            "home_focus": self._string_list(payload.get("home_focus"), "home_focus"),
            "away_focus": self._string_list(payload.get("away_focus"), "away_focus"),
            "swing_factors": self._string_list(payload.get("swing_factors"), "swing_factors"),
        }

    def _format_planning_summary(self, planning_brief: Dict[str, List[str] | str]) -> str:
        return (
            f"{planning_brief['summary']}\n\n"
            "Home Focus\n"
            f"{self._markdown_bullets(planning_brief['home_focus'])}\n\n"
            "Away Focus\n"
            f"{self._markdown_bullets(planning_brief['away_focus'])}\n\n"
            "Swing Factors\n"
            f"{self._markdown_bullets(planning_brief['swing_factors'])}"
        )

    def _compact_participant_brief(self, participants: List[Dict[str, Any]]) -> str:
        lines = []
        for participant in participants:
            name = str(participant.get("name") or "").strip()
            role = str(participant.get("position") or participant.get("role") or "Unknown").strip()
            description = str(participant.get("description") or "").strip()
            line = f"- {name} ({role})"
            if description:
                line += f": {description}"
            lines.append(line)
        return "\n".join(lines) or "- None"

    def _string_list(self, value: Any, field_name: str) -> List[str]:
        if not isinstance(value, list):
            raise ValueError(f"Planning brief field '{field_name}' must be a JSON array")
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        if len(cleaned) < 2:
            raise ValueError(f"Planning brief field '{field_name}' must contain at least two items")
        return cleaned[:4]

    def _markdown_bullets(self, items: List[str]) -> str:
        return "\n".join(f"- {item}" for item in items)
