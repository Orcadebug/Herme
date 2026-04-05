<template>
  <div class="play-by-play-feed">
    <div class="feed-header">
      <h3 class="feed-title">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        Play by Play
      </h3>
      <div class="filter-tabs">
        <button
          v-for="opt in filterOptions"
          :key="opt.value"
          class="filter-tab"
          :class="{ active: filter === opt.value }"
          @click="$emit('filter-change', opt.value)"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>

    <div ref="feedRef" class="feed-body">
      <div v-if="filteredEvents.length === 0" class="feed-empty">
        <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
        <p>No plays yet. Start the simulation to see live action.</p>
      </div>

      <div
        v-for="event in filteredEvents"
        :key="event.id"
        class="event-item"
        :class="[event.team, event.actionType]"
      >
        <div class="event-timestamp">{{ event.timestamp }}</div>
        <div class="event-icon" v-html="getEventIcon(event.actionType)"></div>
        <div class="event-content">
          <p class="event-desc">{{ event.description || event.title }}</p>
          <div class="event-meta">
            <span v-if="event.actor" class="event-actor">{{ event.actor }}</span>
            <span v-if="event.outcome" class="event-outcome">{{ event.outcome }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'

const props = defineProps({
  events: { type: Array, default: () => [] },
  homeTeam: { type: String, default: '' },
  awayTeam: { type: String, default: '' },
  filter: { type: String, default: 'all' }
})

defineEmits(['filter-change'])

const feedRef = ref(null)

const filterOptions = [
  { value: 'all', label: 'All' },
  { value: 'home', label: 'Home' },
  { value: 'away', label: 'Away' }
]

const filteredEvents = computed(() => {
  if (props.filter === 'all') return props.events
  return props.events.filter(e => e.team === props.filter)
})

function getEventIcon(actionType) {
  const icons = {
    shot: `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>`,
    turnover: `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>`,
    foul: `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
    rebound: `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>`,
    assist: `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
    steal: `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>`,
    block: `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>`,
    timeout: `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>`,
    substitution: `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>`
  }
  return icons[actionType] || `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>`
}

watch(() => props.events.length, async () => {
  await nextTick()
  if (feedRef.value) {
    feedRef.value.scrollTop = feedRef.value.scrollHeight
  }
})
</script>

<style scoped>
.play-by-play-feed {
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

.feed-header {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.feed-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  margin: 0;
}

.feed-title svg {
  color: var(--accent-blue);
}

.filter-tabs {
  display: flex;
  gap: 4px;
}

.filter-tab {
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

.filter-tab.active {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}

.feed-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.feed-body::-webkit-scrollbar {
  width: 4px;
}

.feed-body::-webkit-scrollbar-track {
  background: transparent;
}

.feed-body::-webkit-scrollbar-thumb {
  background: var(--border-subtle);
  border-radius: 2px;
}

.feed-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px 20px;
  color: var(--text-secondary);
  font-size: 13px;
  text-align: center;
}

.feed-empty svg {
  opacity: 0.3;
}

.event-item {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  transition: background 0.2s;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(-10px); }
  to { opacity: 1; transform: translateX(0); }
}

.event-item:hover {
  background: rgba(255, 255, 255, 0.03);
}

.event-item.home {
  border-left: 2px solid var(--accent-blue);
}

.event-item.away {
  border-left: 2px solid var(--accent-orange);
}

.event-item.shot {
  background: rgba(0, 230, 118, 0.05);
}

.event-item.turnover {
  background: rgba(255, 77, 77, 0.05);
}

.event-timestamp {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  min-width: 40px;
  padding-top: 2px;
}

.event-icon {
  display: flex;
  align-items: center;
  color: var(--text-secondary);
  padding-top: 2px;
}

.event-content {
  flex: 1;
  min-width: 0;
}

.event-desc {
  margin: 0 0 4px;
  font-size: 13px;
  line-height: 1.4;
  color: var(--text-primary);
}

.event-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
}

.event-actor {
  color: var(--accent-blue);
  font-weight: 600;
}

.event-outcome {
  color: var(--text-secondary);
}
</style>
