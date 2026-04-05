<template>
  <div class="matchup-setup">
    <div class="panel-header">
      <h1 class="panel-title">Matchup Setup</h1>
      <p class="panel-subtitle">Configure your teams and sport to begin the simulation</p>
    </div>

    <div class="setup-grid">
      <div class="team-inputs">
        <div class="team-card home">
          <div class="team-badge">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
            HOME
          </div>
          <div class="input-wrapper">
            <svg class="search-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
            <input
              :value="homeTeam"
              @input="$emit('update:home-team', $event.target.value)"
              placeholder="Home team (e.g. Lakers)"
              class="team-input"
            />
          </div>
        </div>

        <div class="vs-divider">VS</div>

        <div class="team-card away">
          <div class="team-badge">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
            AWAY
          </div>
          <div class="input-wrapper">
            <svg class="search-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
            <input
              :value="awayTeam"
              @input="$emit('update:away-team', $event.target.value)"
              placeholder="Away team (e.g. Celtics)"
              class="team-input"
            />
          </div>
        </div>
      </div>

      <div class="sport-selector">
        <h3 class="section-label">Select Sport</h3>
        <div class="sport-options">
          <button
            v-for="sport in sportOptions"
            :key="sport.id"
            class="sport-option"
            :class="{ active: sport === selectedSport }"
            @click="$emit('update:sport', sport.id)"
          >
            <div class="sport-icon" v-html="sport.icon"></div>
            <span class="sport-name">{{ sport.name }}</span>
          </button>
        </div>

        <div class="league-input">
          <label class="field-label">League (Optional)</label>
          <input
            :value="league"
            @input="$emit('update:league', $event.target.value)"
            placeholder="e.g. NBA, Premier League, NFL"
            class="text-input"
          />
        </div>
      </div>
    </div>

    <div class="action-bar">
      <button
        class="research-btn"
        :disabled="researching || !canResearch"
        @click="$emit('research')"
      >
        <svg v-if="!researching" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <svg v-else class="spin" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 11-6.219-8.56"/></svg>
        {{ researching ? 'Researching...' : 'Research Teams' }}
      </button>

      <button
        class="simulate-btn"
        :disabled="!canSimulate"
        @click="$emit('start-simulation')"
      >
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        Start Simulation
      </button>
    </div>

    <div v-if="researching" class="skeleton-section">
      <div class="skeleton-line"></div>
      <div class="skeleton-line short"></div>
      <div class="skeleton-grid">
        <div class="skeleton-card"></div>
        <div class="skeleton-card"></div>
        <div class="skeleton-card"></div>
      </div>
    </div>

    <div v-if="workspace && !researching" class="research-results">
      <div class="result-header">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        Research Complete
      </div>
      <div class="dossier-summary">
        <div class="dossier-stat">
          <span class="stat-value">{{ workspace.dossier_index?.length || 0 }}</span>
          <span class="stat-label">Dossiers</span>
        </div>
        <div class="dossier-stat">
          <span class="stat-value">{{ workspace.participants?.length || 0 }}</span>
          <span class="stat-label">Participants</span>
        </div>
        <div class="dossier-stat">
          <span class="stat-value">{{ workspace.source_links?.length || 0 }}</span>
          <span class="stat-label">Sources</span>
        </div>
      </div>
      <p v-if="workspace.matchup_summary" class="matchup-summary">{{ workspace.matchup_summary }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  homeTeam: { type: String, default: '' },
  awayTeam: { type: String, default: '' },
  sport: { type: String, default: 'basketball' },
  league: { type: String, default: '' },
  researching: { type: Boolean, default: false },
  researchComplete: { type: Boolean, default: false },
  workspace: { type: Object, default: null }
})

defineEmits(['update:home-team', 'update:away-team', 'update:sport', 'update:league', 'research', 'start-simulation'])

const selectedSport = computed(() => props.sport)

const canResearch = computed(() => props.homeTeam.trim() && props.awayTeam.trim())
const canSimulate = computed(() => canResearch.value && (props.researchComplete || props.workspace?.status === 'ready'))

const sportOptions = [
  {
    id: 'basketball',
    name: 'Basketball',
    icon: `<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2"><circle cx="32" cy="32" r="28"/><path d="M32 4v56M4 32h56M12 12c10 8 16 20 16 20s6-12 16-20M12 52c10-8 16-20 16-20s6 12 16 20"/></svg>`
  },
  {
    id: 'soccer',
    name: 'Soccer',
    icon: `<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2"><circle cx="32" cy="32" r="28"/><polygon points="32,12 42,22 38,34 26,34 22,22"/><line x1="32" y1="12" x2="32" y2="4"/><line x1="42" y1="22" x2="50" y2="18"/><line x1="38" y1="34" x2="44" y2="42"/><line x1="26" y1="34" x2="20" y2="42"/><line x1="22" y1="22" x2="14" y2="18"/></svg>`
  },
  {
    id: 'football',
    name: 'American Football',
    icon: `<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="32" cy="32" rx="28" ry="16" transform="rotate(-30 32 32)"/><line x1="32" y1="16" x2="32" y2="48"/><line x1="24" y1="20" x2="24" y2="44"/><line x1="40" y1="20" x2="40" y2="44"/></svg>`
  }
]
</script>

<style scoped>
.matchup-setup {
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

.setup-grid {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 32px;
  margin-bottom: 32px;
}

.team-inputs {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.team-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 20px;
  transition: all 0.2s;
}

.team-card:hover {
  border-color: var(--border-accent);
}

.team-card.home {
  border-left: 3px solid var(--accent-blue);
}

.team-card.away {
  border-left: 3px solid var(--accent-orange);
}

.team-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.team-card.home .team-badge {
  color: var(--accent-blue);
}

.team-card.away .team-badge {
  color: var(--accent-orange);
}

.input-wrapper {
  position: relative;
}

.search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-secondary);
  pointer-events: none;
}

.team-input {
  width: 100%;
  background: rgba(10, 22, 40, 0.6);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  padding: 14px 16px 14px 42px;
  color: var(--text-primary);
  font: inherit;
  font-size: 16px;
  font-weight: 600;
  transition: border-color 0.2s;
}

.team-input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.team-input::placeholder {
  color: var(--text-secondary);
  font-weight: 400;
}

.vs-divider {
  text-align: center;
  font-size: 18px;
  font-weight: 800;
  color: var(--text-secondary);
  padding: 4px 0;
}

.sport-selector {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 20px;
}

.section-label {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-secondary);
  margin: 0 0 16px;
}

.sport-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
}

.sport-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: rgba(10, 22, 40, 0.4);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  color: var(--text-secondary);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
}

.sport-option:hover {
  border-color: var(--border-accent);
  color: var(--text-primary);
}

.sport-option.active {
  background: rgba(0, 120, 255, 0.1);
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

.sport-icon {
  width: 32px;
  height: 32px;
  color: inherit;
}

.sport-icon svg {
  width: 100%;
  height: 100%;
}

.league-input {
  margin-top: 8px;
}

.field-label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.text-input {
  width: 100%;
  background: rgba(10, 22, 40, 0.6);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 10px 14px;
  color: var(--text-primary);
  font: inherit;
  font-size: 14px;
  transition: border-color 0.2s;
}

.text-input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.text-input::placeholder {
  color: var(--text-secondary);
}

.action-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.research-btn,
.simulate-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 28px;
  border-radius: 10px;
  font: inherit;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.research-btn {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  color: var(--text-primary);
}

.research-btn:hover:not(:disabled) {
  border-color: var(--accent-blue);
  background: var(--bg-card-hover);
}

.research-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.simulate-btn {
  background: var(--accent-orange);
  border: none;
  color: var(--text-primary);
}

.simulate-btn:hover:not(:disabled) {
  background: #e85a28;
  box-shadow: 0 6px 24px rgba(255, 107, 53, 0.3);
  transform: translateY(-2px);
}

.simulate-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.skeleton-section {
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

.skeleton-line.short {
  width: 60%;
}

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 16px;
}

.skeleton-card {
  height: 80px;
  background: linear-gradient(90deg, var(--bg-card-hover) 25%, rgba(255, 255, 255, 0.08) 50%, var(--bg-card-hover) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 10px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.research-results {
  background: var(--bg-card);
  border: 1px solid rgba(0, 230, 118, 0.2);
  border-radius: 16px;
  padding: 20px;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--success);
  margin-bottom: 16px;
}

.dossier-summary {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
}

.dossier-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 800;
  color: var(--accent-blue);
}

.stat-label {
  font-size: 11px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.matchup-summary {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
}

@media (max-width: 960px) {
  .setup-grid {
    grid-template-columns: 1fr;
  }

  .action-bar {
    flex-direction: column;
  }

  .research-btn,
  .simulate-btn {
    justify-content: center;
  }
}

@media (max-width: 640px) {
  .panel-title {
    font-size: 24px;
  }

  .dossier-summary {
    flex-wrap: wrap;
    gap: 16px;
  }
}
</style>
