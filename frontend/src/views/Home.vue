<template>
  <div class="home-shell">
    <!-- Top Navigation Bar -->
    <nav class="top-nav">
      <div class="nav-brand">
        <svg class="brand-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20M2 12h20"/>
        </svg>
        <span class="brand-text">HERMES</span>
      </div>
      <p class="nav-tagline">Simulate Any Game. Every Player. Every Play.</p>
      <div class="nav-actions">
        <a href="https://github.com/Orcadebug/Hermes" target="_blank" class="nav-link">GitHub ↗</a>
        <LanguageSwitcher />
      </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <h1 class="hero-headline">
          Simulate Any Game.<br />
          <span class="accent-text">Every Player. Every Play.</span>
        </h1>
        <p class="hero-sub">
          Hermes uses AI agents to run full game simulations — every player, coach, and fan acting autonomously. Powered by live research data.
        </p>
        <div class="hero-stats">
          <div class="stat-card">
            <span class="stat-number" :class="{ 'counting': animating }">{{ sportsCount }}</span>
            <span class="stat-label">Sports</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-card">
            <span class="stat-number" :class="{ 'counting': animating }">{{ agentRolesCount }}+</span>
            <span class="stat-label">Agent Roles</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-card">
            <span class="stat-number" :class="{ 'counting': animating }">{{ accuracyCount }}%</span>
            <span class="stat-label">Play-by-Play Accuracy</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Sport Selector Grid -->
    <section class="sport-grid">
      <h2 class="section-title">Choose Your Sport</h2>
      <div class="sport-cards">
        <div
          v-for="sport in sports"
          :key="sport.id"
          class="sport-card"
          @click="selectSport(sport.id)"
        >
          <div class="sport-icon" v-html="sport.icon"></div>
          <h3 class="sport-name">{{ sport.name }}</h3>
          <p class="sport-desc">{{ sport.description }}</p>
          <button class="sport-btn" @click.stop="simulateSport(sport.id)">Simulate</button>
        </div>
      </div>
    </section>

    <!-- Quick Simulation Form -->
    <section class="sim-form">
      <h2 class="section-title">Quick Simulation</h2>
      <div class="form-grid">
        <div class="form-row">
          <label class="input-group">
            <span class="input-label">Home Team</span>
            <input
              v-model="form.homeTeam"
              placeholder="e.g. Lakers"
              class="text-input"
            />
          </label>
          <label class="input-group">
            <span class="input-label">Away Team</span>
            <input
              v-model="form.awayTeam"
              placeholder="e.g. Celtics"
              class="text-input"
            />
          </label>
        </div>
        <div class="form-row">
          <label class="input-group">
            <span class="input-label">Sport</span>
            <select v-model="form.sport" class="text-input">
              <option value="">Select a sport</option>
              <option value="basketball">Basketball</option>
              <option value="soccer">Soccer</option>
              <option value="football">American Football</option>
            </select>
          </label>
          <label class="input-group">
            <span class="input-label">League (Optional)</span>
            <input
              v-model="form.league"
              placeholder="e.g. NBA, Premier League"
              class="text-input"
            />
          </label>
        </div>
        <div class="form-actions">
          <button
            class="cta-btn"
            @click="startSimulation"
            :disabled="!canSimulate || loading"
          >
            {{ loading ? 'Starting...' : 'Simulate Now' }}
          </button>
        </div>
      </div>
      <p v-if="error" class="error-text">{{ error }}</p>
    </section>

    <!-- Recent Simulations -->
    <section class="recent-sims">
      <div class="section-header">
        <h2 class="section-title">Recent Simulations</h2>
        <button class="refresh-btn" @click="loadHistory" :disabled="historyLoading">
          {{ historyLoading ? 'Loading...' : 'Refresh' }}
        </button>
      </div>
      <div v-if="historyLoading" class="history-empty">Loading recent simulations...</div>
      <div v-else-if="history.length === 0" class="history-empty">No simulations yet. Start your first game above.</div>
      <div v-else class="sim-scroll">
        <button
          v-for="sim in history"
          :key="sim.id"
          class="sim-card"
          @click="router.push({ name: 'SportsProcess', params: { workspaceId: sim.id } })"
        >
          <span class="sim-badge">{{ sim.sport }}</span>
          <div class="sim-teams">
            <span class="team">{{ sim.homeTeam }}</span>
            <span class="score">{{ sim.homeScore }} - {{ sim.awayScore }}</span>
            <span class="team">{{ sim.awayTeam }}</span>
          </div>
          <span class="sim-date">{{ sim.date }}</span>
        </button>
      </div>
    </section>

    <!-- How It Works -->
    <section class="how-it-works">
      <h2 class="section-title">How It Works</h2>
      <div class="steps">
        <div class="step">
          <div class="step-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/>
              <path d="m21 21-4.35-4.35"/>
            </svg>
          </div>
          <h3>Research Teams</h3>
          <p>Gather live data on rosters, stats, and strategies.</p>
        </div>
        <div class="step-arrow">→</div>
        <div class="step">
          <div class="step-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
          </div>
          <h3>Build Agent Profiles</h3>
          <p>Every player, coach, and fan becomes an autonomous AI agent.</p>
        </div>
        <div class="step-arrow">→</div>
        <div class="step">
          <div class="step-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
          </div>
          <h3>Simulate Game</h3>
          <p>Watch the full game unfold play by play in real time.</p>
        </div>
        <div class="step-arrow">→</div>
        <div class="step">
          <div class="step-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
          </div>
          <h3>Watch & Analyze</h3>
          <p>Deep-dive into stats, replays, and agent decision logs.</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'

const router = useRouter()

// Animated stats
const sportsCount = ref(0)
const agentRolesCount = ref(0)
const accuracyCount = ref(0)
const animating = ref(false)

const form = ref({
  homeTeam: '',
  awayTeam: '',
  sport: '',
  league: ''
})

const loading = ref(false)
const historyLoading = ref(false)
const error = ref('')
const history = ref([])

const canSimulate = computed(() => {
  return form.value.homeTeam.trim() && form.value.awayTeam.trim() && form.value.sport
})

const sports = [
  {
    id: 'basketball',
    name: 'Basketball',
    description: 'Full-court action with player-by-player autonomy, shot selection, and defensive schemes.',
    icon: `<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="32" cy="32" r="28"/>
      <path d="M32 4v56M4 32h56M12 12c10 8 16 20 16 20s6-12 16-20M12 52c10-8 16-20 16-20s6 12 16 20"/>
    </svg>`
  },
  {
    id: 'soccer',
    name: 'Soccer',
    description: '11v11 tactical simulation with formations, pressing, and set-piece strategies.',
    icon: `<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="32" cy="32" r="28"/>
      <polygon points="32,12 42,22 38,34 26,34 22,22"/>
      <line x1="32" y1="12" x2="32" y2="4"/>
      <line x1="42" y1="22" x2="50" y2="18"/>
      <line x1="38" y1="34" x2="44" y2="42"/>
      <line x1="26" y1="34" x2="20" y2="42"/>
      <line x1="22" y1="22" x2="14" y2="18"/>
    </svg>`
  },
  {
    id: 'football',
    name: 'American Football',
    description: 'Down-by-down play calling with route trees, blocking schemes, and defensive reads.',
    icon: `<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2">
      <ellipse cx="32" cy="32" rx="28" ry="16" transform="rotate(-30 32 32)"/>
      <line x1="32" y1="16" x2="32" y2="48"/>
      <line x1="24" y1="20" x2="24" y2="44"/>
      <line x1="40" y1="20" x2="40" y2="44"/>
    </svg>`
  }
]

const selectSport = (sportId) => {
  form.value.sport = sportId
}

const simulateSport = (sportId) => {
  form.value.sport = sportId
  startSimulation()
}

const startSimulation = async () => {
  error.value = ''
  loading.value = true
  try {
    router.push({
      name: 'SportsProcess',
      query: {
        homeTeam: form.value.homeTeam,
        awayTeam: form.value.awayTeam,
        sport: form.value.sport,
        league: form.value.league
      }
    })
  } catch (err) {
    error.value = err.message || 'Unable to start simulation.'
  } finally {
    loading.value = false
  }
}

const loadHistory = async () => {
  historyLoading.value = true
  try {
    history.value = []
  } catch (err) {
    history.value = []
  } finally {
    historyLoading.value = false
  }
}

const animateStats = () => {
  animating.value = true
  const targets = { sports: 3, agents: 50, accuracy: 94 }
  const duration = 1500
  const steps = 60
  const interval = duration / steps

  let step = 0
  const timer = setInterval(() => {
    step++
    const progress = step / steps
    sportsCount.value = Math.round(targets.sports * progress)
    agentRolesCount.value = Math.round(targets.agents * progress)
    accuracyCount.value = Math.round(targets.accuracy * progress)
    if (step >= steps) {
      clearInterval(timer)
      animating.value = false
    }
  }, interval)
}

onMounted(async () => {
  await loadHistory()
  animateStats()
})
</script>

<style scoped>
.home-shell {
  --bg-primary: #0a1628;
  --bg-card: #132238;
  --bg-card-hover: #1a2d4a;
  --accent-blue: #0078ff;
  --accent-orange: #ff6b35;
  --text-primary: #ffffff;
  --text-secondary: #8899aa;
  --border-subtle: rgba(255, 255, 255, 0.08);
  --border-accent: rgba(0, 120, 255, 0.3);
  --glow-blue: rgba(0, 120, 255, 0.15);
  --glow-orange: rgba(255, 107, 53, 0.15);
}

.home-shell {
  min-height: 100vh;
  background: linear-gradient(180deg, #0a1628 0%, #0d1f3c 50%, #0a1628 100%);
  color: var(--text-primary);
  padding: 0;
  font-family: 'JetBrains Mono', 'Space Grotesk', 'Noto Sans SC', monospace;
}

/* Top Navigation */
.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 32px;
  background: rgba(10, 22, 40, 0.95);
  border-bottom: 1px solid var(--border-subtle);
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(12px);
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-icon {
  width: 28px;
  height: 28px;
  color: var(--accent-blue);
}

.brand-text {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.1em;
  background: linear-gradient(135deg, var(--accent-blue), #00c6ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-tagline {
  color: var(--text-secondary);
  font-size: 13px;
  letter-spacing: 0.02em;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.nav-link {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
}

.nav-link:hover {
  color: var(--text-primary);
}

/* Hero Section */
.hero {
  padding: 80px 32px 60px;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.hero::before {
  content: '';
  position: absolute;
  top: -50%;
  left: 50%;
  transform: translateX(-50%);
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, var(--glow-blue) 0%, transparent 70%);
  pointer-events: none;
  animation: pulse 4s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.5; transform: translateX(-50%) scale(1); }
  50% { opacity: 0.8; transform: translateX(-50%) scale(1.1); }
}

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 800px;
  margin: 0 auto;
}

.hero-headline {
  font-size: clamp(36px, 5vw, 56px);
  font-weight: 800;
  line-height: 1.1;
  margin-bottom: 20px;
  animation: fadeInUp 0.6s ease-out;
}

.accent-text {
  background: linear-gradient(135deg, var(--accent-orange), #ff9a5c);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-sub {
  font-size: 18px;
  color: var(--text-secondary);
  max-width: 600px;
  margin: 0 auto 40px;
  line-height: 1.6;
  animation: fadeInUp 0.6s ease-out 0.2s both;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.hero-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32px;
  animation: fadeInUp 0.6s ease-out 0.4s both;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-number {
  font-size: 42px;
  font-weight: 800;
  color: var(--accent-blue);
  line-height: 1;
}

.stat-number.counting {
  animation: countPulse 0.3s ease-in-out;
}

@keyframes countPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 6px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.stat-divider {
  width: 1px;
  height: 48px;
  background: var(--border-subtle);
}

/* Section Titles */
.section-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 24px;
  color: var(--text-primary);
}

/* Sport Grid */
.sport-grid {
  padding: 40px 32px;
  max-width: 1200px;
  margin: 0 auto;
}

.sport-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.sport-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 28px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.sport-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, var(--glow-blue), transparent);
  opacity: 0;
  transition: opacity 0.3s;
}

.sport-card:hover {
  border-color: var(--border-accent);
  transform: translateY(-4px);
  box-shadow: 0 8px 32px var(--glow-blue);
}

.sport-card:hover::before {
  opacity: 1;
}

.sport-icon {
  width: 56px;
  height: 56px;
  margin: 0 auto 16px;
  color: var(--accent-blue);
  position: relative;
  z-index: 1;
}

.sport-icon svg {
  width: 100%;
  height: 100%;
}

.sport-name {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 8px;
  position: relative;
  z-index: 1;
}

.sport-desc {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 20px;
  position: relative;
  z-index: 1;
}

.sport-btn {
  background: var(--accent-blue);
  color: var(--text-primary);
  border: none;
  border-radius: 8px;
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  z-index: 1;
}

.sport-btn:hover {
  background: #0066dd;
  box-shadow: 0 4px 16px var(--glow-blue);
}

/* Quick Simulation Form */
.sim-form {
  padding: 40px 32px;
  max-width: 800px;
  margin: 0 auto;
}

.form-grid {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 28px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-label {
  font-size: 13px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.text-input {
  background: rgba(10, 22, 40, 0.6);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 12px 16px;
  color: var(--text-primary);
  font: inherit;
  font-size: 15px;
  transition: border-color 0.2s;
}

.text-input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.text-input::placeholder {
  color: var(--text-secondary);
}

.text-input option {
  background: var(--bg-card);
  color: var(--text-primary);
}

.form-actions {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.cta-btn {
  background: var(--accent-orange);
  color: var(--text-primary);
  border: none;
  border-radius: 10px;
  padding: 14px 40px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.cta-btn:hover:not(:disabled) {
  background: #e85a28;
  box-shadow: 0 6px 24px var(--glow-orange);
  transform: translateY(-2px);
}

.cta-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-text {
  margin-top: 12px;
  color: #ff4d4d;
  font-size: 14px;
  text-align: center;
}

/* Recent Simulations */
.recent-sims {
  padding: 40px 32px;
  max-width: 1200px;
  margin: 0 auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.refresh-btn {
  background: none;
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  transition: all 0.2s;
}

.refresh-btn:hover {
  border-color: var(--accent-blue);
  color: var(--text-primary);
}

.sim-scroll {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 8px;
  scroll-snap-type: x mandatory;
}

.sim-scroll::-webkit-scrollbar {
  height: 6px;
}

.sim-scroll::-webkit-scrollbar-track {
  background: var(--bg-card);
  border-radius: 3px;
}

.sim-scroll::-webkit-scrollbar-thumb {
  background: var(--accent-blue);
  border-radius: 3px;
}

.sim-card {
  flex: 0 0 280px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
  scroll-snap-align: start;
}

.sim-card:hover {
  border-color: var(--border-accent);
  background: var(--bg-card-hover);
}

.sim-badge {
  display: inline-block;
  background: var(--glow-blue);
  color: var(--accent-blue);
  font-size: 11px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 10px;
}

.sim-teams {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.team {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.score {
  font-size: 16px;
  font-weight: 800;
  color: var(--accent-orange);
}

.sim-date {
  font-size: 12px;
  color: var(--text-secondary);
}

.history-empty {
  color: var(--text-secondary);
  font-size: 14px;
  padding: 24px;
  text-align: center;
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px dashed var(--border-subtle);
}

/* How It Works */
.how-it-works {
  padding: 60px 32px 80px;
  max-width: 1200px;
  margin: 0 auto;
}

.steps {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: 12px;
}

.step {
  flex: 1;
  max-width: 220px;
  text-align: center;
  padding: 24px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  transition: all 0.3s;
}

.step:hover {
  border-color: var(--border-accent);
  transform: translateY(-4px);
}

.step-icon {
  width: 40px;
  height: 40px;
  margin: 0 auto 14px;
  color: var(--accent-blue);
}

.step-icon svg {
  width: 100%;
  height: 100%;
}

.step h3 {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 8px;
}

.step p {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.step-arrow {
  color: var(--text-secondary);
  font-size: 20px;
  padding-top: 36px;
}

/* Responsive */
@media (max-width: 960px) {
  .top-nav {
    flex-direction: column;
    gap: 12px;
    padding: 16px 20px;
  }

  .nav-tagline {
    display: none;
  }

  .hero {
    padding: 48px 20px 40px;
  }

  .hero-stats {
    flex-direction: column;
    gap: 16px;
  }

  .stat-divider {
    width: 48px;
    height: 1px;
  }

  .sport-cards {
    grid-template-columns: 1fr;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .steps {
    flex-direction: column;
    align-items: center;
  }

  .step-arrow {
    transform: rotate(90deg);
    padding: 0;
  }

  .step {
    max-width: 100%;
  }
}

@media (max-width: 640px) {
  .hero-headline {
    font-size: 28px;
  }

  .hero-sub {
    font-size: 15px;
  }

  .stat-number {
    font-size: 32px;
  }

  .sport-grid,
  .sim-form,
  .recent-sims,
  .how-it-works {
    padding-left: 16px;
    padding-right: 16px;
  }
}
</style>
