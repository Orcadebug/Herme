<template>
  <div class="postgame-view">
    <div class="panel-header">
      <h1 class="panel-title">Post-Game Report</h1>
      <p class="panel-subtitle">
        <template v-if="simulation?.status === 'completed'">
          Final: {{ simulation.home_team || homeTeam }} {{ simulation.home_score ?? 0 }} - {{ simulation.away_score ?? 0 }} {{ simulation.away_team || awayTeam }}
        </template>
        <template v-else>Game summary and analysis</template>
      </p>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="skeleton-line"></div>
      <div class="skeleton-line short"></div>
      <div class="skeleton-grid">
        <div class="skeleton-card"></div>
        <div class="skeleton-card"></div>
      </div>
    </div>

    <div v-else class="postgame-content">
      <section class="final-score-section">
        <div class="final-score-card">
          <div class="final-team">
            <div class="team-logo-placeholder home-logo">
              {{ (simulation?.home_team || homeTeam).charAt(0).toUpperCase() }}
            </div>
            <div class="team-info">
              <span class="team-name">{{ simulation?.home_team || homeTeam }}</span>
              <span class="team-label">HOME</span>
            </div>
          </div>
          <div class="final-score-display">
            <span class="final-score" :class="{ winner: isHomeWinner }">{{ simulation?.home_score ?? 0 }}</span>
            <span class="separator">-</span>
            <span class="final-score" :class="{ winner: !isHomeWinner }">{{ simulation?.away_score ?? 0 }}</span>
            <span class="final-badge">FINAL</span>
          </div>
          <div class="final-team away">
            <div class="team-info">
              <span class="team-name">{{ simulation?.away_team || awayTeam }}</span>
              <span class="team-label">AWAY</span>
            </div>
            <div class="team-logo-placeholder away-logo">
              {{ (simulation?.away_team || awayTeam).charAt(0).toUpperCase() }}
            </div>
          </div>
        </div>
      </section>

      <section class="box-score-section">
        <h2 class="section-title">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
          Box Score
        </h2>
        <div v-if="boxScore.length > 0" class="box-score-table">
          <table>
            <thead>
              <tr>
                <th>Player</th>
                <th>PTS</th>
                <th>REB</th>
                <th>AST</th>
                <th>STL</th>
                <th>BLK</th>
                <th>FG%</th>
                <th>MIN</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in boxScore" :key="row.name" :class="{ 'home-row': row.team === 'home', 'away-row': row.team === 'away' }">
                <td class="player-cell">
                  <span class="jersey">#{{ row.number }}</span>
                  {{ row.name }}
                </td>
                <td class="stat-cell">{{ row.PTS }}</td>
                <td class="stat-cell">{{ row.REB }}</td>
                <td class="stat-cell">{{ row.AST }}</td>
                <td class="stat-cell">{{ row.STL }}</td>
                <td class="stat-cell">{{ row.BLK }}</td>
                <td class="stat-cell">{{ row.FG }}</td>
                <td class="stat-cell">{{ row.MIN }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="placeholder-card">Box score will be generated after the game completes.</div>
      </section>

      <section class="grades-section">
        <h2 class="section-title">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          Performance Grades
        </h2>
        <div class="grades-grid">
          <div v-for="grade in grades" :key="grade.name" class="grade-card">
            <span class="grade-player">{{ grade.name }}</span>
            <span class="grade-letter" :class="grade.grade.toLowerCase()">{{ grade.grade }}</span>
          </div>
          <div v-if="!grades.length" class="placeholder-card">Grades will be assigned after analysis.</div>
        </div>
      </section>

      <section class="top-performers-section">
        <h2 class="section-title">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
          Top Performers
        </h2>
        <div class="performers-grid">
          <div v-for="performer in topPerformers" :key="performer.name" class="performer-card">
            <div class="performer-rank">#{{ performer.rank }}</div>
            <div class="performer-info">
              <span class="performer-name">{{ performer.name }}</span>
              <span class="performer-team">{{ performer.team }}</span>
              <span class="performer-stat">{{ performer.stat }}</span>
            </div>
          </div>
          <div v-if="!topPerformers.length" class="placeholder-card">Top performers will be highlighted here.</div>
        </div>
      </section>

      <section class="game-ball-section">
        <h2 class="section-title">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="7"/><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/></svg>
          Game Ball
        </h2>
        <div v-if="gameBall" class="game-ball-card">
          <div class="game-ball-avatar">
            {{ gameBall.name?.charAt(0).toUpperCase() || 'M' }}
          </div>
          <div class="game-ball-info">
            <h3 class="game-ball-name">{{ gameBall.name }}</h3>
            <p class="game-ball-team">{{ gameBall.team }}</p>
            <p class="game-ball-reason">{{ gameBall.reason }}</p>
          </div>
        </div>
        <div v-else class="placeholder-card">MVP will be awarded after the game.</div>
      </section>

      <section class="quotes-section">
        <h2 class="section-title">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          Press Conference
        </h2>
        <div class="quotes-grid">
          <div v-for="quote in quotes" :key="quote.speaker" class="quote-card">
            <div class="quote-speaker">
              <span class="speaker-name">{{ quote.speaker }}</span>
              <span class="speaker-role">{{ quote.role }}</span>
            </div>
            <blockquote class="quote-text">"{{ quote.text }}"</blockquote>
          </div>
          <div v-if="!quotes.length" class="placeholder-card">Post-game quotes will appear here.</div>
        </div>
      </section>

      <section class="media-section">
        <h2 class="section-title">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
          Media Reaction
        </h2>
        <div class="media-grid">
          <div v-for="item in mediaReaction" :key="item.source" class="media-card">
            <span class="media-source">{{ item.source }}</span>
            <p class="media-text">{{ item.text }}</p>
          </div>
          <div v-if="!mediaReaction.length" class="placeholder-card">Media roundup will appear here.</div>
        </div>
      </section>

      <div class="action-bar">
        <button class="load-btn" @click="$emit('load')" :disabled="loading">
          <svg v-if="!loading" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
          <svg v-else class="spin" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 11-6.219-8.56"/></svg>
          {{ loading ? 'Loading...' : 'Load Full Report' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  workspaceId: { type: String, default: '' },
  simulation: { type: Object, default: null },
  events: { type: Array, default: () => [] },
  postgameData: { type: Object, default: null },
  loading: { type: Boolean, default: false }
})

defineEmits(['load'])

const homeTeam = computed(() => props.simulation?.home_team || '')
const awayTeam = computed(() => props.simulation?.away_team || '')
const isHomeWinner = computed(() => (props.simulation?.home_score ?? 0) >= (props.simulation?.away_score ?? 0))

const boxScore = computed(() => props.postgameData?.boxScore || [])
const grades = computed(() => props.postgameData?.grades || [])
const topPerformers = computed(() => props.postgameData?.topPerformers || [])
const gameBall = computed(() => props.postgameData?.gameBall || null)
const quotes = computed(() => props.postgameData?.quotes || [])
const mediaReaction = computed(() => props.postgameData?.mediaReaction || [])
</script>

<style scoped>
.postgame-view {
  --bg-primary: #0a1628;
  --bg-card: #132238;
  --bg-card-hover: #1a2d4a;
  --accent-blue: #0078ff;
  --accent-orange: #ff6b35;
  --text-primary: #ffffff;
  --text-secondary: #8899aa;
  --border-subtle: rgba(255, 255, 255, 0.08);
  --border-accent: rgba(0, 120, 255, 0.3);
  --success: #00e676;
  --danger: #ff4d4d;
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

.postgame-content {
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

.final-score-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, rgba(10, 22, 40, 0.95), rgba(19, 34, 56, 0.95));
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 24px 32px;
}

.final-team {
  display: flex;
  align-items: center;
  gap: 14px;
}

.final-team.away {
  flex-direction: row-reverse;
}

.team-logo-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  font-size: 24px;
  font-weight: 800;
  color: white;
}

.home-logo {
  background: linear-gradient(135deg, var(--accent-blue), #00c6ff);
}

.away-logo {
  background: linear-gradient(135deg, var(--accent-orange), #ff9a5c);
}

.team-info {
  display: flex;
  flex-direction: column;
}

.team-name {
  font-size: 18px;
  font-weight: 700;
}

.team-label {
  font-size: 11px;
  color: var(--text-secondary);
  letter-spacing: 0.08em;
}

.final-score-display {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-direction: column;
}

.final-score {
  font-size: 48px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.final-score.winner {
  color: var(--success);
}

.separator {
  font-size: 24px;
  color: var(--text-secondary);
}

.final-badge {
  background: var(--accent-orange);
  color: white;
  padding: 4px 16px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.1em;
}

.box-score-table {
  overflow-x: auto;
  border-radius: 12px;
  border: 1px solid var(--border-subtle);
}

.box-score-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.box-score-table th {
  background: var(--bg-card-hover);
  padding: 10px 12px;
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-subtle);
}

.box-score-table td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-subtle);
}

.player-cell {
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.jersey {
  font-size: 11px;
  color: var(--accent-blue);
  font-weight: 700;
}

.stat-cell {
  text-align: center;
  font-variant-numeric: tabular-nums;
}

.home-row {
  background: rgba(0, 120, 255, 0.03);
}

.away-row {
  background: rgba(255, 107, 53, 0.03);
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

.grades-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
}

.grade-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  text-align: center;
}

.grade-player {
  font-size: 12px;
  font-weight: 600;
}

.grade-letter {
  font-size: 28px;
  font-weight: 800;
}

.grade-letter.a { color: var(--success); }
.grade-letter.b { color: var(--accent-blue); }
.grade-letter.c { color: #ffd700; }
.grade-letter.d { color: var(--accent-orange); }
.grade-letter.f { color: var(--danger); }

.performers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
}

.performer-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
}

.performer-rank {
  font-size: 24px;
  font-weight: 800;
  color: var(--accent-orange);
}

.performer-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.performer-name {
  font-size: 14px;
  font-weight: 700;
}

.performer-team {
  font-size: 11px;
  color: var(--text-secondary);
}

.performer-stat {
  font-size: 12px;
  color: var(--accent-blue);
  font-weight: 600;
}

.game-ball-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 24px;
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.05), rgba(255, 107, 53, 0.05));
  border: 1px solid rgba(255, 215, 0, 0.2);
  border-radius: 14px;
}

.game-ball-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #ffd700, #ff6b35);
  border-radius: 50%;
  font-size: 28px;
  font-weight: 800;
  color: white;
}

.game-ball-name {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 4px;
}

.game-ball-team {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 8px;
}

.game-ball-reason {
  font-size: 14px;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.5;
}

.quotes-grid {
  display: grid;
  gap: 12px;
}

.quote-card {
  padding: 16px 20px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  border-left: 3px solid var(--accent-blue);
}

.quote-speaker {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.speaker-name {
  font-size: 14px;
  font-weight: 700;
}

.speaker-role {
  font-size: 12px;
  color: var(--text-secondary);
}

.quote-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  font-style: italic;
}

.media-grid {
  display: grid;
  gap: 12px;
}

.media-card {
  padding: 14px 18px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
}

.media-source {
  font-size: 12px;
  font-weight: 700;
  color: var(--accent-blue);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.media-text {
  margin: 6px 0 0;
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-primary);
}

.action-bar {
  display: flex;
  justify-content: center;
  padding-top: 16px;
}

.load-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--accent-blue);
  border: none;
  color: white;
  padding: 14px 32px;
  border-radius: 10px;
  font: inherit;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.load-btn:hover:not(:disabled) {
  background: #0066dd;
  box-shadow: 0 6px 24px rgba(0, 120, 255, 0.3);
  transform: translateY(-2px);
}

.load-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .final-score-card {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .final-team,
  .final-team.away {
    flex-direction: column;
  }

  .grades-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
