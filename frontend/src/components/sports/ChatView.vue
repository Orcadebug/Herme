<template>
  <div class="chat-view">
    <div class="panel-header">
      <h1 class="panel-title">Persona Chat</h1>
      <p class="panel-subtitle">Talk to players, coaches, and commentators</p>
    </div>

    <div class="chat-layout">
      <div class="persona-sidebar">
        <h3 class="sidebar-title">Select Persona</h3>
        <div class="persona-search">
          <svg class="search-icon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input
            v-model="searchQuery"
            placeholder="Search personas..."
            class="search-input"
          />
        </div>
        <div class="persona-list">
          <div
            v-for="persona in filteredPersonas"
            :key="persona.name || persona"
            class="persona-item"
            :class="{ active: selectedPersona === (persona.name || persona) }"
            @click="selectPersona(persona)"
          >
            <div class="persona-avatar">
              {{ (persona.name || persona).charAt(0).toUpperCase() }}
            </div>
            <div class="persona-info">
              <span class="persona-name">{{ persona.name || persona }}</span>
              <span class="persona-role">{{ persona.role || persona.kind || 'Analyst' }}</span>
            </div>
          </div>
          <div v-if="filteredPersonas.length === 0" class="no-personas">
            No personas available.
          </div>
        </div>
      </div>

      <div class="chat-main">
        <div v-if="!selectedPersona" class="chat-empty">
          <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <p>Select a persona to start chatting</p>
        </div>

        <template v-else>
          <div class="chat-header">
            <div class="chat-persona-info">
              <div class="chat-avatar">
                {{ selectedPersona.charAt(0).toUpperCase() }}
              </div>
              <div>
                <h3 class="chat-name">{{ selectedPersona }}</h3>
                <p class="chat-role">{{ personaRole }}</p>
              </div>
            </div>
            <button class="clear-btn" @click="clearChat">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
              Clear
            </button>
          </div>

          <div ref="chatBodyRef" class="chat-body">
            <div v-for="(msg, i) in chatLog" :key="i" class="message" :class="msg.role">
              <div class="message-bubble">
                <p class="message-text">{{ msg.content }}</p>
              </div>
            </div>
            <div v-if="chatSending" class="message assistant">
              <div class="message-bubble typing">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
              </div>
            </div>
          </div>

          <div class="chat-input-area">
            <textarea
              v-model="chatMessage"
              @keydown.enter.exact.prevent="sendMessage"
              placeholder="Ask about the game, strategy, or anything else..."
              class="chat-textarea"
              rows="2"
            ></textarea>
            <button
              class="send-btn"
              :disabled="chatSending || !chatMessage.trim()"
              @click="sendMessage"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            </button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { chatWithSportsPersona } from '../../api/sports'

const props = defineProps({
  workspaceId: { type: String, default: '' },
  personas: { type: Array, default: () => [] },
  workspace: { type: Object, default: null }
})

const searchQuery = ref('')
const selectedPersona = ref('')
const chatLog = ref([])
const chatMessage = ref('')
const chatSending = ref(false)
const chatBodyRef = ref(null)

const personaRole = computed(() => {
  if (!props.workspace?.participants) return 'Analyst'
  const p = props.workspace.participants.find(p => p.name === selectedPersona.value)
  return p ? `${p.kind} · ${p.profile?.archetype || p.role || 'Analyst'}` : 'Analyst'
})

const filteredPersonas = computed(() => {
  const list = props.personas.map(name => {
    const p = props.workspace?.participants?.find(p => p.name === name)
    return { name, ...p }
  })
  if (!searchQuery.value) return list
  const q = searchQuery.value.toLowerCase()
  return list.filter(p => p.name.toLowerCase().includes(q))
})

function selectPersona(persona) {
  selectedPersona.value = persona.name || persona
  chatLog.value = []
}

function clearChat() {
  chatLog.value = []
}

async function sendMessage() {
  if (!chatMessage.value.trim() || chatSending.value) return
  const message = chatMessage.value.trim()
  chatLog.value.push({ role: 'user', content: message })
  chatMessage.value = ''
  chatSending.value = true

  try {
    const res = await chatWithSportsPersona({
      workspace_id: props.workspaceId,
      persona: selectedPersona.value,
      message,
      chat_history: chatLog.value
    })
    chatLog.value.push({ role: 'assistant', content: res.data.reply })
  } catch (err) {
    chatLog.value.push({ role: 'assistant', content: `Error: ${err.message || 'Failed to get response.'}` })
  } finally {
    chatSending.value = false
    await nextTick()
    if (chatBodyRef.value) {
      chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
    }
  }
}

watch(() => chatLog.value.length, async () => {
  await nextTick()
  if (chatBodyRef.value) {
    chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
  }
})
</script>

<style scoped>
.chat-view {
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
  margin-bottom: 24px;
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

.chat-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
  height: calc(100vh - 240px);
  min-height: 500px;
}

.persona-sidebar {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-title {
  padding: 14px 16px;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-subtle);
  margin: 0;
}

.persona-search {
  padding: 10px 12px;
  position: relative;
}

.search-icon {
  position: absolute;
  left: 22px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-secondary);
  pointer-events: none;
}

.search-input {
  width: 100%;
  background: rgba(10, 22, 40, 0.6);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 8px 12px 8px 34px;
  color: var(--text-primary);
  font: inherit;
  font-size: 13px;
  transition: border-color 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.search-input::placeholder {
  color: var(--text-secondary);
}

.persona-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.persona-list::-webkit-scrollbar {
  width: 4px;
}

.persona-list::-webkit-scrollbar-thumb {
  background: var(--border-subtle);
  border-radius: 2px;
}

.persona-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.persona-item:hover {
  background: rgba(255, 255, 255, 0.03);
}

.persona-item.active {
  background: rgba(0, 120, 255, 0.1);
}

.persona-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  height: 36px;
  background: linear-gradient(135deg, var(--accent-blue), #00c6ff);
  border-radius: 50%;
  font-size: 14px;
  font-weight: 700;
  color: white;
}

.persona-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.persona-name {
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.persona-role {
  font-size: 11px;
  color: var(--text-secondary);
}

.no-personas {
  padding: 20px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 13px;
}

.chat-main {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 16px;
  color: var(--text-secondary);
  font-size: 15px;
}

.chat-empty svg {
  opacity: 0.2;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-subtle);
}

.chat-persona-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--accent-orange), #ff9a5c);
  border-radius: 50%;
  font-size: 16px;
  font-weight: 700;
  color: white;
}

.chat-name {
  font-size: 15px;
  font-weight: 700;
  margin: 0;
}

.chat-role {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0;
}

.clear-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  transition: all 0.2s;
}

.clear-btn:hover {
  border-color: var(--danger);
  color: var(--danger);
}

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-body::-webkit-scrollbar {
  width: 4px;
}

.chat-body::-webkit-scrollbar-thumb {
  background: var(--border-subtle);
  border-radius: 2px;
}

.message {
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.5;
}

.message.user .message-bubble {
  background: var(--accent-blue);
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-bubble {
  background: var(--bg-card-hover);
  color: var(--text-primary);
  border-bottom-left-radius: 4px;
}

.message-text {
  margin: 0;
}

.message-bubble.typing {
  display: flex;
  gap: 4px;
  padding: 14px 20px;
}

.typing-dot {
  width: 6px;
  height: 6px;
  background: var(--text-secondary);
  border-radius: 50%;
  animation: typingBounce 1.4s ease-in-out infinite;
}

.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-6px); }
}

.chat-input-area {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid var(--border-subtle);
}

.chat-textarea {
  flex: 1;
  background: rgba(10, 22, 40, 0.6);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  padding: 10px 14px;
  color: var(--text-primary);
  font: inherit;
  font-size: 14px;
  resize: none;
  transition: border-color 0.2s;
}

.chat-textarea:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.chat-textarea::placeholder {
  color: var(--text-secondary);
}

.send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  background: var(--accent-blue);
  border: none;
  border-radius: 10px;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: #0066dd;
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

@media (max-width: 960px) {
  .chat-layout {
    grid-template-columns: 1fr;
    height: auto;
  }

  .persona-sidebar {
    max-height: 200px;
  }

  .chat-main {
    min-height: 400px;
  }
}
</style>
