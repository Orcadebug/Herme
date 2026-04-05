"""
Perplexity-backed sports research provider.
"""

import json
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI

from ..config import Config
from ..models.sports_workspace import slugify


def _normalize_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _extract_first_json_object(text: str) -> Dict[str, Any]:
    stripped = (text or "").strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    start = stripped.find("{")
    if start == -1:
        raise ValueError("Research response did not contain a JSON object")

    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(stripped)):
        char = stripped[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return json.loads(stripped[start:index + 1])

    raise ValueError("Research response contained an incomplete JSON object")


class SportsDataProvider:
    """Fetch team and roster data via web-grounded sports research."""

    def __init__(self):
        self.api_key = (Config.SPORTS_RESEARCH_API_KEY or "").strip()
        self.base_url = (Config.SPORTS_RESEARCH_BASE_URL or "").rstrip("/")
        self.model = (Config.SPORTS_RESEARCH_MODEL_NAME or "").strip()
        if not self.api_key:
            raise ValueError("SPORTS_RESEARCH_API_KEY is required for sports planning")
        if not self.base_url:
            raise ValueError("SPORTS_RESEARCH_BASE_URL is required for sports planning")
        if not self.model:
            raise ValueError("SPORTS_RESEARCH_MODEL_NAME is required for sports planning")

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self._roster_cache: Dict[str, List[Dict[str, Any]]] = {}

    def _research_team(self, name: str, sport: str = "", league: str = "") -> Tuple[Dict[str, Any], List[str]]:
        prompt = (
            "Research the current sports team requested below using live web search.\n"
            "Return JSON only with this schema:\n"
            "{\n"
            '  "found": true,\n'
            '  "team": {\n'
            '    "name": "official team name",\n'
            '    "sport": "canonical sport name",\n'
            '    "league": "current league name",\n'
            '    "country": "country or null",\n'
            '    "stadium": "home venue or null",\n'
            '    "description": "2-4 sentence factual summary",\n'
            '    "manager": "current head coach or manager or null",\n'
            '    "founded": "year or null"\n'
            "  },\n"
            '  "roster": [\n'
            "    {\n"
            '      "name": "person full name",\n'
            '      "kind": "player or coach",\n'
            '      "position": "position or coaching role",\n'
            '      "birth_date": "YYYY-MM-DD or null",\n'
            '      "nationality": "nationality or null",\n'
            '      "height": "height or null",\n'
            '      "weight": "weight or null",\n'
            '      "description": "1-3 sentence factual profile",\n'
            '      "thumb": null\n'
            "    }\n"
            "  ],\n"
            '  "notes": "short note about any uncertainty or nulls"\n'
            "}\n"
            "Requirements:\n"
            "- Use the current team, current head coach/manager, and current roster.\n"
            "- Include at least one coach in roster with kind='coach'.\n"
            "- Include as many current players as you can verify.\n"
            "- Prefer official team/league sources and high-quality current reporting.\n"
            "- If you cannot confidently identify the exact team, return {\"found\": false, \"notes\": \"...\"}.\n"
            "- Do not invent unknown fields; use null when needed.\n\n"
            f"Requested team name: {name}\n"
            f"Requested sport: {sport or 'unspecified'}\n"
            f"Requested league: {league or 'unspecified'}\n"
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a sports research system. Use web-grounded results only. "
                        "Return JSON only and do not include markdown fences."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=3000,
        )
        payload = response.model_dump()
        citations = payload.get("citations") or []
        search_results = payload.get("search_results") or []
        content = payload["choices"][0]["message"]["content"]
        if not citations and not search_results:
            raise RuntimeError("Sports research provider returned no citations for the requested team")
        data = _extract_first_json_object(content)
        source_urls = citations or [item.get("url") for item in search_results if item.get("url")]
        return data, [url for url in source_urls if url]

    def _research_head_coach(self, team_name: str, sport: str = "", league: str = "") -> Tuple[Optional[Dict[str, str]], List[str]]:
        prompt = (
            "Research the current head coach or manager for the team below using live web search.\n"
            "Return JSON only with this schema:\n"
            "{\n"
            '  "found": true,\n'
            '  "name": "full name",\n'
            '  "role": "Head Coach or Manager"\n'
            "}\n"
            "If the answer is uncertain, return {\"found\": false}.\n\n"
            f"Team: {team_name}\n"
            f"Sport: {sport or 'unspecified'}\n"
            f"League: {league or 'unspecified'}\n"
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a sports research system. Use web-grounded results only. "
                        "Return JSON only and do not include markdown fences."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=256,
        )
        payload = response.model_dump()
        citations = payload.get("citations") or []
        search_results = payload.get("search_results") or []
        content = payload["choices"][0]["message"]["content"]
        data = _extract_first_json_object(content)
        source_urls = citations or [item.get("url") for item in search_results if item.get("url")]
        if not data.get("found"):
            return None, [url for url in source_urls if url]
        name = str(data.get("name") or "").strip()
        role = str(data.get("role") or "Head Coach").strip()
        if not name:
            return None, [url for url in source_urls if url]
        return {"name": name, "role": role or "Head Coach"}, [url for url in source_urls if url]

    def search_team(self, name: str, sport: str = "", league: str = "") -> Optional[Dict[str, Any]]:
        if not name.strip():
            raise ValueError("Team name is required")

        data, source_urls = self._research_team(name=name, sport=sport, league=league)
        if not data.get("found"):
            return None

        team = data.get("team") or {}
        roster = data.get("roster")
        team_name = str(team.get("name") or "").strip()
        if not team_name:
            raise ValueError(f"Research provider did not return a canonical team name for '{name}'")
        if not isinstance(roster, list) or not roster:
            raise ValueError(f"Research provider did not return a current roster for '{team_name}'")

        team_id = f"team-{slugify(team_name)}"
        manager_name = str(team.get("manager") or "").strip()
        normalized_roster = self._normalize_roster(
            team_id=team_id,
            team_name=team_name,
            sport=team.get("sport") or sport,
            roster=roster,
            source_urls=source_urls,
        )
        if not any(item["kind"] == "coach" for item in normalized_roster):
            coach_entry, coach_sources = self._research_head_coach(
                team_name=team_name,
                sport=team.get("sport") or sport,
                league=team.get("league") or league,
            )
            for url in coach_sources:
                if url not in source_urls:
                    source_urls.append(url)
            if coach_entry:
                manager_name = coach_entry["name"]
                normalized_roster.append(
                    {
                        "id": f"{team_id}-{slugify(coach_entry['name'])}",
                        "name": coach_entry["name"],
                        "team": team_name,
                        "sport": str(team.get("sport") or sport or "").strip(),
                        "position": coach_entry["role"],
                        "birth_date": None,
                        "nationality": None,
                        "height": None,
                        "weight": None,
                        "description": f"{coach_entry['name']} is the current {coach_entry['role']} of {team_name}.",
                        "thumb": None,
                        "source_url": coach_sources[0] if coach_sources else (source_urls[0] if source_urls else ""),
                        "kind": "coach",
                    }
                )

        if not manager_name:
            manager_name = next((item["name"] for item in normalized_roster if item["kind"] == "coach"), "")
        if not manager_name:
            raise ValueError(f"Research provider did not return a current coach for '{team_name}'")

        self._roster_cache[team_id] = normalized_roster
        primary_source = source_urls[0] if source_urls else ""
        return {
            "id": team_id,
            "name": team_name,
            "sport": team.get("sport") or sport,
            "league": team.get("league") or league,
            "country": team.get("country"),
            "stadium": team.get("stadium"),
            "badge": None,
            "description": team.get("description") or "",
            "manager": manager_name,
            "founded": team.get("founded"),
            "source_url": primary_source,
            "source_urls": source_urls,
            "research_notes": data.get("notes") or "",
        }

    def _normalize_roster(
        self,
        team_id: str,
        team_name: str,
        sport: str,
        roster: List[Dict[str, Any]],
        source_urls: List[str],
    ) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        seen_people = set()
        default_source = source_urls[0] if source_urls else ""
        for item in roster:
            if not isinstance(item, dict):
                continue
            person_name = str(item.get("name") or "").strip()
            if not person_name:
                continue
            dedupe_key = _normalize_text(person_name)
            if dedupe_key in seen_people:
                continue
            seen_people.add(dedupe_key)

            kind = _normalize_text(str(item.get("kind") or "player"))
            position = str(item.get("position") or "").strip()
            if kind not in {"player", "coach"}:
                if any(keyword in position.lower() for keyword in ("coach", "manager", "assistant")):
                    kind = "coach"
                else:
                    kind = "player"

            normalized.append(
                {
                    "id": f"{team_id}-{slugify(person_name)}",
                    "name": person_name,
                    "team": team_name,
                    "sport": str(item.get("sport") or sport or "").strip(),
                    "position": position or ("Head Coach" if kind == "coach" else "Unknown"),
                    "birth_date": item.get("birth_date"),
                    "nationality": item.get("nationality"),
                    "height": item.get("height"),
                    "weight": item.get("weight"),
                    "description": str(item.get("description") or "").strip(),
                    "thumb": item.get("thumb"),
                    "source_url": str(item.get("source_url") or default_source).strip(),
                    "source_urls": [url for url in source_urls if url],
                    "research_notes": "",
                    "kind": kind,
                }
            )
        return normalized

    def get_roster(self, team_id: str) -> List[Dict[str, Any]]:
        if not team_id:
            raise ValueError("Team id is required for roster lookup")
        roster = self._roster_cache.get(team_id)
        if not roster:
            raise ValueError(f"No cached research roster found for team id {team_id}")
        return roster
