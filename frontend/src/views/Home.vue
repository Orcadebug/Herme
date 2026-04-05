<template>
  <div class="home-shell">
    <header class="topbar">
      <div class="brand-block">
        <div class="brand">HERMES</div>
        <p class="tagline">A concise and versatile group intelligence engine that predicts everything.</p>
      </div>
      <div class="topbar-actions">
        <LanguageSwitcher />
        <a href="https://github.com/Orcadebug/Hermes" target="_blank" class="ghost-link">GitHub ↗</a>
      </div>
    </header>

    <main class="layout">
      <section class="hero-card">
        <div class="hero-copy">
          <span class="eyebrow">Multi-Agent Prediction Engine</span>
          <h1>Rehearse the future in a digital sandbox.</h1>
          <p>
            Upload seed materials and describe your prediction requirements in natural language. Hermes constructs a
            high-fidelity parallel digital world where thousands of intelligent agents with independent personalities
            freely interact and undergo social evolution.
          </p>
          <div class="workflow">
            <div class="workflow-item">01. Upload seed materials</div>
            <div class="workflow-item">02. Build knowledge graph</div>
            <div class="workflow-item">03. Generate agent personas</div>
            <div class="workflow-item">04. Run parallel simulation</div>
            <div class="workflow-item">05. Generate report and chat</div>
          </div>
        </div>
      </section>

      <section class="form-card">
        <div class="panel-header">
          <span>New Prediction</span>
          <span class="panel-meta">GraphRAG + Multi-Agent Simulation</span>
        </div>

        <div class="grid">
          <label class="field">
            <span>Prediction Topic</span>
            <input v-model="form.topic" placeholder="e.g. US Election 2028, AI regulation impact..." :disabled="loading" />
          </label>
          <label class="field">
            <span>Domain</span>
            <select v-model="form.domain" :disabled="loading">
              <option value="">Select a domain</option>
              <option value="politics">Politics</option>
              <option value="finance">Finance</option>
              <option value="technology">Technology</option>
              <option value="social">Social / Public Opinion</option>
              <option value="creative">Creative / Fiction</option>
            </select>
          </label>
        </div>

        <label class="field field-wide">
          <span>Seed Materials</span>
          <textarea
            v-model="form.seeds"
            rows="5"
            :disabled="loading"
            placeholder="Paste news articles, policy drafts, financial signals, or any real-world seed information here..."
          />
        </label>

        <label class="field field-wide">
          <span>Additional Context</span>
          <textarea
            v-model="form.context"
            rows="3"
            :disabled="loading"
            placeholder="Optional: specific variables to inject, scenarios to test, or questions to answer."
          />
        </label>

        <div class="footer-row">
          <p class="helper">Hermes uses multi-agent simulation to model collective emergence from individual interactions, producing detailed prediction reports you can interrogate.</p>
          <button class="primary-btn" @click="startPrediction" :disabled="!canSubmit || loading">
            <span>{{ loading ? 'Initializing...' : 'Start Prediction' }}</span>
            <span>→</span>
          </button>
        </div>

        <p v-if="error" class="error-text">{{ error }}</p>
      </section>

      <section class="history-card">
        <div class="panel-header">
          <span>Recent Predictions</span>
          <button class="refresh-link" @click="loadHistory" :disabled="historyLoading">Refresh</button>
        </div>
        <div v-if="historyLoading" class="history-empty">Loading recent predictions...</div>
        <div v-else-if="history.length === 0" class="history-empty">No predictions yet. Start your first simulation above.</div>
        <div v-else class="history-list">
          <button
            v-for="item in history"
            :key="item.id"
            class="history-item"
            @click="router.push({ name: 'Process', params: { predictionId: item.id } })"
          >
            <div class="history-main">
              <strong>{{ item.topic }}</strong>
              <span>{{ item.domain }} · {{ item.created_at }}</span>
            </div>
            <span class="status-chip">{{ item.status }}</span>
          </button>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'

const router = useRouter()

const form = ref({
  topic: '',
  domain: '',
  seeds: '',
  context: ''
})

const loading = ref(false)
const historyLoading = ref(false)
const error = ref('')
const history = ref([])

const canSubmit = computed(() => {
  return form.value.topic.trim() && form.value.seeds.trim()
})

const startPrediction = async () => {
  error.value = ''
  loading.value = true
  try {
    // Navigate to the process view with prediction params
    router.push({
      name: 'Process',
      query: {
        topic: form.value.topic,
        domain: form.value.domain,
        seeds: form.value.seeds,
        context: form.value.context
      }
    })
  } catch (err) {
    error.value = err.message || 'Unable to start prediction.'
  } finally {
    loading.value = false
  }
}

const loadHistory = async () => {
  historyLoading.value = true
  try {
    // TODO: Wire up actual API call
    history.value = []
  } catch (err) {
    history.value = []
  } finally {
    historyLoading.value = false
  }
}

onMounted(async () => {
  await loadHistory()
})
</script>

<style scoped>
.home-shell {
  min-height: 100vh;
  padding: 32px;
  background:
    radial-gradient(circle at top left, rgba(242, 197, 123, 0.35), transparent 34%),
    radial-gradient(circle at top right, rgba(102, 153, 204, 0.18), transparent 28%),
    #f7f2ea;
  color: #111;
}

.topbar {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-start;
  margin-bottom: 28px;
}

.brand {
  font-size: 30px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.tagline {
  max-width: 640px;
  margin-top: 8px;
  color: #574d41;
}

.topbar-actions {
  display: flex;
  gap: 16px;
  align-items: center;
}

.ghost-link,
.refresh-link {
  color: #111;
  text-decoration: none;
  background: none;
  border: none;
  cursor: pointer;
  font: inherit;
}

.layout {
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  gap: 24px;
}

.hero-card,
.form-card,
.history-card {
  border: 1px solid rgba(17, 17, 17, 0.12);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 24px 80px rgba(17, 17, 17, 0.08);
}

.hero-card {
  padding: 32px;
  min-height: 320px;
}

.eyebrow {
  display: inline-block;
  padding: 6px 10px;
  border-radius: 999px;
  background: #111;
  color: #f7f2ea;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.hero-copy h1 {
  margin: 18px 0 16px;
  font-size: clamp(38px, 6vw, 64px);
  line-height: 0.95;
}

.hero-copy p {
  max-width: 58ch;
  color: #52473a;
}

.workflow {
  display: grid;
  gap: 10px;
  margin-top: 26px;
}

.workflow-item {
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(17, 17, 17, 0.08);
  background: linear-gradient(135deg, rgba(242, 197, 123, 0.12), rgba(17, 17, 17, 0.02));
}

.form-card,
.history-card {
  padding: 24px;
}

.history-card {
  grid-column: 1 / -1;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 16px;
  margin-bottom: 20px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 12px;
}

.panel-meta {
  color: #7a6c5c;
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.field {
  display: grid;
  gap: 8px;
  font-size: 14px;
}

.field input,
.field textarea,
.field select {
  border: 1px solid rgba(17, 17, 17, 0.12);
  border-radius: 16px;
  padding: 14px 16px;
  background: #fffdfa;
  font: inherit;
}

.field-wide {
  margin-top: 16px;
}

.footer-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-top: 22px;
}

.helper {
  color: #6b5e50;
  max-width: 46ch;
}

.primary-btn {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  border: none;
  border-radius: 999px;
  background: #111;
  color: #fff;
  cursor: pointer;
  font: inherit;
}

.primary-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-text {
  margin-top: 14px;
  color: #a52e2e;
}

.history-list {
  display: grid;
  gap: 12px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(17, 17, 17, 0.08);
  background: #fffdfa;
  cursor: pointer;
  text-align: left;
}

.history-main {
  display: grid;
  gap: 4px;
}

.history-main span {
  color: #6b5e50;
}

.status-chip {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(17, 17, 17, 0.08);
  text-transform: uppercase;
  font-size: 12px;
}

.history-empty {
  color: #6b5e50;
}

@media (max-width: 960px) {
  .home-shell {
    padding: 18px;
  }

  .topbar,
  .footer-row {
    flex-direction: column;
    align-items: stretch;
  }

  .layout,
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
