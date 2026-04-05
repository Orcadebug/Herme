<template>
  <div class="scoreboard-ticker">
    <div class="team-info home">
      <div class="team-logo-placeholder">
        {{ homeTeam.charAt(0).toUpperCase() }}
      </div>
      <div class="team-details">
        <span class="team-name">{{ homeTeam }}</span>
        <span class="team-record">HOME</span>
      </div>
    </div>

    <div class="score-center">
      <div class="score-display">
        <span class="score" :class="{ flash: scoreFlash === 'home' }">{{ homeScore }}</span>
        <span class="separator">-</span>
        <span class="score" :class="{ flash: scoreFlash === 'away' }">{{ awayScore }}</span>
      </div>
      <div class="game-info">
        <span v-if="isComplete" class="final-badge">FINAL</span>
        <template v-else>
          <span class="period">{{ period }}</span>
          <span class="clock">{{ gameClock }}</span>
          <span v-if="isRunning" class="live-indicator">
            <span class="live-dot"></span> LIVE
          </span>
        </template>
      </div>
      <div class="fouls-timeouts">
        <div class="foul-count">
          <span class="label">Fouls</span>
          <span class="value">{{ homeFouls }}</span>
          <span class="separator">-</span>
          <span class="value">{{ awayFouls }}</span>
        </div>
        <div class="timeout-dots">
          <span class="label">TO</span>
          <div class="dots">
            <span v-for="i in 7" :key="'h' + i" class="dot" :class="{ filled: i <= homeTimeouts, home: true }"></span>
          </div>
          <div class="dots">
            <span v-for="i in 7" :key="'a' + i" class="dot" :class="{ filled: i <= awayTimeouts, away: true }"></span>
          </div>
        </div>
      </div>
    </div>

    <div class="team-info away">
      <div class="team-details">
        <span class="team-name">{{ awayTeam }}</span>
        <span class="team-record">AWAY</span>
      </div>
      <div class="team-logo-placeholder">
        {{ awayTeam.charAt(0).toUpperCase() }}
      </div>
    </div>

    <div v-if="possession" class="possession-arrow" :class="possession">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12 2L4 14h5v8h6v-8h5z"/></svg>
    </div>

    <div v-if="!isRunning && !isComplete" class="start-overlay">
      <button class="start-btn" @click="$emit('start')">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        Start Game
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  homeTeam: { type: String, default: '' },
  awayTeam: { type: String, default: '' },
  homeScore: { type: Number, default: 0 },
  awayScore: { type: Number, default: 0 },
  gameClock: { type: String, default: '12:00' },
  period: { type: String, default: '1st' },
  possession: { type: String, default: null },
  homeFouls: { type: Number, default: 0 },
  awayFouls: { type: Number, default: 0 },
  homeTimeouts: { type: Number, default: 7 },
  awayTimeouts: { type: Number, default: 7 },
  sport: { type: String, default: 'basketball' },
  isRunning: { type: Boolean, default: false },
  isComplete: { type: Boolean, default: false },
  scoreFlash: { type: String, default: '' }
})

defineEmits(['start'])
</script>

<style scoped>
.scoreboard-ticker {
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, rgba(10, 22, 40, 0.98), rgba(19, 34, 56, 0.98));
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 14px 24px;
  backdrop-filter: blur(16px);
}

.team-info {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 180px;
}

.team-info.away {
  flex-direction: row-reverse;
}

.team-logo-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, var(--accent-blue), #00c6ff);
  border-radius: 50%;
  font-size: 22px;
  font-weight: 800;
  color: white;
}

.team-info.away .team-logo-placeholder {
  background: linear-gradient(135deg, var(--accent-orange), #ff9a5c);
}

.team-details {
  display: flex;
  flex-direction: column;
}

.team-name {
  font-size: 16px;
  font-weight: 700;
}

.team-record {
  font-size: 11px;
  color: var(--text-secondary);
  letter-spacing: 0.08em;
}

.score-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.score-display {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score {
  font-size: 42px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  transition: all 0.3s;
}

.score.flash {
  color: var(--success);
  text-shadow: 0 0 20px rgba(0, 230, 118, 0.5);
}

.separator {
  font-size: 28px;
  color: var(--text-secondary);
  font-weight: 300;
}

.game-info {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.period {
  color: var(--text-secondary);
  font-weight: 600;
}

.clock {
  color: var(--text-primary);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.final-badge {
  background: var(--accent-orange);
  color: white;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.1em;
}

.live-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--danger);
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 0.08em;
}

.live-dot {
  width: 6px;
  height: 6px;
  background: var(--danger);
  border-radius: 50%;
  animation: livePulse 1.5s ease-in-out infinite;
}

@keyframes livePulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.fouls-timeouts {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 11px;
}

.foul-count {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--text-secondary);
}

.foul-count .value {
  color: var(--text-primary);
  font-weight: 700;
}

.timeout-dots {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary);
}

.dots {
  display: flex;
  gap: 3px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
}

.dot.filled {
  background: var(--accent-blue);
}

.dot.filled.away {
  background: var(--accent-orange);
}

.possession-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
}

.possession-arrow.home {
  left: 200px;
  color: var(--accent-blue);
}

.possession-arrow.away {
  right: 200px;
  color: var(--accent-orange);
}

.start-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(10, 22, 40, 0.85);
  border-radius: 14px;
  backdrop-filter: blur(4px);
}

.start-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--accent-orange);
  border: none;
  color: white;
  padding: 14px 32px;
  border-radius: 10px;
  font: inherit;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.start-btn:hover {
  background: #e85a28;
  box-shadow: 0 6px 24px rgba(255, 107, 53, 0.3);
  transform: translateY(-2px);
}

@media (max-width: 768px) {
  .scoreboard-ticker {
    flex-direction: column;
    gap: 12px;
    padding: 12px 16px;
  }

  .team-info {
    min-width: auto;
    width: 100%;
    justify-content: center;
  }

  .score {
    font-size: 32px;
  }

  .fouls-timeouts {
    display: none;
  }
}
</style>
