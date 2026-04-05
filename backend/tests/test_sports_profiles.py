from app.services.sports_profiles import (
    build_participant_profile,
    parse_profile_markdown,
    render_profile_markdown,
)


def test_player_profile_round_trip():
    team = {
        "name": "New York Sample",
        "description": "A spacing-heavy basketball team built around quick guards and weak-side shooting.",
    }
    player = {
        "name": "Alex Creator",
        "position": "Point Guard",
        "description": "Lead guard and primary playmaker who pressures the rim and creates for teammates.",
        "source_url": "https://example.com/player",
    }

    profile = build_participant_profile(player, team, "player", team_focus=["push pace", "spread the floor"], roster_index=0)
    markdown = render_profile_markdown(profile)
    parsed = parse_profile_markdown(markdown)

    assert parsed["kind"] == "player"
    assert parsed["name"] == "Alex Creator"
    assert parsed["usage_band"] in {"primary", "secondary"}
    assert parsed["playmaking_band"] == "lead"
    assert "Playstyle" in parsed["sections"]
    assert parsed["runtime_card"]["playmaking_factor"] >= 0.75


def test_coach_profile_round_trip():
    team = {
        "name": "Los Angeles Sample",
        "description": "A versatile roster that can switch and push in transition.",
    }
    coach = {
        "name": "Casey Coach",
        "position": "Head Coach",
        "description": "Prefers pace, spacing, and flexible switching coverages.",
        "source_url": "https://example.com/coach",
    }

    profile = build_participant_profile(coach, team, "coach", team_focus=["play fast", "switch 1-4"], roster_index=0)
    markdown = render_profile_markdown(profile)
    parsed = parse_profile_markdown(markdown)

    assert parsed["kind"] == "coach"
    assert parsed["pace_preference"] == "fast"
    assert parsed["switch_policy"] in {"aggressive", "matchup"}
    assert "Coaching Identity" in parsed["sections"]
    assert abs(sum(parsed["offense_family_weights"].values()) - 1.0) < 0.001
