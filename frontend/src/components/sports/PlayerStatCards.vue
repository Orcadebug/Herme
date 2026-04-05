<template>
  <div class="player-stat-cards">
    <div class="cards-header">
      <h3 class="cards-title">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        Player Stats
      </h3>
      <div class="team-toggle">
        <button
          class="toggle-btn"
          :class="{ active: activeTeam === 'home' }"
          @click="$emit('team-change', 'home')"
        >
          {{ homeTeam }}
        </button>
        <button
          class="toggle-btn"
          :class="{ active: activeTeam === 'away' }"
          @click="$emit('team-change', 'away')"
        >
          {{ awayTeam }}
        </button>
      </div>
    </div>

    <div class="cards-body">
      <div v-if="playerCards.length === 0" class="cards-empty">
        <p>Player stats will appear once the game starts.</p>
      </div>

      <div class="player-grid">
        <div
          v-for="player in playerCards"
          :key="player.name"
          class="player-card"
          :class="{ hot: player.isHot, cold: player.isCold }"
        >
          <div class="player-top">
            <span class="jersey-num">#{{ player.number }}</span>
            <span class="player-name">{{ player.name }}</span>
            <span class="player-pos">{{ player.position }}</span>
          </div>
          <div class="player-stats">
            <div v-for="(val, key) in player.stats" :key="key" class="stat-cell">
              <span class="stat-val">{{ val }}</span>
              <span class="stat-key">{{ key }}</span>
            </div>
          </div>
          <div v-if="player.isHot" class="hot-indicator">
            <svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M12 2c.5 3.5 2 6 4 8-1 3-3 5-4 6-1-1-3-3-4-6 2-2 3.5-4.5 4-8z"/></svg>
            HOT
          </div>
          <div v-if="player.isCold" class="cold-indicator">
            <svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M12 2v20M7 7l5-5 5 5M7 17l5 5 5-5"/></svg>
            COLD
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  homeTeam: { type: String, default: '' },
  awayTeam: { type: String, default: '' },
  events: { type: Array, default: () => [] },
  sport: { type: String, default: 'basketball' },
  activeTeam: { type: String, default: 'home' }
})

defineEmits(['team-change'])

const playerCards = computed(() => {
  const teamName = props.activeTeam === 'home' ? props.homeTeam : props.awayTeam
  const teamEvents = props.events.filter(e => e.team === props.activeTeam)

  const playerMap = {}
  teamEvents.forEach(e => {
    const name = e.actor || 'Player'
    if (!playerMap[name]) {
      playerMap[name] = {
        name,
        number: Math.floor(Math.random() * 99) + 1,
        position: props.sport === 'basketball' ? ['PG', 'SG', 'SF', 'PF', 'C'][Math.floor(Math.random() * 5)] : 'Player',
        stats: props.sport === 'basketball'
          ? { PTS: 0, REB: 0, AST: 0, STL: 0, BLK: 0, 'FG%': '0' }
          : { G: 0, A: 0, S: 0, T: 0 },
        shotAttempts: 0,
        shotMade: 0
      }
    }
    const p = playerMap[name]
    if (e.actionType === 'shot') {
      p.shotAttempts++
      const made = e.outcome?.toLowerCase().includes('made') || e.outcome?.toLowerCase().includes('score')
      if (made) {
        p.shotMade++
        p.stats.PTS = (p.stats.PTS || 0) + (e.description?.toLowerCase().includes('three') ? 3 : 2)
      }
      p.stats['FG%'] = p.shotAttempts > 0 ? Math.round((p.shotMade / p.shotAttempts) * 100) + '%' : '0%'
    }
    if (e.actionType === 'rebound') p.stats.REB = (p.stats.REB || 0) + 1
    if (e.actionType === 'assist') { p.stats.AST = (p.stats.AST || 0) + 1; p.stats.PTS = (p.stats.PTS || 0) }
    if (e.actionType === 'steal') p.stats.STL = (p.stats.STL || 0) + 1
    if (e.actionType === 'block') p.stats.BLK = (p.stats.BLK || 0) + 1
  })

  return Object.values(playerMap).map(p => ({
    ...p,
    isHot: (p.stats.PTS || 0) >= 15,
    isCold: p.shotAttempts >= 3 && p.shotMade === 0
  })).sort((a, b) => (b.stats.PTS || 0) - (a.stats.PTS || 0))
})
</script>

<style scoped>
.player-stat-cards {
  --bg-primary: #0a1628;
  --bg-card: #132238;
  --bg-card-hover: #1a2d4a;
  --accent-blue: #0078ff;
  --accent-orange: #ff6b35;
  --text-primary: #ffffff;
  --text-secondary: #8899aa;
  --border-subtle: rgba(255, 255, 255, 0.08);
  --success: #00e676;
  --danger: #ff4d4d;

  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: 600px;
}

.cards-header {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cards-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  margin: 0;
}

.cards-title svg {
  color: var(--accent-blue);
}

.team-toggle {
  display: flex;
  gap: 4px;
}

.toggle-btn {
  padding: 4px 10px;
  background: none;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  color: var(--text-secondary);
  cursor: pointer;
  font: inherit;
  font-size: 11px;
  font-weight: 600;
  transition: all 0.2s;
}

.toggle-btn.active {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}

.toggle-btn:last-child.active {
  background: var(--accent-orange);
  border-color: var(--accent-orange);
}

.cards-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.cards-body::-webkit-scrollbar {
  width: 4px;
}

.cards-body::-webkit-scrollbar-thumb {
  background: var(--border-subtle);
  border-radius: 2px;
}

.cards-empty {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-secondary);
  font-size: 13px;
}

.player-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.player-card {
  background: rgba(10, 22, 40, 0.5);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  padding: 12px;
  position: relative;
  transition: all 0.2s;
}

.player-card:hover {
  border-color: var(--border-accent);
}

.player-card.hot {
  border-color: rgba(0, 230, 118, 0.3);
  box-shadow: 0 0 12px rgba(0, 230, 118, 0.1);
}

.player-card.cold {
  border-color: rgba(255, 77, 77, 0.3);
  box-shadow: 0 0 12px rgba(255, 77, 77, 0.1);
}

.player-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.jersey-num {
  font-size: 14px;
  font-weight: 800;
  color: var(--accent-blue);
}

.player-name {
  flex: 1;
  font-size: 13px;
  font-weight: 600;
}

.player-pos {
  font-size: 11px;
  color: var(--text-secondary);
  background: var(--bg-card-hover);
  padding: 2px 6px;
  border-radius: 4px;
}

.player-stats {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 4px;
}

.stat-cell {
  text-align: center;
}

.stat-val {
  display: block;
  font-size: 14px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.stat-key {
  display: block;
  font-size: 9px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.hot-indicator,
.cold-indicator {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.hot-indicator {
  color: var(--success);
}

.cold-indicator {
  color: var(--danger);
}
</style>
