<template>
  <div class="social-feed">
    <div class="feed-header">
      <h3 class="feed-title">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        Fan Reactions
      </h3>
      <div class="filter-tabs">
        <button
          v-for="opt in filterOptions"
          :key="opt.value"
          class="filter-tab"
          :class="{ active: activeFilter === opt.value }"
          @click="activeFilter = opt.value"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>

    <div class="feed-body">
      <div v-if="filteredReactions.length === 0" class="feed-empty">
        <p>Fan reactions will appear during the game.</p>
      </div>

      <div class="reactions-scroll">
        <div v-for="(reaction, i) in filteredReactions" :key="i" class="reaction-card">
          <div class="reaction-avatar">
            {{ reaction.avatar || reaction.handle?.charAt(0)?.toUpperCase() || 'F' }}
          </div>
          <div class="reaction-content">
            <div class="reaction-meta">
              <span class="reaction-handle">{{ reaction.handle || '@fan' }}</span>
              <span class="reaction-time">{{ reaction.time || 'now' }}</span>
            </div>
            <p class="reaction-text">{{ reaction.text || reaction.content || '' }}</p>
            <div class="reaction-actions">
              <span class="action-item">
                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                {{ reaction.likes || Math.floor(Math.random() * 500) }}
              </span>
              <span class="action-item">
                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                {{ reaction.retweets || Math.floor(Math.random() * 100) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  reactions: { type: Array, default: () => [] }
})

const activeFilter = ref('all')

const filterOptions = [
  { value: 'all', label: 'All' },
  { value: 'home', label: 'Home Fans' },
  { value: 'away', label: 'Away Fans' },
  { value: 'commentator', label: 'Commentators' }
]

const filteredReactions = computed(() => {
  if (activeFilter.value === 'all') return props.reactions
  return props.reactions.filter(r => r.type === activeFilter.value || r.fanType === activeFilter.value)
})
</script>

<style scoped>
.social-feed {
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
  margin-top: 16px;
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
  padding: 12px;
}

.feed-empty {
  text-align: center;
  padding: 20px;
  color: var(--text-secondary);
  font-size: 13px;
}

.reactions-scroll {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
  scroll-snap-type: x mandatory;
}

.reactions-scroll::-webkit-scrollbar {
  height: 4px;
}

.reactions-scroll::-webkit-scrollbar-thumb {
  background: var(--border-subtle);
  border-radius: 2px;
}

.reaction-card {
  flex: 0 0 280px;
  display: flex;
  gap: 10px;
  padding: 12px;
  background: rgba(10, 22, 40, 0.5);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  scroll-snap-align: start;
  transition: border-color 0.2s;
}

.reaction-card:hover {
  border-color: var(--border-accent);
}

.reaction-avatar {
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

.reaction-content {
  flex: 1;
  min-width: 0;
}

.reaction-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
}

.reaction-handle {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-primary);
}

.reaction-time {
  font-size: 11px;
  color: var(--text-secondary);
}

.reaction-text {
  margin: 0 0 6px;
  font-size: 13px;
  line-height: 1.4;
  color: var(--text-primary);
}

.reaction-actions {
  display: flex;
  gap: 12px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-secondary);
}
</style>
