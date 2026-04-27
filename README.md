<div align="center">

# HERMES

**Simulate Any Game. Every Player. Every Play.**

A multi-agent sports simulation engine powered by AI agents with live research data.

</div>

## Overview

**Hermes** is a sports-first multi-agent simulation engine. It uses AI agents — each with unique personalities, playstyles, and tactical preferences — to simulate full games play-by-play. Every player, coach, referee, fan, and commentator acts autonomously, producing realistic game outcomes and rich narrative content.

> **You provide:** Two team names and a sport.
>
> **Hermes returns:** A full game simulation with play-by-play action, live fan reactions, post-game analysis, and the ability to chat with any participant.

### Use Cases

- **Game Simulation**: Watch AI agents play out realistic basketball, soccer, or American football games
- **Player Analysis**: See how individual player agents perform based on their researched profiles
- **Matchup Exploration**: Run hypothetical matchups between any two teams
- **Fan Engagement**: Experience live social media reactions from diverse fan personas during games
- **Post-Game Content**: Generate coach press conferences, player interviews, and media roundups

## How It Works

Hermes runs a multi-stage pipeline that goes from team research to interactive game simulation:

```
Team Names ──► Live Research ──► Agent Profiles ──► Game Simulation ──► Reactions & Analysis
```

### Stage 1: Live Team Research (Perplexity)

1. Enter home and away team names, select a sport
2. Hermes uses **Perplexity** to research live web data for each team:
   - Current roster with player positions and stats
   - Head coach identity and tactical tendencies
   - Team description, recent performance, league context
3. Research results are stored as structured team profiles with source citations

### Stage 2: Agent Profile Generation

For each researched person, Hermes generates a detailed AI agent profile:

- **Player Agents**: Archetype (lead guard, rim big, wing scorer, etc.), usage band, shot profile, defense style, stamina, decision style, hot/cold tendencies, preferred court zones
- **Coach Agents**: Pace preference, rotation style, offensive families (spread PnR, horns, motion), defensive coverages (man, switch, drop, zone), timeout and foul management
- **Fan Agents**: 6 archetypes — superfan (home/away), skeptic, stats nerd, troll fan, neutral analyst — each with unique handles, bios, and personalities
- **Commentator Agents**: Play-by-play announcer (factual/excited) and color commentator (analytical/opinionated)

### Stage 3: Game Simulation (Multi-Agent Engine)

The basketball multi-agent engine runs the game with full autonomy:

1. **Each phase**, every player agent decides their action based on their profile + current game state:
   - Ball handlers choose: drive, pass, shoot, reset
   - Off-ball players choose: screen, cut, space, seal, relocate
   - Defenders choose: contain, press, switch, help, contest
2. **Coach agents** call offensive sets and defensive coverages
3. **Referee agents** evaluate contact and call fouls
4. The engine resolves all decisions into coherent events with proper rule enforcement (shot clock, fouls, bonus, substitutions)
5. After each event, **fan agents** generate social media reactions and **commentators** provide broadcast-style commentary

### Stage 4: Live Reactions & Commentary

During the simulation, Hermes generates real-time content:

- **Fan Reactions**: Twitter-style posts from 30 diverse fan agents with sentiment analysis
- **Commentary**: Play-by-play calls and color analysis for key events
- **Shot Chart**: Visual court/field showing all shot locations and outcomes

### Stage 5: Post-Game Analysis

After the game completes, Hermes generates:

- **Full Box Score**: Player stats with performance grades (A-F)
- **Coach Press Conference**: Quotes from both head coaches
- **Player Interviews**: Reactions from top performers
- **Media Roundup**: Analyst reactions and storylines
- **Game Ball**: MVP award with justification

### Stage 6: Interactive Chat

After simulation, you can chat with any participant:

- Any player from either team
- Both head coaches
- Commentators
- The Match Analyst

Each responds in character based on their profile and what happened in the game.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3)                          │
│  Home → Matchup → Pre-Game → Live Game → Post-Game → Chat   │
│  ESPN-style dark theme: Scoreboard, Player Cards, Shot Chart │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────┐
│                     Backend (Flask)                          │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────────────┐ │
│  │Sports Planner│ │  Simulator   │ │  Fan/Commentator      │ │
│  │(Perplexity)  │ │(Multi-Agent) │ │  Agent Pool           │ │
│  │Team Research │ │Basketball    │ │  Live Reactions       │ │
│  │Profile Build │ │Soccer/FB     │ │  Pre/Post Game        │ │
│  └──────┬──────┘ └──────┬───────┘ └───────────┬───────────┘ │
│         │               │                      │             │
│         ▼               ▼                      ▼             │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────────────┐ │
│  │ Perplexity  │ │  Rule Packs  │ │  Report Generator     │ │
│  │ (Research)  │ │ (Sport Rules)│ │  (Post-Game Content)  │ │
│  └─────────────┘ └──────────────┘ └───────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
              LLM API (OpenRouter) for all agent behavior
```

### Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python / Flask (port 5001) |
| Frontend | Vue 3 + Vite (port 3000) |
| Research | Perplexity API (live web data) |
| LLM | OpenAI-compatible API (OpenRouter, Qwen, etc.) |
| Simulation | Custom multi-agent engine with sport-specific rule packs |
| Deployment | Docker (single container) |
| i18n | 7 languages: Chinese, English, Spanish, French, Portuguese, Russian, German |

### Supported Sports

| Sport | Engine | Status |
|-------|--------|--------|
| Basketball | Multi-agent (player/coach/ref agents) | Full support |
| Soccer | LLM event generation | Rule packs ready |
| American Football | LLM event generation | Rule packs ready |

## Quick Start

### Prerequisites

| Tool | Version | Description |
|------|---------|-------------|
| **Node.js** | 18+ | Frontend runtime, includes npm |
| **Python** | >=3.11, <=3.12 | Backend runtime |
| **uv** | Latest | Python package manager |

### 1. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
# LLM API (agent behavior, simulation, commentary, chat)
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL_NAME=qwen/qwen3.6-plus:free

# Perplexity (live team/roster research)
SPORTS_RESEARCH_API_KEY=your_perplexity_api_key
SPORTS_RESEARCH_BASE_URL=https://api.perplexity.ai
SPORTS_RESEARCH_MODEL_NAME=sonar
```

### 2. Install Dependencies

```bash
# One-click: all dependencies (root + frontend + backend)
npm run setup:all
```

Or step by step:

```bash
npm run setup              # Node dependencies (root + frontend)
npm run setup:backend      # Python dependencies (auto-creates venv)
```

### 3. Start Services

```bash
npm run dev                # Start both frontend and backend
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:5001 |

```bash
npm run backend            # Start backend only
npm run frontend           # Start frontend only
```

### Docker Deployment

```bash
cp .env.example .env
docker compose up -d
```

Reads `.env` from root directory, maps ports `3000` (frontend) and `5001` (backend), persists `./backend/uploads`.

## API Reference

### Sports Game Management (`/api/sports/game/`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/config` | Get supported sports and configuration |
| POST | `/plan` | Research teams and build agent profiles |
| GET | `/plan/status` | Check planning/research progress |
| POST | `/simulate` | Start game simulation |
| GET | `/simulate/status` | Check simulation progress |
| GET | `/<workspace_id>` | Get workspace details |
| GET | `/list` | List all workspaces |
| POST | `/scenario` | Save/update scenario configuration |
| GET | `/events` | Get play-by-play events |
| GET | `/report` | Get generated report |
| POST | `/report/generate` | Trigger report generation |
| GET | `/report/status` | Check report generation status |
| POST | `/chat` | Chat with a game participant |
| GET | `/reactions/<workspace_id>` | Get fan/commentator reactions |
| GET | `/pregame/<workspace_id>` | Get pre-game content |
| POST | `/pregame/<workspace_id>` | Generate pre-game content |
| GET | `/postgame/<workspace_id>` | Get post-game content |
| POST | `/postgame/<workspace_id>` | Generate post-game content |

## Project Structure

```
Hermes/
├── backend/
│   ├── run.py                        # Flask entry point
│   ├── app/
│   │   ├── config.py                 # Configuration from .env
│   │   ├── api/
│   │   │   └── sports.py             # Sports simulation endpoints
│   │   ├── models/
│   │   │   ├── task.py               # Async task tracking
│   │   │   └── sports_workspace.py   # Sports workspace model
│   │   ├── services/
│   │   │   ├── sports_simulator.py           # Main simulation engine
│   │   │   ├── basketball_multi_agent.py     # Basketball multi-agent engine
│   │   │   ├── sports_fan_agents.py          # Fan agent reaction system
│   │   │   ├── sports_commentator_agents.py  # Commentator broadcast system
│   │   │   ├── sports_pregame.py             # Pre-game hype generation
│   │   │   ├── sports_postgame.py            # Post-game analysis generation
│   │   │   ├── sports_planner.py             # Team research & profile building
│   │   │   ├── sports_data_provider.py       # Perplexity research integration
│   │   │   ├── sports_rule_packs.py          # Sport-specific rule definitions
│   │   │   ├── sports_profiles.py            # Player/coach profile generation
│   │   │   ├── sports_reporter.py            # Report generation & persona chat
│   │   │   └── sports_workspace.py           # Workspace management
│   │   └── utils/
│   │       ├── llm_client.py         # OpenAI-compatible LLM wrapper
│   │       ├── locale.py             # Thread-local i18n
│   │       ├── logger.py             # Logging utilities
│   │       └── retry.py              # Retry with backoff
│   └── tests/
│       ├── test_basketball_multi_agent.py
│       └── test_sports_profiles.py
├── frontend/
│   └── src/
│       ├── views/
│       │   ├── Home.vue              # Sports landing page
│       │   └── SportsProcessView.vue # 5-step simulation workflow
│       ├── components/
│       │   └── LanguageSwitcher.vue  # i18n language selector
│       ├── api/
│       │   ├── index.js              # Axios client setup
│       │   └── sports.js             # Sports API functions
│       ├── i18n/                     # Vue I18n setup
│       ├── router/                   # Vue Router
│       └── App.vue                   # Root component (dark ESPN theme)
├── locales/                          # Translation files (7 languages)
├── docker-compose.yml
├── Dockerfile
└── package.json
```

## Acknowledgments

We would like to sincerely thank **[MiroFish](https://github.com/666ghj/MiroFish)** for inspiring this project. Their vision of a concise and versatile group intelligence engine laid the foundation for Hermes.

## License

This project is licensed under the MIT License -- see the [LICENSE](./LICENSE) file for details.
