<template>
  <div class="sports-shell">
    <header class="workspace-header">
      <div class="header-main">
        <button class="back-link" @click="router.push('/')">← Home</button>
        <div>
          <div class="workspace-title">{{ title }}</div>
          <div class="workspace-meta">{{ workspace?.sport || 'Sport' }} · {{ workspace?.league || 'League pending' }}</div>
        </div>
      </div>
      <div class="header-status">
        <span class="status-label">{{ workspace?.status || 'loading' }}</span>
        <span v-if="simulation" class="score-pill">{{ simulation.home_team }} {{ simulation.home_score }} - {{ simulation.away_score }} {{ simulation.away_team }}</span>
      </div>
    </header>

    <div class="stepper">
      <button
        v-for="step in steps"
        :key="step.id"
        class="step-btn"
        :class="{ active: currentStep === step.id }"
        @click="selectStep(step.id)"
      >
        <span>{{ step.id }}</span>
        <strong>{{ step.label }}</strong>
      </button>
    </div>

    <main class="workspace-layout">
      <aside class="sidebar-card">
        <div class="sidebar-section">
          <h3>Workspace</h3>
          <p v-if="workspace">{{ workspace.home_team_query }} vs {{ workspace.away_team_query }}</p>
          <p v-else>Loading workspace...</p>
        </div>

        <div class="sidebar-section">
          <h3>Dossier Inventory</h3>
          <p>{{ workspace?.dossier_index?.length || 0 }} files generated</p>
          <ul class="compact-list">
            <li v-for="item in (workspace?.dossier_index || []).slice(0, 8)" :key="item.path">{{ item.type }} · {{ item.name }}{{ item.profile_path ? ' · md + json' : '' }}</li>
          </ul>
        </div>

        <div class="sidebar-section">
          <h3>Agent Profiles</h3>
          <ul class="compact-list">
            <li v-for="item in participantPreview" :key="item.name">{{ item.name }} · {{ item.kind }} · {{ item.style }}</li>
          </ul>
        </div>

        <div class="sidebar-section">
          <h3>Sources</h3>
          <ul class="compact-list">
            <li v-for="link in workspace?.source_links || []" :key="link">
              <a :href="link" target="_blank">{{ link }}</a>
            </li>
          </ul>
        </div>

        <div class="sidebar-section">
          <h3>Matchup Summary</h3>
          <p>{{ workspace?.matchup_summary || 'Planner summary will appear here.' }}</p>
        </div>
      </aside>

      <section class="content-card">
        <p v-if="activeError" class="error-text">{{ activeError }}</p>

        <section v-if="currentStep === 1" class="panel">
          <div class="panel-head">
            <h2>Step 1 · Planner</h2>
            <span>{{ planStatusLabel }}</span>
          </div>
          <p class="panel-copy">
            Perplexity gathers cited external team data, then OpenRouter turns that research into the planning brief, dossiers, and validated rule pack used by the simulator.
          </p>
          <div class="progress-block">
            <div class="progress-track">
              <div class="progress-fill" :style="{ width: `${planProgress}%` }"></div>
            </div>
            <span>{{ planProgress }}%</span>
          </div>
          <p class="status-text">{{ plannerMessage }}</p>
          <div v-if="workspace?.dossier_index?.length" class="file-grid">
            <div v-for="item in workspace.dossier_index" :key="item.path" class="file-card">
              <strong>{{ item.name }}</strong>
              <span>{{ item.type }}</span>
            </div>
          </div>
          <button class="primary-btn" :disabled="workspace?.status !== 'ready' && workspace?.status !== 'simulated' && workspace?.status !== 'report_ready'" @click="currentStep = 2">
            Continue To Scenario Controls
          </button>
        </section>

        <section v-else-if="currentStep === 2" class="panel">
          <div class="panel-head">
            <h2>Step 2 · Scenario Controls</h2>
            <button class="ghost-btn" @click="resetScenario">Reset</button>
          </div>
          <div class="scenario-grid">
            <label class="field">
              <span>Venue</span>
              <select v-model="scenario.venue">
                <option value="home">Home advantage</option>
                <option value="away">Away advantage</option>
                <option value="neutral">Neutral site</option>
              </select>
            </label>
            <label class="field">
              <span>Weather</span>
              <input v-model="scenario.weather" placeholder="standard, rain, heat, indoor..." />
            </label>
            <label class="field">
              <span>Pace</span>
              <select v-model="scenario.pace">
                <option value="slow">Slow</option>
                <option value="balanced">Balanced</option>
                <option value="fast">Fast</option>
              </select>
            </label>
            <label class="field">
              <span>Fatigue</span>
              <select v-model="scenario.fatigue">
                <option value="fresh">Fresh</option>
                <option value="balanced">Balanced</option>
                <option value="fatigued">Fatigued</option>
              </select>
            </label>
            <label class="field">
              <span>Officiating</span>
              <select v-model="scenario.officiating">
                <option value="standard">Standard</option>
                <option value="tight">Tight whistle</option>
                <option value="lenient">Lenient</option>
              </select>
            </label>
            <label class="field">
              <span>Randomness</span>
              <input v-model.number="scenario.randomness" type="number" min="0.05" max="0.95" step="0.05" />
            </label>
          </div>
          <label class="field field-stack">
            <span>Injuries / Availability Notes</span>
            <textarea v-model="scenario.injuries" rows="4" placeholder="Who is limited, unavailable, or playing through something?" />
          </label>
          <label class="field field-stack">
            <span>Additional Notes</span>
            <textarea v-model="scenario.notes" rows="4" placeholder="Anything the planner should not know by default but the simulation should respect." />
          </label>
          <div class="button-row">
            <button class="ghost-btn" @click="currentStep = 1">Back</button>
            <button class="primary-btn" @click="saveScenarioAndAdvance" :disabled="savingScenario">{{ savingScenario ? 'Saving...' : 'Save Scenario And Continue' }}</button>
          </div>
        </section>

        <section v-else-if="currentStep === 3" class="panel">
          <div class="panel-head">
            <h2>Step 3 · Match Simulation</h2>
            <button class="primary-btn" @click="startSimulationFlow" :disabled="simulationRunning || simulationCompleted || !workspaceReady">
              {{ simulationRunning ? 'Simulation Running' : simulationCompleted ? 'Simulation Complete' : 'Start Simulation' }}
            </button>
          </div>
          <div v-if="simulation" class="scoreboard">
            <div class="team-score">
              <strong>{{ simulation.home_team }}</strong>
              <span>{{ simulation.home_score }}</span>
            </div>
            <div class="score-meta">
              <span>{{ simulation.current_segment || 'Match' }}</span>
              <span>Step {{ simulation.current_step }} / {{ simulation.target_steps }}</span>
            </div>
            <div class="team-score">
              <strong>{{ simulation.away_team }}</strong>
              <span>{{ simulation.away_score }}</span>
            </div>
          </div>
          <div
            v-if="['basketball_multi_agent', 'basketball_llm_multi_agent'].includes(simulation?.simulation_mode)"
            class="state-grid"
          >
            <div class="state-chip">
              <strong>Phase</strong>
              <span>{{ simulation.possession_phase || 'inbound' }}</span>
            </div>
            <div class="state-chip">
              <strong>Shot Clock</strong>
              <span>{{ simulation.shot_clock ?? '24' }}</span>
            </div>
            <div class="state-chip">
              <strong>Ball</strong>
              <span>{{ simulation.ball_handler || 'dead ball' }}</span>
            </div>
            <div class="state-chip">
              <strong>Set</strong>
              <span>{{ simulation.offense_set || 'flow' }}</span>
            </div>
            <div class="state-chip">
              <strong>Defense</strong>
              <span>{{ simulation.defensive_scheme || 'man' }}</span>
            </div>
            <div class="state-chip">
              <strong>Team Fouls</strong>
              <span>{{ simulation.home_team_fouls ?? 0 }} / {{ simulation.away_team_fouls ?? 0 }}</span>
            </div>
          </div>
          <div class="progress-block">
            <div class="progress-track">
              <div class="progress-fill dark" :style="{ width: `${simulationProgress}%` }"></div>
            </div>
            <span>{{ simulationProgress }}%</span>
          </div>
          <div class="event-list">
            <article v-for="event in events.slice().reverse()" :key="`${event.step}-${event.title}`" class="event-card">
              <div class="event-topline">
                <strong>{{ event.segment }}</strong>
                <span>{{ event.clock }}</span>
              </div>
              <div class="event-meta">
                <span>{{ event.phase || 'event' }}</span>
                <span>{{ event.action_type || 'play' }}</span>
                <span v-if="event.zone">{{ event.zone }}</span>
              </div>
              <h4>{{ event.title }}</h4>
              <p>{{ event.play_by_play }}</p>
              <small>{{ event.primary_actor }} · {{ event.coach }}</small>
              <small v-if="event.outcome">{{ event.outcome }}</small>
            </article>
          </div>
          <div class="button-row">
            <button class="ghost-btn" @click="currentStep = 2">Back</button>
            <button class="primary-btn" @click="currentStep = 4" :disabled="!simulationCompleted">Continue To Report</button>
          </div>
        </section>

        <section v-else-if="currentStep === 4" class="panel">
          <div class="panel-head">
            <h2>Step 4 · Report</h2>
            <button class="primary-btn" @click="launchReport" :disabled="reportRunning || !simulationCompleted">
              {{ reportRunning ? 'Generating Report...' : reportContent ? 'Regenerate Report' : 'Generate Report' }}
            </button>
          </div>
          <p class="status-text">{{ reportMessage }}</p>
          <pre v-if="reportContent" class="report-box">{{ reportContent }}</pre>
          <div class="button-row">
            <button class="ghost-btn" @click="currentStep = 3">Back</button>
            <button class="primary-btn" @click="currentStep = 5" :disabled="!reportContent">Continue To Chat</button>
          </div>
        </section>

        <section v-else class="panel">
          <div class="panel-head">
            <h2>Step 5 · Persona Chat</h2>
          </div>
          <div class="chat-controls">
            <label class="field">
              <span>Persona</span>
              <select v-model="selectedPersona">
                <option value="Match Analyst">Match Analyst</option>
                <option v-for="persona in personas" :key="persona" :value="persona">{{ persona }}</option>
              </select>
            </label>
          </div>
          <div class="chat-log">
            <div v-for="(entry, index) in chatLog" :key="index" class="chat-entry" :class="entry.role">
              <strong>{{ entry.role === 'assistant' ? selectedPersona : 'You' }}</strong>
              <p>{{ entry.content }}</p>
            </div>
          </div>
          <div class="chat-compose">
            <textarea v-model="chatMessage" rows="3" placeholder="Ask the coach, player, or analyst about the simulation." />
            <button class="primary-btn" @click="sendChat" :disabled="chatSending || !chatMessage.trim()">
              {{ chatSending ? 'Sending...' : 'Send' }}
            </button>
          </div>
        </section>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  chatWithSportsPersona,
  generateSportsReport,
  getSportsEvents,
  getSportsPlanStatus,
  getSportsReport,
  getSportsReportStatus,
  getSportsSimulationStatus,
  getSportsWorkspace,
  saveSportsScenario,
  startSportsSimulation
} from '../api/sports'

const route = useRoute()
const router = useRouter()

const createScenarioDefaults = () => ({
  venue: 'home',
  weather: 'standard',
  pace: 'balanced',
  randomness: 0.35,
  fatigue: 'balanced',
  officiating: 'standard',
  injuries: '',
  notes: '',
  seed: Math.floor(Math.random() * 1000000) + 1
})

const steps = [
  { id: 1, label: 'Planner' },
  { id: 2, label: 'Scenario' },
  { id: 3, label: 'Simulation' },
  { id: 4, label: 'Report' },
  { id: 5, label: 'Chat' }
]

const workspace = ref(null)
const currentStep = ref(1)
const plannerMessage = ref('Waiting for planner...')
const planProgress = ref(0)
const simulation = ref(null)
const events = ref([])
const reportContent = ref('')
const reportMessage = ref('Generate a postgame report once the simulation completes.')
const reportTaskId = ref(route.query.reportTask || '')
const scenario = ref(createScenarioDefaults())
const savingScenario = ref(false)
const chatLog = ref([])
const chatMessage = ref('')
const chatSending = ref(false)
const selectedPersona = ref('Match Analyst')
const uiError = ref('')

let plannerTimer = null
let simulationTimer = null
let reportTimer = null

const title = computed(() => {
  if (!workspace.value) return 'Loading workspace'
  return `${workspace.value.home_team_query} vs ${workspace.value.away_team_query}`
})

const planStatusLabel = computed(() => workspace.value?.status || 'planning')
const workspaceReady = computed(() => ['ready', 'simulated', 'report_ready'].includes(workspace.value?.status))
const simulationRunning = computed(() => simulation.value?.status === 'running')
const simulationCompleted = computed(() => simulation.value?.status === 'completed')
const activeError = computed(() => uiError.value || simulation.value?.error || workspace.value?.error || '')
const simulationProgress = computed(() => {
  if (!simulation.value?.target_steps) return 0
  return Math.round((simulation.value.current_step / simulation.value.target_steps) * 100)
})
const personas = computed(() => {
  if (!workspace.value?.participants) return []
  return workspace.value.participants.map(item => item.name).slice(0, 24)
})
const participantPreview = computed(() => {
  if (!workspace.value?.participants) return []
  return workspace.value.participants.slice(0, 8).map(item => ({
    name: item.name,
    kind: item.kind,
    style: item.profile?.archetype || item.profile?.pace_preference || item.role || 'profile pending'
  }))
})
const reportRunning = computed(() => Boolean(reportTaskId.value))

const clearTimers = () => {
  if (plannerTimer) window.clearInterval(plannerTimer)
  if (simulationTimer) window.clearInterval(simulationTimer)
  if (reportTimer) window.clearInterval(reportTimer)
  plannerTimer = null
  simulationTimer = null
  reportTimer = null
}

const loadWorkspace = async () => {
  try {
    const res = await getSportsWorkspace(route.params.workspaceId)
    workspace.value = res.data
    scenario.value = { ...createScenarioDefaults(), ...(workspace.value?.scenario || {}) }
    if (workspace.value?.latest_report_task_id && !workspace.value?.latest_report_id) {
      reportTaskId.value = workspace.value.latest_report_task_id
    }
    if (workspace.value?.latest_report_id) {
      reportTaskId.value = ''
    }
    if (workspace.value?.status === 'planning') {
      startPlannerPolling()
    }
    if (workspace.value?.latest_simulation_id) {
      await loadSimulationStatus()
    }
    if (workspace.value?.latest_report_id) {
      await loadReport()
    }
  } catch (err) {
    uiError.value = err.message || 'Unable to load workspace.'
  }
}

const startPlannerPolling = () => {
  if (plannerTimer) return
  plannerTimer = window.setInterval(async () => {
    try {
      const taskId = route.query.task || workspace.value?.planning_task_id
      const res = await getSportsPlanStatus(taskId ? { task_id: taskId } : { workspace_id: route.params.workspaceId })
      const data = res.data || {}
      plannerMessage.value = data.message || data.error || 'Planner running...'
      planProgress.value = data.progress || (workspace.value?.status === 'ready' ? 100 : planProgress.value)
      await loadWorkspace()
      if (workspace.value?.status !== 'planning') {
        window.clearInterval(plannerTimer)
        plannerTimer = null
        if (workspace.value?.status === 'ready') {
          planProgress.value = 100
        }
      }
    } catch (err) {
      plannerMessage.value = err.message || 'Planner polling failed.'
      uiError.value = plannerMessage.value
    }
  }, 1500)
}

const loadSimulationStatus = async () => {
  if (!workspace.value?.latest_simulation_id) return
  const res = await getSportsSimulationStatus({
    workspace_id: route.params.workspaceId,
    simulation_id: workspace.value.latest_simulation_id
  })
  simulation.value = res.data
  const eventRes = await getSportsEvents({
    workspace_id: route.params.workspaceId,
    simulation_id: workspace.value.latest_simulation_id
  })
  events.value = eventRes.data || []
}

const startSimulationPolling = () => {
  if (simulationTimer) return
  simulationTimer = window.setInterval(async () => {
    try {
      await loadSimulationStatus()
      await loadWorkspace()
      if (simulation.value?.status !== 'running') {
        window.clearInterval(simulationTimer)
        simulationTimer = null
      }
    } catch (err) {
      window.clearInterval(simulationTimer)
      simulationTimer = null
      uiError.value = err.message || 'Simulation polling failed.'
    }
  }, 1600)
}

const saveScenarioAndAdvance = async () => {
  uiError.value = ''
  savingScenario.value = true
  try {
    const res = await saveSportsScenario({
      workspace_id: route.params.workspaceId,
      scenario: scenario.value
    })
    workspace.value = res.data
    currentStep.value = 3
  } catch (err) {
    uiError.value = err.message || 'Unable to save scenario.'
  } finally {
    savingScenario.value = false
  }
}

const startSimulationFlow = async () => {
  uiError.value = ''
  try {
    const res = await startSportsSimulation({ workspace_id: route.params.workspaceId })
    simulation.value = res.data
    await loadWorkspace()
    startSimulationPolling()
  } catch (err) {
    uiError.value = err.message || 'Unable to start simulation.'
  }
}

const launchReport = async () => {
  uiError.value = ''
  reportMessage.value = 'Submitting report generation task...'
  try {
    const res = await generateSportsReport({ workspace_id: route.params.workspaceId })
    reportTaskId.value = res.data.task_id
    startReportPolling()
  } catch (err) {
    reportMessage.value = err.message || 'Unable to start report generation.'
    uiError.value = reportMessage.value
  }
}

const startReportPolling = () => {
  if (reportTimer || !reportTaskId.value) return
  reportTimer = window.setInterval(async () => {
    try {
      const res = await getSportsReportStatus({ task_id: reportTaskId.value })
      const data = res.data || {}
      reportMessage.value = data.message || 'Generating report...'
      if (data.status === 'completed') {
        window.clearInterval(reportTimer)
        reportTimer = null
        reportTaskId.value = ''
        await loadWorkspace()
        await loadReport()
      }
      if (data.status === 'failed') {
        window.clearInterval(reportTimer)
        reportTimer = null
        reportTaskId.value = ''
        reportMessage.value = data.error || 'Report generation failed.'
      }
    } catch (err) {
      window.clearInterval(reportTimer)
      reportTimer = null
      reportTaskId.value = ''
      reportMessage.value = err.message || 'Report polling failed.'
      uiError.value = reportMessage.value
    }
  }, 1500)
}

const loadReport = async () => {
  if (!workspace.value?.latest_report_id) return
  const res = await getSportsReport({
    workspace_id: route.params.workspaceId,
    report_id: workspace.value.latest_report_id
  })
  reportContent.value = res.data.content
  reportMessage.value = 'Report ready.'
}

const sendChat = async () => {
  if (!chatMessage.value.trim()) return
  uiError.value = ''
  const message = chatMessage.value.trim()
  chatLog.value.push({ role: 'user', content: message })
  chatMessage.value = ''
  chatSending.value = true
  try {
    const res = await chatWithSportsPersona({
      workspace_id: route.params.workspaceId,
      persona: selectedPersona.value,
      message,
      chat_history: chatLog.value
    })
    chatLog.value.push({ role: 'assistant', content: res.data.reply })
  } catch (err) {
    uiError.value = err.message || 'Unable to send chat message.'
    chatLog.value.push({ role: 'assistant', content: uiError.value })
  } finally {
    chatSending.value = false
  }
}

const resetScenario = () => {
  scenario.value = createScenarioDefaults()
}

const selectStep = (stepId) => {
  if (stepId === 2 && !workspaceReady.value) return
  if (stepId === 3 && !workspaceReady.value) return
  if (stepId === 4 && !simulationCompleted.value) return
  if (stepId === 5 && !reportContent.value) return
  currentStep.value = stepId
}

onMounted(async () => {
  await loadWorkspace()
  if (workspace.value?.status === 'planning') {
    startPlannerPolling()
  }
  if (simulation.value?.status === 'running') {
    startSimulationPolling()
  }
  if (reportTaskId.value) {
    startReportPolling()
  }
})

onUnmounted(clearTimers)
</script>

<style scoped>
.sports-shell {
  min-height: 100vh;
  padding: 24px;
  background:
    linear-gradient(180deg, rgba(245, 239, 230, 0.9), rgba(245, 239, 230, 0.98)),
    #efe8dc;
}

.workspace-header,
.stepper,
.workspace-layout {
  max-width: 1440px;
  margin: 0 auto;
}

.workspace-header {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: center;
  margin-bottom: 18px;
}

.header-main {
  display: flex;
  gap: 16px;
  align-items: center;
}

.back-link {
  border: none;
  background: #111;
  color: #fff;
  padding: 10px 14px;
  border-radius: 999px;
  cursor: pointer;
}

.workspace-title {
  font-size: 28px;
  font-weight: 800;
}

.workspace-meta {
  color: #6d6255;
}

.header-status {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.status-label,
.score-pill {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(17, 17, 17, 0.08);
  text-transform: uppercase;
  font-size: 12px;
}

.stepper {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.step-btn {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-start;
  padding: 16px;
  border: 1px solid rgba(17, 17, 17, 0.1);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  text-align: left;
}

.step-btn.active {
  background: #111;
  color: #fff;
}

.workspace-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 18px;
}

.sidebar-card,
.content-card {
  border: 1px solid rgba(17, 17, 17, 0.1);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 24px 80px rgba(17, 17, 17, 0.06);
}

.sidebar-card {
  padding: 22px;
  display: grid;
  gap: 18px;
  align-self: start;
}

.sidebar-section {
  display: grid;
  gap: 10px;
}

.sidebar-section h3 {
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.compact-list {
  margin: 0;
  padding-left: 18px;
  color: #5d5245;
}

.compact-list a {
  color: inherit;
}

.content-card {
  padding: 24px;
}

.panel {
  display: grid;
  gap: 18px;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.panel-copy,
.status-text {
  color: #665a4c;
}

.error-text {
  margin: 0 0 18px;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(167, 42, 42, 0.08);
  border: 1px solid rgba(167, 42, 42, 0.2);
  color: #7c1f1f;
}

.progress-block {
  display: flex;
  gap: 12px;
  align-items: center;
}

.progress-track {
  flex: 1;
  height: 10px;
  border-radius: 999px;
  background: rgba(17, 17, 17, 0.08);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #f4ba59, #e17445);
}

.progress-fill.dark {
  background: linear-gradient(90deg, #111, #3c556d);
}

.file-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.file-card,
.event-card {
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(17, 17, 17, 0.08);
  background: #fffdf8;
}

.file-card span {
  display: block;
  margin-top: 6px;
  color: #74685a;
}

.state-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.state-chip {
  display: grid;
  gap: 6px;
  padding: 14px;
  border-radius: 16px;
  background: rgba(17, 17, 17, 0.04);
}

.state-chip strong {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.event-meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  color: #6b5e4f;
  font-size: 12px;
  text-transform: uppercase;
}

.scenario-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.field {
  display: grid;
  gap: 8px;
}

.field input,
.field textarea,
.field select {
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(17, 17, 17, 0.12);
  background: #fffdf8;
  font: inherit;
}

.field-stack {
  margin-top: 4px;
}

.button-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.primary-btn,
.ghost-btn {
  border: none;
  padding: 12px 18px;
  border-radius: 999px;
  cursor: pointer;
  font: inherit;
}

.primary-btn {
  background: #111;
  color: #fff;
}

.primary-btn:disabled,
.ghost-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.ghost-btn {
  background: rgba(17, 17, 17, 0.08);
  color: #111;
}

.scoreboard {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 16px;
  padding: 18px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(17, 17, 17, 0.96), rgba(44, 67, 87, 0.88));
  color: #fff;
}

.team-score {
  display: grid;
  gap: 6px;
}

.team-score span {
  font-size: 42px;
  font-weight: 800;
}

.score-meta {
  display: grid;
  gap: 6px;
  justify-items: center;
  font-size: 14px;
}

.event-list {
  display: grid;
  gap: 12px;
  max-height: 540px;
  overflow: auto;
}

.event-topline {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: #6a5d4f;
  margin-bottom: 8px;
}

.event-card h4 {
  margin: 0 0 8px;
}

.report-box {
  padding: 18px;
  border-radius: 18px;
  background: #111;
  color: #f4efe7;
  white-space: pre-wrap;
  max-height: 620px;
  overflow: auto;
}

.chat-controls,
.chat-compose {
  display: grid;
  gap: 12px;
}

.chat-log {
  display: grid;
  gap: 12px;
  max-height: 420px;
  overflow: auto;
}

.chat-entry {
  padding: 16px;
  border-radius: 18px;
  background: rgba(17, 17, 17, 0.06);
}

.chat-entry.assistant {
  background: #111;
  color: #fff;
}

.chat-entry p {
  margin: 8px 0 0;
}

@media (max-width: 1080px) {
  .workspace-layout {
    grid-template-columns: 1fr;
  }

  .stepper,
  .scenario-grid,
  .file-grid,
  .state-grid {
    grid-template-columns: 1fr;
  }

  .workspace-header,
  .panel-head,
  .button-row {
    flex-direction: column;
    align-items: stretch;
  }

  .scoreboard {
    grid-template-columns: 1fr;
    justify-items: center;
    text-align: center;
  }
}
</style>
