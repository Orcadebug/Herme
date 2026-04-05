<template>
  <div class="live-game-view">
    <ScoreboardTicker
      :home-team="homeTeam"
      :away-team="awayTeam"
      :home-score="homeScore"
      :away-score="awayScore"
      :game-clock="gameClock"
      :period="currentPeriod"
      :possession="possession"
      :home-fouls="homeFouls"
      :away-fouls="awayFouls"
      :home-timeouts="homeTimeouts"
      :away-timeouts="awayTimeouts"
      :sport="sport"
      :is-running="isRunning"
      :is-complete="isComplete"
      :score-flash="scoreFlash"
      @start="$emit('start')"
    />

    <div class="live-grid">
      <div class="col-left">
        <PlayByPlayFeed
          :events="formattedEvents"
          :home-team="homeTeam"
          :away-team="awayTeam"
          :filter="teamFilter"
          @filter-change="teamFilter = $event"
        />
      </div>

      <div class="col-center">
        <CourtVisualization
          :sport="sport"
          :events="formattedEvents"
          :game-state="gameState"
        />
      </div>

      <div class="col-right">
        <PlayerStatCards
          :home-team="homeTeam"
          :away-team="awayTeam"
          :events="formattedEvents"
          :sport="sport"
          :active-team="statTeamFilter"
          @team-change="statTeamFilter = $event"
        />
      </div>
    </div>

    <SocialMediaFeed :reactions="reactions" />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import ScoreboardTicker from './ScoreboardTicker.vue'
import PlayByPlayFeed from './PlayByPlayFeed.vue'
import CourtVisualization from './CourtVisualization.vue'
import PlayerStatCards from './PlayerStatCards.vue'
import SocialMediaFeed from './SocialMediaFeed.vue'

const props = defineProps({
  workspaceId: { type: String, default: '' },
  homeTeam: { type: String, default: '' },
  awayTeam: { type: String, default: '' },
  sport: { type: String, default: 'basketball' },
  simulation: { type: Object, default: null },
  events: { type: Array, default: () => [] },
  gameState: { type: Object, default: null },
  reactions: { type: Array, default: () => [] },
  isRunning: { type: Boolean, default: false },
  isComplete: { type: Boolean, default: false }
})

defineEmits(['start'])

const teamFilter = ref('all')
const statTeamFilter = ref('home')
const scoreFlash = ref('')

const homeScore = computed(() => props.simulation?.home_score ?? 0)
const awayScore = computed(() => props.simulation?.away_score ?? 0)
const gameClock = computed(() => props.simulation?.clock ?? '12:00')
const currentPeriod = computed(() => props.simulation?.current_segment ?? '1st')
const possession = computed(() => props.simulation?.possession ?? null)
const homeFouls = computed(() => props.simulation?.home_team_fouls ?? 0)
const awayFouls = computed(() => props.simulation?.away_team_fouls ?? 0)
const homeTimeouts = computed(() => props.simulation?.home_timeouts_remaining ?? 7)
const awayTimeouts = computed(() => props.simulation?.away_timeouts_remaining ?? 7)

const formattedEvents = computed(() => {
  return (props.events || []).map(e => ({
    id: `${e.step}-${e.title}`,
    timestamp: e.clock || '',
    segment: e.segment || '',
    title: e.title || '',
    description: e.play_by_play || '',
    actionType: e.action_type || 'play',
    phase: e.phase || '',
    zone: e.zone || '',
    actor: e.primary_actor || '',
    outcome: e.outcome || '',
    team: detectTeam(e)
  }))
})

function detectTeam(event) {
  const title = (event.title || '').toLowerCase()
  const desc = (event.play_by_play || '').toLowerCase()
  const actor = (event.primary_actor || '').toLowerCase()
  const home = props.homeTeam.toLowerCase()
  const away = props.awayTeam.toLowerCase()
  if (title.includes(home) || desc.includes(home) || actor.includes(home)) return 'home'
  if (title.includes(away) || desc.includes(away) || actor.includes(away)) return 'away'
  return 'neutral'
}

watch([homeScore, awayScore], ([newHome, newAway], [oldHome, oldAway]) => {
  if (oldHome !== undefined && newHome !== oldHome) {
    scoreFlash.value = 'home'
    setTimeout(() => scoreFlash.value = '', 800)
  }
  if (oldAway !== undefined && newAway !== oldAway) {
    scoreFlash.value = 'away'
    setTimeout(() => scoreFlash.value = '', 800)
  }
})
</script>

<style scoped>
.live-game-view {
  --bg-primary: #0a1628;
  --bg-card: #132238;
  --bg-card-hover: #1a2d4a;
  --accent-blue: #0078ff;
  --accent-orange: #ff6b35;
  --text-primary: #ffffff;
  --text-secondary: #8899aa;
  --border-subtle: rgba(255, 255, 255, 0.08);
  --border-accent: rgba(0, 120, 255, 0.3);
  --success: #00e676;
  --danger: #ff4d4d;
}

.live-grid {
  display: grid;
  grid-template-columns: 30% 40% 30%;
  gap: 16px;
  margin-top: 16px;
  min-height: 500px;
}

.col-left,
.col-center,
.col-right {
  min-height: 500px;
}

@media (max-width: 1200px) {
  .live-grid {
    grid-template-columns: 1fr;
  }

  .col-left,
  .col-center,
  .col-right {
    min-height: auto;
  }
}
</style>
