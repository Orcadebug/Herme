<template>
  <div class="court-visualization">
    <div class="court-header">
      <h3 class="court-title">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="12" x2="21" y2="12"/><circle cx="12" cy="12" r="3"/></svg>
        {{ courtLabel }}
      </h3>
      <div class="court-legend">
        <span class="legend-item"><span class="legend-dot made"></span> Made</span>
        <span class="legend-item"><span class="legend-dot missed"></span> Missed</span>
      </div>
    </div>

    <div class="court-container">
      <svg v-if="sport === 'basketball'" viewBox="0 0 500 470" class="court-svg">
        <!-- Full Court -->
        <rect x="10" y="10" width="480" height="450" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.3"/>
        <!-- Half court line -->
        <line x1="10" y1="235" x2="490" y2="235" stroke="#ffffff" stroke-width="2" opacity="0.3"/>
        <!-- Center circle -->
        <circle cx="250" cy="235" r="40" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.3"/>
        <!-- Top key -->
        <rect x="190" y="10" width="120" height="140" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.3"/>
        <!-- Top free throw circle -->
        <circle cx="250" cy="150" r="40" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.3"/>
        <!-- Top 3-point arc -->
        <path d="M 50 10 Q 50 100 130 140" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.2"/>
        <path d="M 450 10 Q 450 100 370 140" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.2"/>
        <!-- Backboard top -->
        <line x1="220" y1="40" x2="280" y2="40" stroke="#ffffff" stroke-width="3" opacity="0.5"/>
        <!-- Rim top -->
        <circle cx="250" cy="50" r="8" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.5"/>

        <!-- Bottom key -->
        <rect x="190" y="320" width="120" height="140" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.3"/>
        <!-- Bottom free throw circle -->
        <circle cx="250" cy="320" r="40" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.3"/>
        <!-- Bottom 3-point arc -->
        <path d="M 50 460 Q 50 370 130 330" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.2"/>
        <path d="M 450 460 Q 450 370 370 330" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.2"/>
        <!-- Backboard bottom -->
        <line x1="220" y1="430" x2="280" y2="430" stroke="#ffffff" stroke-width="3" opacity="0.5"/>
        <!-- Rim bottom -->
        <circle cx="250" cy="420" r="8" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.5"/>

        <!-- Shot locations -->
        <circle
          v-for="(shot, i) in shotLocations"
          :key="'shot-' + i"
          :cx="shot.x"
          :cy="shot.y"
          :r="shot.made ? 6 : 4"
          :fill="shot.made ? 'rgba(0, 230, 118, 0.6)' : 'rgba(255, 77, 77, 0.6)'"
          :stroke="shot.made ? '#00e676' : '#ff4d4d'"
          :stroke-width="1.5"
          class="shot-marker"
        >
          <title>{{ shot.tooltip }}</title>
        </circle>

        <!-- Animated ball for current play -->
        <circle
          v-if="ballPosition"
          :cx="ballPosition.x"
          :cy="ballPosition.y"
          r="8"
          fill="#ff6b35"
          class="animated-ball"
        />
      </svg>

      <svg v-else-if="sport === 'soccer'" viewBox="0 0 500 320" class="court-svg">
        <!-- Pitch -->
        <rect x="10" y="10" width="480" height="300" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.3"/>
        <!-- Half line -->
        <line x1="250" y1="10" x2="250" y2="310" stroke="#ffffff" stroke-width="2" opacity="0.3"/>
        <!-- Center circle -->
        <circle cx="250" cy="160" r="50" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.3"/>
        <!-- Center spot -->
        <circle cx="250" cy="160" r="3" fill="#ffffff" opacity="0.3"/>
        <!-- Left penalty area -->
        <rect x="10" y="80" width="100" height="160" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.3"/>
        <!-- Left goal area -->
        <rect x="10" y="120" width="40" height="80" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.3"/>
        <!-- Right penalty area -->
        <rect x="390" y="80" width="100" height="160" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.3"/>
        <!-- Right goal area -->
        <rect x="450" y="120" width="40" height="80" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.3"/>

        <!-- Event markers -->
        <circle
          v-for="(evt, i) in eventLocations"
          :key="'evt-' + i"
          :cx="evt.x"
          :cy="evt.y"
          :r="evt.significant ? 7 : 4"
          :fill="evt.type === 'goal' ? 'rgba(0, 230, 118, 0.6)' : evt.type === 'shot' ? 'rgba(255, 107, 53, 0.5)' : 'rgba(136, 153, 170, 0.4)'"
          :stroke="evt.type === 'goal' ? '#00e676' : evt.type === 'shot' ? '#ff6b35' : '#8899aa'"
          :stroke-width="1.5"
          class="shot-marker"
        >
          <title>{{ evt.tooltip }}</title>
        </circle>

        <!-- Animated ball -->
        <circle
          v-if="ballPosition"
          :cx="ballPosition.x"
          :cy="ballPosition.y"
          r="8"
          fill="#ff6b35"
          class="animated-ball"
        />
      </svg>

      <svg v-else viewBox="0 0 500 240" class="court-svg">
        <!-- Football field -->
        <rect x="10" y="10" width="480" height="220" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.3"/>
        <!-- Yard lines -->
        <line v-for="i in 9" :key="'yard-' + i" :x1="10 + i * 48" y1="10" :x2="10 + i * 48" y2="230" stroke="#ffffff" stroke-width="1" opacity="0.15"/>
        <!-- End zones -->
        <rect x="10" y="10" width="48" height="220" fill="rgba(0, 120, 255, 0.1)" stroke="none"/>
        <rect x="442" y="10" width="48" height="220" fill="rgba(255, 107, 53, 0.1)" stroke="none"/>
        <!-- Hash marks -->
        <line x1="10" y1="120" x2="490" y2="120" stroke="#ffffff" stroke-width="1" opacity="0.2"/>

        <!-- Play markers -->
        <circle
          v-for="(play, i) in eventLocations"
          :key="'play-' + i"
          :cx="play.x"
          :cy="play.y"
          :r="play.significant ? 7 : 4"
          :fill="play.type === 'touchdown' ? 'rgba(0, 230, 118, 0.6)' : play.type === 'pass' ? 'rgba(0, 120, 255, 0.5)' : 'rgba(136, 153, 170, 0.4)'"
          :stroke="play.type === 'touchdown' ? '#00e676' : play.type === 'pass' ? '#0078ff' : '#8899aa'"
          :stroke-width="1.5"
          class="shot-marker"
        >
          <title>{{ play.tooltip }}</title>
        </circle>

        <!-- Animated ball -->
        <circle
          v-if="ballPosition"
          :cx="ballPosition.x"
          :cy="ballPosition.y"
          r="8"
          fill="#ff6b35"
          class="animated-ball"
        />
      </svg>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  sport: { type: String, default: 'basketball' },
  events: { type: Array, default: () => [] },
  gameState: { type: Object, default: null }
})

const courtLabel = computed(() => {
  const labels = { basketball: 'Basketball Court', soccer: 'Soccer Pitch', football: 'Football Field' }
  return labels[props.sport] || 'Court'
})

const shotLocations = computed(() => {
  if (props.sport !== 'basketball') return []
  return props.events
    .filter(e => e.actionType === 'shot' || e.actionType?.includes('shot'))
    .map((e, i) => ({
      x: 50 + Math.random() * 400,
      y: 50 + Math.random() * 370,
      made: e.outcome?.toLowerCase().includes('made') || e.outcome?.toLowerCase().includes('score') || !e.outcome?.toLowerCase().includes('miss'),
      tooltip: `${e.actor || 'Player'} - ${e.description || e.title}`
    }))
})

const eventLocations = computed(() => {
  return props.events
    .filter(e => e.actionType && e.actionType !== 'substitution' && e.actionType !== 'timeout')
    .map((e, i) => ({
      x: 50 + Math.random() * 400,
      y: 30 + Math.random() * (props.sport === 'football' ? 180 : props.sport === 'soccer' ? 260 : 410),
      type: e.actionType,
      significant: e.actionType === 'goal' || e.actionType === 'touchdown' || e.actionType === 'shot',
      tooltip: `${e.actor || 'Player'} - ${e.description || e.title}`
    }))
})

const ballPosition = computed(() => {
  if (!props.gameState?.ball_position) return null
  return props.gameState.ball_position
})
</script>

<style scoped>
.court-visualization {
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
}

.court-header {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.court-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  margin: 0;
}

.court-title svg {
  color: var(--accent-blue);
}

.court-legend {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: var(--text-secondary);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-dot.made { background: var(--success); }
.legend-dot.missed { background: var(--danger); }

.court-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  min-height: 300px;
}

.court-svg {
  width: 100%;
  max-width: 500px;
  height: auto;
}

.shot-marker {
  transition: all 0.3s;
  cursor: pointer;
}

.shot-marker:hover {
  r: 10;
  stroke-width: 2.5;
}

.animated-ball {
  animation: ballPulse 1s ease-in-out infinite;
  filter: drop-shadow(0 0 8px rgba(255, 107, 53, 0.6));
}

@keyframes ballPulse {
  0%, 100% { r: 8; opacity: 1; }
  50% { r: 10; opacity: 0.8; }
}
</style>
