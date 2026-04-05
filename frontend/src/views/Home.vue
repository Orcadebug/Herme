<template>
  <div class="page">

    <!-- Nav -->
    <nav class="nav">
      <div class="nav-inner">
        <a href="/" class="wordmark">HERMES</a>
        <div class="nav-right">
          <span class="nav-tag">Sports Simulation Engine</span>
          <a href="https://github.com/Orcadebug/Hermes" target="_blank" rel="noopener" class="nav-link">
            GitHub
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 17L17 7M7 7h10v10"/></svg>
          </a>
          <LanguageSwitcher />
        </div>
      </div>
    </nav>

    <!-- Hero -->
    <section class="hero">
      <div class="container">
        <p class="eyebrow">AI-Powered · Play-by-Play</p>
        <h1 class="headline">
          Simulate Any Game.<br />
          <span class="headline-accent">Every Player. Every Play.</span>
        </h1>
        <p class="hero-desc">
          Hermes deploys autonomous AI agents for every player, coach, and fan — running full game simulations powered by live research data.
        </p>
        <div class="stats-row">
          <div class="stat">
            <span class="stat-num">{{ sportsCount }}</span>
            <span class="stat-label">Sports</span>
          </div>
          <div class="stat-sep"></div>
          <div class="stat">
            <span class="stat-num">{{ agentRolesCount }}+</span>
            <span class="stat-label">Agent Roles</span>
          </div>
          <div class="stat-sep"></div>
          <div class="stat">
            <span class="stat-num">{{ accuracyCount }}%</span>
            <span class="stat-label">Accuracy</span>
          </div>
        </div>
      </div>
    </section>

    <div class="divider"></div>

    <!-- Sport Selector -->
    <section class="section">
      <div class="container">
        <h2 class="section-title">Choose Your Sport</h2>
        <div class="sport-grid">
          <div
            v-for="sport in sports"
            :key="sport.id"
            class="sport-card"
            :class="{ 'sport-card--active': form.sport === sport.id }"
            @click="selectSport(sport.id)"
          >
            <div class="sport-icon" v-html="sport.icon"></div>
            <div class="sport-body">
              <h3 class="sport-name">{{ sport.name }}</h3>
              <p class="sport-desc">{{ sport.description }}</p>
            </div>
            <button class="btn-outline" @click.stop="simulateSport(sport.id)">Simulate</button>
          </div>
        </div>
      </div>
    </section>

    <div class="divider"></div>

    <!-- Quick Simulation Form -->
    <section class="section">
      <div class="container container--narrow">
        <h2 class="section-title">Quick Simulation</h2>
        <div class="form-card">
          <div class="form-row">
            <label class="field">
              <span class="field-label">Home Team</span>
              <input v-model="form.homeTeam" placeholder="e.g. Lakers" class="field-input" />
            </label>
            <label class="field">
              <span class="field-label">Away Team</span>
              <input v-model="form.awayTeam" placeholder="e.g. Celtics" class="field-input" />
            </label>
          </div>
          <div class="form-row">
            <label class="field">
              <span class="field-label">Sport</span>
              <select v-model="form.sport" class="field-input">
                <option value="">Select a sport</option>
                <option value="basketball">Basketball</option>
                <option value="soccer">Soccer</option>
                <option value="football">American Football</option>
              </select>
            </label>
            <label class="field">
              <span class="field-label">League <span class="field-optional">(optional)</span></span>
              <input v-model="form.league" placeholder="e.g. NBA, Premier League" class="field-input" />
            </label>
          </div>
          <div class="form-footer">
            <button
              class="btn-cta"
              @click="startSimulation"
              :disabled="!canSimulate || loading"
            >
              {{ loading ? 'Starting...' : 'Simulate Now' }}
            </button>
            <p v-if="error" class="error-msg">{{ error }}</p>
          </div>
        </div>
      </div>
    </section>

    <div class="divider"></div>

    <!-- Recent Simulations -->
    <section class="section">
      <div class="container">
        <div class="section-header">
          <h2 class="section-title">Recent Simulations</h2>
          <button class="btn-ghost" @click="loadHistory" :disabled="historyLoading">
            {{ historyLoading ? 'Loading…' : 'Refresh' }}
          </button>
        </div>
        <div v-if="historyLoading" class="empty-state">Loading…</div>
        <div v-else-if="history.length === 0" class="empty-state">
          No simulations yet. Start your first game above.
        </div>
        <div v-else class="sim-list">
          <button
            v-for="sim in history"
            :key="sim.id"
            class="sim-item"
            @click="router.push({ name: 'SportsProcess', params: { workspaceId: sim.id } })"
          >
            <span class="sim-sport">{{ sim.sport }}</span>
            <div class="sim-match">
              <span class="sim-team">{{ sim.homeTeam }}</span>
              <span class="sim-score">{{ sim.homeScore }} – {{ sim.awayScore }}</span>
              <span class="sim-team">{{ sim.awayTeam }}</span>
            </div>
            <span class="sim-date">{{ sim.date }}</span>
          </button>
        </div>
      </div>
    </section>

    <div class="divider"></div>

    <!-- How It Works -->
    <section class="section section--last">
      <div class="container">
        <h2 class="section-title">How It Works</h2>
        <div class="steps">
          <div class="step" v-for="(step, i) in steps" :key="i">
            <span class="step-num">0{{ i + 1 }}</span>
            <div class="step-icon" v-html="step.icon"></div>
            <h3 class="step-title">{{ step.title }}</h3>
            <p class="step-desc">{{ step.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
      <div class="container">
        <span class="footer-brand">HERMES</span>
        <span class="footer-copy">Simulate Any Game. Every Player. Every Play.</span>
        <a href="https://github.com/Orcadebug/Hermes" target="_blank" rel="noopener" class="footer-link">GitHub ↗</a>
      </div>
    </footer>

  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'

const router = useRouter()

const sportsCount = ref(0)
const agentRolesCount = ref(0)
const accuracyCount = ref(0)

const form = ref({ homeTeam: '', awayTeam: '', sport: '', league: '' })
const loading = ref(false)
const historyLoading = ref(false)
const error = ref('')
const history = ref([])

const canSimulate = computed(() =>
  form.value.homeTeam.trim() && form.value.awayTeam.trim() && form.value.sport
)

const sports = [
  {
    id: 'basketball',
    name: 'Basketball',
    description: 'Full-court action with player-by-player autonomy, shot selection, and defensive schemes.',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
      <circle cx="12" cy="12" r="10"/>
      <path d="M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20M2 12h20"/>
    </svg>`
  },
  {
    id: 'soccer',
    name: 'Soccer',
    description: '11v11 tactical simulation with formations, pressing, and set-piece strategies.',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
      <circle cx="12" cy="12" r="10"/>
      <path d="M12 2l3.09 9.26H22l-6.18 4.49L18 22l-6-4.36L6 22l2.18-6.25L2 11.26h6.91z"/>
    </svg>`
  },
  {
    id: 'football',
    name: 'American Football',
    description: 'Down-by-down play calling with route trees, blocking schemes, and defensive reads.',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
      <ellipse cx="12" cy="12" rx="10" ry="6" transform="rotate(-30 12 12)"/>
      <line x1="12" y1="6" x2="12" y2="18"/>
      <line x1="9" y1="7.5" x2="9" y2="16.5"/>
      <line x1="15" y1="7.5" x2="15" y2="16.5"/>
    </svg>`
  }
]

const steps = [
  {
    title: 'Research Teams',
    desc: 'Gather live data on rosters, stats, and strategies.',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>`
  },
  {
    title: 'Build Agent Profiles',
    desc: 'Every player, coach, and fan becomes an autonomous AI agent.',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>`
  },
  {
    title: 'Simulate Game',
    desc: 'Watch the full game unfold play by play in real time.',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>`
  },
  {
    title: 'Watch & Analyze',
    desc: 'Deep-dive into stats, replays, and agent decision logs.',
    icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`
  }
]

const selectSport = (id) => { form.value.sport = id }

const simulateSport = (id) => {
  form.value.sport = id
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
  } catch {
    history.value = []
  } finally {
    historyLoading.value = false
  }
}

const animateStats = () => {
  const targets = { sports: 3, agents: 50, accuracy: 94 }
  const steps = 60
  const interval = 1500 / steps
  let step = 0
  const timer = setInterval(() => {
    step++
    const p = step / steps
    sportsCount.value = Math.round(targets.sports * p)
    agentRolesCount.value = Math.round(targets.agents * p)
    accuracyCount.value = Math.round(targets.accuracy * p)
    if (step >= steps) clearInterval(timer)
  }, interval)
}

onMounted(async () => {
  await loadHistory()
  animateStats()
})
</script>

<style scoped>
/* ── Layout ── */
.page {
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-body);
}

.container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 32px;
}

.container--narrow {
  max-width: 720px;
}

.divider {
  height: 1px;
  background: var(--border);
}

.section {
  padding: 64px 0;
}

.section--last {
  padding-bottom: 80px;
}

.section-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 32px;
}

.section-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  margin-bottom: 32px;
}

.section-header .section-title {
  margin-bottom: 0;
}

/* ── Nav ── */
.nav {
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  background: var(--bg);
  z-index: 100;
}

.nav-inner {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 32px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.wordmark {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: var(--text);
  cursor: pointer;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.nav-tag {
  font-size: 13px;
  color: var(--muted);
  letter-spacing: 0.02em;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  font-weight: 500;
  color: var(--muted);
  transition: color var(--transition);
}

.nav-link:hover {
  color: var(--text);
}

/* ── Hero ── */
.hero {
  padding: 96px 0 80px;
}

.eyebrow {
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--gold);
  margin-bottom: 20px;
}

.headline {
  font-family: var(--font-display);
  font-size: clamp(48px, 7vw, 88px);
  font-weight: 800;
  line-height: 1.0;
  letter-spacing: 0.01em;
  text-transform: uppercase;
  margin-bottom: 24px;
}

.headline-accent {
  color: var(--muted);
}

.hero-desc {
  font-size: 18px;
  font-weight: 300;
  color: var(--muted);
  max-width: 560px;
  line-height: 1.7;
  margin-bottom: 48px;
}

.stats-row {
  display: flex;
  align-items: center;
  gap: 40px;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-num {
  font-family: var(--font-display);
  font-size: 40px;
  font-weight: 700;
  line-height: 1;
  color: var(--text);
}

.stat-label {
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--subtle);
}

.stat-sep {
  width: 1px;
  height: 40px;
  background: var(--border);
}

/* ── Sport Cards ── */
.sport-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.sport-card {
  background: var(--bg);
  padding: 32px 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  cursor: pointer;
  transition: background var(--transition);
}

.sport-card:hover,
.sport-card--active {
  background: var(--surface);
}

.sport-card--active .sport-name {
  color: var(--gold);
}

.sport-icon {
  width: 32px;
  height: 32px;
  color: var(--subtle);
}

.sport-icon svg {
  width: 100%;
  height: 100%;
}

.sport-body {
  flex: 1;
}

.sport-name {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin-bottom: 8px;
  transition: color var(--transition);
}

.sport-desc {
  font-size: 14px;
  color: var(--muted);
  line-height: 1.6;
}

/* ── Buttons ── */
.btn-outline {
  align-self: flex-start;
  background: none;
  border: 1px solid var(--border);
  color: var(--text);
  padding: 8px 20px;
  font-size: 13px;
  font-weight: 600;
  font-family: var(--font-display);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  border-radius: var(--radius);
  transition: border-color var(--transition), background var(--transition);
}

.btn-outline:hover {
  border-color: var(--text);
  background: var(--text);
  color: var(--bg);
  cursor: pointer;
}

.btn-cta {
  background: var(--gold);
  color: #000;
  border: none;
  padding: 14px 40px;
  font-size: 15px;
  font-weight: 700;
  font-family: var(--font-display);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border-radius: var(--radius);
  transition: background var(--transition), transform var(--transition);
}

.btn-cta:hover:not(:disabled) {
  background: var(--gold-hover);
  transform: translateY(-1px);
}

.btn-cta:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-ghost {
  background: none;
  border: 1px solid var(--border);
  color: var(--muted);
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 500;
  border-radius: var(--radius);
  transition: border-color var(--transition), color var(--transition);
}

.btn-ghost:hover:not(:disabled) {
  border-color: var(--subtle);
  color: var(--text);
}

/* ── Form ── */
.form-card {
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-label {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
}

.field-optional {
  font-weight: 400;
  text-transform: none;
  letter-spacing: 0;
  color: var(--subtle);
}

.field-input {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 10px 14px;
  font-size: 15px;
  color: var(--text);
  transition: border-color var(--transition);
  appearance: none;
  -webkit-appearance: none;
}

.field-input:focus {
  outline: none;
  border-color: var(--text);
}

.field-input::placeholder {
  color: var(--subtle);
}

.field-input option {
  color: var(--text);
  background: var(--bg);
}

.form-footer {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
  padding-top: 4px;
}

.error-msg {
  font-size: 13px;
  color: var(--danger);
}

/* ── Recent Sims ── */
.empty-state {
  font-size: 14px;
  color: var(--muted);
  padding: 32px;
  text-align: center;
  border: 1px dashed var(--border);
  border-radius: var(--radius-md);
}

.sim-list {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.sim-item {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px 24px;
  background: var(--bg);
  border: none;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  text-align: left;
  transition: background var(--transition);
  font-family: var(--font-body);
}

.sim-item:last-child {
  border-bottom: none;
}

.sim-item:hover {
  background: var(--surface);
}

.sim-sport {
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--subtle);
  min-width: 80px;
}

.sim-match {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.sim-team {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.sim-score {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--gold);
  letter-spacing: 0.04em;
}

.sim-date {
  font-size: 13px;
  color: var(--subtle);
}

/* ── How It Works ── */
.steps {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.step {
  background: var(--bg);
  padding: 32px 24px;
  transition: background var(--transition);
}

.step:hover {
  background: var(--surface);
}

.step-num {
  display: block;
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--gold);
  margin-bottom: 16px;
}

.step-icon {
  width: 28px;
  height: 28px;
  color: var(--subtle);
  margin-bottom: 16px;
}

.step-icon svg {
  width: 100%;
  height: 100%;
}

.step-title {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.step-desc {
  font-size: 13px;
  color: var(--muted);
  line-height: 1.6;
}

/* ── Footer ── */
.footer {
  border-top: 1px solid var(--border);
  padding: 24px 0;
}

.footer .container {
  display: flex;
  align-items: center;
  gap: 24px;
}

.footer-brand {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: var(--text);
}

.footer-copy {
  font-size: 13px;
  color: var(--subtle);
  flex: 1;
}

.footer-link {
  font-size: 13px;
  color: var(--muted);
  transition: color var(--transition);
}

.footer-link:hover {
  color: var(--text);
}

/* ── Responsive ── */
@media (max-width: 960px) {
  .nav-tag { display: none; }

  .sport-grid {
    grid-template-columns: 1fr;
  }

  .steps {
    grid-template-columns: repeat(2, 1fr);
  }

  .stats-row {
    gap: 24px;
  }
}

@media (max-width: 640px) {
  .container { padding: 0 20px; }
  .nav-inner { padding: 0 20px; }

  .hero { padding: 64px 0 48px; }
  .section { padding: 48px 0; }

  .headline { font-size: 42px; }

  .form-row { grid-template-columns: 1fr; }

  .steps { grid-template-columns: 1fr; }

  .stats-row {
    flex-wrap: wrap;
    gap: 20px;
  }

  .stat-sep { display: none; }

  .footer .container {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
