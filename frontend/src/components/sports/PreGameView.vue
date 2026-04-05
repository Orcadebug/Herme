<template>
  <div class="pregame-view">
    <div class="panel-header">
      <h1 class="panel-title">Pre-Game</h1>
      <p class="panel-subtitle">{{ homeTeam }} vs {{ awayTeam }} · {{ sportDisplay }}</p>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="skeleton-line"></div>
      <div class="skeleton-line short"></div>
      <div class="skeleton-grid">
        <div class="skeleton-card"></div>
        <div class="skeleton-card"></div>
      </div>
    </div>

    <div v-else class="pregame-content">
      <section class="storylines-section">
        <h2 class="section-title">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          Key Storylines
        </h2>
        <div class="storyline-cards">
          <div v-for="(storyline, i) in storylines" :key="i" class="storyline-card">
            <span class="storyline-number">{{ i + 1 }}</span>
            <p class="storyline-text">{{ storyline }}</p>
          </div>
          <div v-if="!storylines.length" class="placeholder-card">Storylines will appear once research is complete.</div>
        </div>
      </section>

      <section class="matchups-section">
        <h2 class="section-title">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          Key Matchups
        </h2>
        <div class="matchup-grid">
          <div v-for="(matchup, i) in matchups" :key="i" class="matchup-card">
            <div class="matchup-players">
              <span class="player home">{{ matchup.home }}</span>
              <span class="vs">vs</span>
              <span class="player away">{{ matchup.away }}</span>
            </div>
            <p class="matchup-desc">{{ matchup.description }}</p>
          </div>
          <div v-if="!matchups.length" class="placeholder-card">Key matchups will appear here.</div>
        </div>
      </section>

      <section class="lineups-section">
        <h2 class="section-title">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="14" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          Predicted Lineups
        </h2>
        <div class="lineups-grid">
          <div class="lineup-card home-lineup">
            <h3 class="lineup-team">{{ homeTeam }}</h3>
            <ul class="lineup-list">
              <li v-for="(player, i) in homeLineup" :key="i" class="lineup-player">
                <span class="jersey">{{ player.number }}</span>
                <span class="name">{{ player.name }}</span>
                <span class="position">{{ player.position }}</span>
              </li>
              <li v-if="!homeLineup.length" class="placeholder-item">Lineup pending...</li>
            </ul>
          </div>
          <div class="lineup-card away-lineup">
            <h3 class="lineup-team">{{ awayTeam }}</h3>
            <ul class="lineup-list">
              <li v-for="(player, i) in awayLineup" :key="i" class="lineup-player">
                <span class="jersey">{{ player.number }}</span>
                <span class="name">{{ player.name }}</span>
                <span class="position">{{ player.position }}</span>
              </li>
              <li v-if="!awayLineup.length" class="placeholder-item">Lineup pending...</li>
            </ul>
          </div>
        </div>
      </section>

      <section class="watch-for-section">
        <h2 class="section-title">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          What to Watch For
        </h2>
        <ul class="watch-list">
          <li v-for="(item, i) in watchFor" :key="i" class="watch-item">
            <span class="watch-bullet"></span>
            {{ item }}
          </li>
          <li v-if="!watchFor.length" class="placeholder-item">Key observations will appear here.</li>
        </ul>
      </section>

      <div class="action-bar">
        <button class="begin-btn" @click="$emit('begin-simulation')">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          Begin Simulation
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  workspaceId: { type: String, default: '' },
  homeTeam: { type: String, default: '' },
  awayTeam: { type: String, default: '' },
  sport: { type: String, default: 'basketball' },
  pregameData: { type: Object, default: null },
  loading: { type: Boolean, default: false }
})

defineEmits(['begin-simulation'])

const sportDisplay = computed(() => {
  const map = { basketball: 'Basketball', soccer: 'Soccer', football: 'American Football' }
  return map[props.sport] || props.sport
})

const storylines = computed(() => props.pregameData?.storylines || [])
const matchups = computed(() => props.pregameData?.matchups || [])
const homeLineup = computed(() => props.pregameData?.lineups?.home || [])
const awayLineup = computed(() => props.pregameData?.lineups?.away || [])
const watchFor = computed(() => props.pregameData?.watchFor || [])
</script>

<style scoped>
.pregame-view {
  --bg-primary: #0a1628;
  --bg-card: #132238;
  --bg-card-hover: #1a2d4a;
  --accent-blue: #0078ff;
  --accent-orange: #ff6b35;
  --text-primary: #ffffff;
  --text-secondary: #8899aa;
  --border-subtle: rgba(255, 255, 255, 0.08);
  --border-accent: rgba(0, 120, 255, 0.3);
}

.panel-header {
  margin-bottom: 32px;
}

.panel-title {
  font-size: 32px;
  font-weight: 800;
  margin: 0 0 8px;
  background: linear-gradient(135deg, var(--text-primary), var(--accent-blue));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.panel-subtitle {
  color: var(--text-secondary);
  font-size: 15px;
  margin: 0;
}

.loading-state {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 24px;
}

.skeleton-line {
  height: 14px;
  background: linear-gradient(90deg, var(--bg-card-hover) 25%, rgba(255, 255, 255, 0.08) 50%, var(--bg-card-hover) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 6px;
  margin-bottom: 12px;
}

.skeleton-line.short { width: 60%; }

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-top: 16px;
}

.skeleton-card {
  height: 100px;
  background: linear-gradient(90deg, var(--bg-card-hover) 25%, rgba(255, 255, 255, 0.08) 50%, var(--bg-card-hover) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 10px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.pregame-content {
  display: grid;
  gap: 32px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 16px;
  color: var(--text-primary);
}

.section-title svg {
  color: var(--accent-blue);
}

.storyline-cards {
  display: grid;
  gap: 12px;
}

.storyline-card {
  display: flex;
  gap: 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 16px 20px;
  transition: border-color 0.2s;
}

.storyline-card:hover {
  border-color: var(--border-accent);
}

.storyline-number {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 28px;
  background: var(--accent-blue);
  color: white;
  border-radius: 50%;
  font-size: 13px;
  font-weight: 700;
}

.storyline-text {
  margin: 0;
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.6;
}

.matchup-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.matchup-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 16px;
}

.matchup-players {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.player {
  font-size: 14px;
  font-weight: 600;
}

.player.home { color: var(--accent-blue); }
.player.away { color: var(--accent-orange); }

.vs {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 700;
}

.matchup-desc {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.lineups-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.lineup-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 16px;
}

.home-lineup { border-top: 3px solid var(--accent-blue); }
.away-lineup { border-top: 3px solid var(--accent-orange); }

.lineup-team {
  font-size: 16px;
  font-weight: 700;
  margin: 0 0 12px;
}

.lineup-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 6px;
}

.lineup-player {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
  font-size: 13px;
}

.jersey {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 26px;
  height: 26px;
  background: var(--bg-card-hover);
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-secondary);
}

.name {
  flex: 1;
  font-weight: 600;
}

.position {
  font-size: 11px;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.placeholder-item {
  color: var(--text-secondary);
  font-size: 13px;
  font-style: italic;
  padding: 8px 0;
}

.placeholder-card {
  color: var(--text-secondary);
  font-size: 14px;
  font-style: italic;
  text-align: center;
  padding: 24px;
  background: var(--bg-card);
  border: 1px dashed var(--border-subtle);
  border-radius: 12px;
}

.watch-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 10px;
}

.watch-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.5;
}

.watch-bullet {
  display: inline-block;
  min-width: 8px;
  height: 8px;
  background: var(--accent-orange);
  border-radius: 50%;
  margin-top: 6px;
}

.action-bar {
  display: flex;
  justify-content: center;
  padding-top: 16px;
}

.begin-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--accent-orange);
  border: none;
  color: var(--text-primary);
  padding: 16px 40px;
  border-radius: 12px;
  font: inherit;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.begin-btn:hover {
  background: #e85a28;
  box-shadow: 0 6px 24px rgba(255, 107, 53, 0.3);
  transform: translateY(-2px);
}

@media (max-width: 960px) {
  .lineups-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .panel-title { font-size: 24px; }
  .matchup-grid { grid-template-columns: 1fr; }
}
</style>
