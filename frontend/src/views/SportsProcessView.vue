<template>
  <div class="sports-shell">
    <!-- Top Broadcast Bar -->
    <header class="broadcast-header">
      <div class="header-left">
        <button class="back-btn" @click="router.push('/')">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
          Home
        </button>
        <div class="brand">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20M2 12h20"/></svg>
          <span class="brand-name">HERMES</span>
          <span class="brand-divider">|</span>
          <span class="matchup-label">{{ matchupLabel }}</span>
          <span class="live-badge" v-if="isLive">
            <span class="live-dot"></span> LIVE
          </span>
        </div>
      </div>
      <div class="header-right">
        <span v-if="workspace?.sport" class="sport-pill">{{ workspace.sport }}</span>
        <span v-if="workspace?.league" class="league-pill">{{ workspace.league }}</span>
      </div>
    </header>

    <!-- Step Tabs -->
    <nav class="step-nav">
      <button
        v-for="step in steps"
        :key="step.id"
        class="step-tab"
        :class="{ active: currentStep === step.id, disabled: !canAccessStep(step.id), done: stepDone(step.id) }"
        @click="selectStep(step.id)"
      >
        <span class="step-num">{{ stepDone(step.id) ? '✓' : step.id }}</span>
        <span class="step-label">{{ step.label }}</span>
      </button>
    </nav>

    <!-- Error Banner -->
    <div v-if="activeError" class="error-banner">
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      {{ activeError }}
      <button class="dismiss" @click="uiError = ''">✕</button>
    </div>

    <main class="main-content">
      <Transition name="fade" mode="out-in">

        <!-- ===================== STEP 1: MATCHUP SETUP ===================== -->
        <section v-if="currentStep === 1" key="setup" class="panel">
          <div class="panel-head">
            <h2>Matchup Setup</h2>
            <p class="sub">Select teams, sport, and research before simulating</p>
          </div>

          <div class="setup-grid">
            <!-- Sport Selector -->
            <div class="field-block">
              <label class="fld-label">Sport</label>
              <div class="sport-options">
                <button v-for="s in sportOptions" :key="s.id" class="sport-opt" :class="{ sel: form.sport === s.id }" @click="form.sport = s.id">
                  <span class="sport-ico" v-html="s.icon"></span>
                  <span>{{ s.name }}</span>
                </button>
              </div>
            </div>

            <!-- Team Inputs -->
            <div class="teams-row">
              <div class="team-field">
                <label class="fld-label">Home Team</label>
                <div class="input-wrap">
                  <input v-model="form.homeTeam" class="txt" placeholder="e.g. Lakers" @input="suggest('home')" />
                  <div v-if="searchingHome" class="spin"></div>
                  <ul v-if="homeSug.length" class="sug-list">
                    <li v-for="t in homeSug" :key="t" @click="form.homeTeam = t; homeSug = []">{{ t }}</li>
                  </ul>
                </div>
              </div>
              <div class="vs">VS</div>
              <div class="team-field">
                <label class="fld-label">Away Team</label>
                <div class="input-wrap">
                  <input v-model="form.awayTeam" class="txt" placeholder="e.g. Celtics" @input="suggest('away')" />
                  <div v-if="searchingAway" class="spin"></div>
                  <ul v-if="awaySug.length" class="sug-list">
                    <li v-for="t in awaySug" :key="t" @click="form.awayTeam = t; awaySug = []">{{ t }}</li>
                  </ul>
                </div>
              </div>
            </div>

            <div class="field-block">
              <label class="fld-label">League <span class="opt">(optional)</span></label>
              <input v-model="form.league" class="txt" placeholder="e.g. NBA, Premier League, NFL" />
            </div>
          </div>

          <!-- Research Button -->
          <div class="research-bar">
            <button class="research-btn" :disabled="!canResearch || researching" @click="doResearch">
              <div v-if="researching" class="btn-spin"></div>
              <svg v-else viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
              {{ researching ? 'Researching…' : 'Research Teams' }}
            </button>
            <p class="hint">Uses Perplexity to gather live roster, stats, and strategy data</p>
          </div>

          <!-- Research Loading Skeletons -->
          <div v-if="researching" class="skel-wrap">
            <div class="skel"></div>
            <div class="skel short"></div>
            <div class="skel"></div>
            <p class="skel-text">Gathering cited external team data…</p>
          </div>

          <!-- Research Complete -->
          <div v-if="researchDone" class="done-card">
            <div class="done-check">✓</div>
            <h3>Research Complete</h3>
            <p>{{ workspace?.dossier_index?.length || 0 }} files · {{ workspace?.participants?.length || 0 }} agent profiles</p>
            <button class="go-btn" @click="goStep(2)">Start Simulation →</button>
          </div>
        </section>

        <!-- ===================== STEP 2: PRE-GAME ===================== -->
        <section v-else-if="currentStep === 2" key="pregame" class="panel">
          <div class="panel-head">
            <h2>Pre-Game</h2>
            <p class="sub">Storylines, key matchups, and predicted lineups</p>
          </div>

          <div v-if="loadingPre" class="skel-wrap">
            <div class="skel"></div><div class="skel"></div><div class="skel short"></div>
          </div>

          <div v-else-if="pre" class="pre-content">
            <!-- Storylines -->
            <section class="sec">
              <h3 class="sec-title">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16v16H4z"/><path d="M4 9h16"/><path d="M4 14h10"/></svg>
                Key Storylines
              </h3>
              <div class="story-grid">
                <div v-for="(s, i) in pre.storylines || []" :key="i" class="story-card">
                  <span class="story-n">{{ i + 1 }}</span>
                  <p>{{ s }}</p>
                </div>
              </div>
            </section>

            <!-- Key Matchups -->
            <section class="sec">
              <h3 class="sec-title">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                Key Matchups
              </h3>
              <div class="mu-list">
                <div v-for="(m, i) in pre.key_matchups || []" :key="i" class="mu-row">
                  <span class="mu-p home">{{ m.home_player || 'TBD' }}</span>
                  <span class="mu-vs">vs</span>
                  <span class="mu-p away">{{ m.away_player || 'TBD' }}</span>
                </div>
              </div>
            </section>

            <!-- Lineups -->
            <section class="sec">
              <h3 class="sec-title">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                Predicted Lineups
              </h3>
              <div class="lu-grid">
                <div class="lu-col home">
                  <h4>{{ workspace?.home_team_query || 'Home' }}</h4>
                  <ul class="lu-list">
                    <li v-for="(p, i) in pre.home_lineup || []" :key="i">
                      <span class="lu-num">{{ p.number || '#' }}</span>
                      <span class="lu-name">{{ p.name }}</span>
                      <span class="lu-pos">{{ p.position }}</span>
                    </li>
                  </ul>
                </div>
                <div class="lu-col away">
                  <h4>{{ workspace?.away_team_query || 'Away' }}</h4>
                  <ul class="lu-list">
                    <li v-for="(p, i) in pre.away_lineup || []" :key="i">
                      <span class="lu-num">{{ p.number || '#' }}</span>
                      <span class="lu-name">{{ p.name }}</span>
                      <span class="lu-pos">{{ p.position }}</span>
                    </li>
                  </ul>
                </div>
              </div>
            </section>

            <!-- What to Watch For -->
            <section v-if="pre.what_to_watch?.length" class="sec">
              <h3 class="sec-title">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                What to Watch For
              </h3>
              <ul class="watch-list">
                <li v-for="(w, i) in pre.what_to_watch" :key="i">{{ w }}</li>
              </ul>
            </section>
          </div>

          <div class="panel-foot">
            <button class="ghost" @click="goStep(1)">← Back</button>
            <button class="primary" @click="beginSim" :disabled="simStarting">{{ simStarting ? 'Starting…' : 'Begin Simulation' }}</button>
          </div>
        </section>

        <!-- ===================== STEP 3: LIVE GAME ===================== -->
        <section v-else-if="currentStep === 3" key="live" class="panel live-panel">

          <!-- Scoreboard Ticker -->
          <div class="scoreboard" :class="{ flash: scoreFlash }">
            <div class="sb-team home">
              <span class="sb-name">{{ workspace?.home_team_query || 'HOME' }}</span>
              <span class="sb-score" :class="{ up: homeUp }">{{ homeScore }}</span>
              <span class="sb-rec">{{ workspace?.home_record || '' }}</span>
            </div>
            <div class="sb-center">
              <div class="sb-clock">{{ gameClock }}</div>
              <div class="sb-period">{{ gamePeriod }}</div>
              <div v-if="possession" class="poss" :class="possession">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </div>
            </div>
            <div class="sb-team away">
              <span class="sb-name">{{ workspace?.away_team_query || 'AWAY' }}</span>
              <span class="sb-score" :class="{ up: awayUp }">{{ awayScore }}</span>
              <span class="sb-rec">{{ workspace?.away_record || '' }}</span>
            </div>
          </div>

          <!-- State Chips (basketball) -->
          <div v-if="sim && isBBall" class="chips">
            <div class="chip"><b>Phase</b><span>{{ sim.possession_phase || '—' }}</span></div>
            <div class="chip"><b>Shot Clock</b><span>{{ sim.shot_clock ?? '—' }}</span></div>
            <div class="chip"><b>Ball</b><span>{{ sim.ball_handler || '—' }}</span></div>
            <div class="chip"><b>Set</b><span>{{ sim.offense_set || '—' }}</span></div>
            <div class="chip"><b>Defense</b><span>{{ sim.defensive_scheme || '—' }}</span></div>
            <div class="chip"><b>Fouls</b><span>{{ sim.home_team_fouls ?? 0 }} / {{ sim.away_team_fouls ?? 0 }}</span></div>
          </div>

          <!-- 3-Column Live Grid -->
          <div class="live-grid">

            <!-- Left: Play-by-Play -->
            <div class="col pbp-col">
              <div class="col-hd">
                <h3>Play by Play</h3>
                <div class="filters">
                  <button class="fbtn" :class="{ on: pbpF === 'all' }" @click="pbpF = 'all'">All</button>
                  <button class="fbtn" :class="{ on: pbpF === 'home' }" @click="pbpF = 'home'">{{ homeShort }}</button>
                  <button class="fbtn" :class="{ on: pbpF === 'away' }" @click="pbpF = 'away'">{{ awayShort }}</button>
                </div>
              </div>
              <div ref="pbpRef" class="pbp-feed">
                <div v-if="filteredPbp.length === 0" class="empty"><p>Waiting for plays…</p></div>
                <article v-for="(ev, i) in filteredPbp" :key="`e${i}`" class="pbp-ev" :class="ev.team_side">
                  <span class="pbp-time">{{ ev.clock || ev.segment }}</span>
                  <span class="pbp-emoji">{{ evEmoji(ev) }}</span>
                  <div class="pbp-body">
                    <p class="pbp-txt">{{ ev.play_by_play || ev.title }}</p>
                    <span class="pbp-actor">{{ ev.primary_actor }}</span>
                  </div>
                </article>
              </div>
            </div>

            <!-- Center: Court / Field -->
            <div class="col court-col">
              <div class="col-hd">
                <h3>Field View</h3>
                <span class="sport-tag">{{ workspace?.sport || form.sport }}</span>
              </div>
              <div class="court-wrap">
                <!-- Basketball Court -->
                <svg v-if="isBBall" viewBox="0 0 500 470" class="court-svg">
                  <rect x="10" y="10" width="480" height="450" fill="none" stroke="#1a2d4a" stroke-width="2" rx="4"/>
                  <line x1="10" y1="235" x2="490" y2="235" stroke="#1a2d4a" stroke-width="2"/>
                  <circle cx="250" cy="235" r="40" fill="none" stroke="#1a2d4a" stroke-width="2"/>
                  <rect x="190" y="10" width="120" height="120" fill="none" stroke="#1a2d4a" stroke-width="2"/>
                  <path d="M190 130 A60 60 0 0 0 310 130" fill="none" stroke="#1a2d4a" stroke-width="2"/>
                  <rect x="190" y="340" width="120" height="120" fill="none" stroke="#1a2d4a" stroke-width="2"/>
                  <path d="M190 340 A60 60 0 0 1 310 340" fill="none" stroke="#1a2d4a" stroke-width="2"/>
                  <path d="M50 10 A200 200 0 0 1 450 10" fill="none" stroke="#1a2d4a" stroke-width="2"/>
                  <path d="M50 460 A200 200 0 0 0 450 460" fill="none" stroke="#1a2d4a" stroke-width="2"/>
                  <circle v-for="(s, i) in shots" :key="'s'+i" :cx="s.x" :cy="s.y" r="6" :fill="s.made ? '#00c853' : '#ff1744'" opacity="0.8"><title>{{ s.d }}</title></circle>
                  <circle v-if="ball" :cx="ball.x" :cy="ball.y" r="8" fill="#ff6b35"><animate attributeName="r" values="6;10;6" dur="1s" repeatCount="indefinite"/></circle>
                </svg>

                <!-- Soccer Pitch -->
                <svg v-else-if="isSoccer" viewBox="0 0 500 340" class="court-svg">
                  <rect x="10" y="10" width="480" height="320" fill="none" stroke="#1a2d4a" stroke-width="2" rx="4"/>
                  <line x1="250" y1="10" x2="250" y2="330" stroke="#1a2d4a" stroke-width="2"/>
                  <circle cx="250" cy="170" r="50" fill="none" stroke="#1a2d4a" stroke-width="2"/>
                  <rect x="10" y="100" width="80" height="140" fill="none" stroke="#1a2d4a" stroke-width="2"/>
                  <rect x="410" y="100" width="80" height="140" fill="none" stroke="#1a2d4a" stroke-width="2"/>
                  <rect x="10" y="135" width="30" height="70" fill="none" stroke="#1a2d4a" stroke-width="2"/>
                  <rect x="460" y="135" width="30" height="70" fill="none" stroke="#1a2d4a" stroke-width="2"/>
                  <circle v-for="(e, i) in fieldEvts" :key="'fe'+i" :cx="e.x" :cy="e.y" r="5" :fill="e.t === 'home' ? '#0078ff' : '#ff6b35'" opacity="0.7"><title>{{ e.d }}</title></circle>
                  <circle v-if="ball" :cx="ball.x" :cy="ball.y" r="7" fill="#ff6b35"><animate attributeName="r" values="5;9;5" dur="1s" repeatCount="indefinite"/></circle>
                </svg>

                <!-- Football Field -->
                <svg v-else-if="isFootball" viewBox="0 0 600 240" class="court-svg">
                  <rect x="10" y="10" width="580" height="220" fill="none" stroke="#1a2d4a" stroke-width="2" rx="4"/>
                  <line v-for="n in 10" :key="'yl'+n" :x1="10+n*58" y1="10" :x2="10+n*58" y2="230" stroke="#1a2d4a" stroke-width="1"/>
                  <rect x="10" y="10" width="40" height="220" fill="none" stroke="#1a2d4a" stroke-width="2"/>
                  <rect x="550" y="10" width="40" height="220" fill="none" stroke="#1a2d4a" stroke-width="2"/>
                  <circle v-for="(e, i) in fieldEvts" :key="'fe'+i" :cx="e.x" :cy="e.y" r="5" :fill="e.t === 'home' ? '#0078ff' : '#ff6b35'" opacity="0.7"><title>{{ e.d }}</title></circle>
                  <circle v-if="ball" :cx="ball.x" :cy="ball.y" r="7" fill="#ff6b35"><animate attributeName="r" values="5;9;5" dur="1s" repeatCount="indefinite"/></circle>
                </svg>

                <!-- Generic fallback -->
                <div v-else class="generic-field">
                  <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="2" width="20" height="20" rx="2"/><line x1="12" y1="2" x2="12" y2="22"/><circle cx="12" cy="12" r="4"/></svg>
                  <p>Field visualization for {{ workspace?.sport || 'this sport' }}</p>
                </div>
              </div>
            </div>

            <!-- Right: Player Stats -->
            <div class="col stats-col">
              <div class="col-hd">
                <h3>Player Stats</h3>
                <div class="team-tog">
                  <button class="tbtn" :class="{ on: statT === 'home' }" @click="statT = 'home'">{{ homeShort }}</button>
                  <button class="tbtn" :class="{ on: statT === 'away' }" @click="statT = 'away'">{{ awayShort }}</button>
                </div>
              </div>
              <div class="stats-scroll">
                <div v-for="p in curStats" :key="p.name" class="stat-card" :class="{ hot: p.hot, cold: p.cold }">
                  <div class="sc-hd">
                    <span class="sc-num">{{ p.number || '#' }}</span>
                    <div class="sc-info"><span class="sc-name">{{ p.name }}</span><span class="sc-pos">{{ p.position }}</span></div>
                  </div>
                  <div class="sc-body">
                    <template v-if="isBBall">
                      <div class="sr"><span>PTS</span><b>{{ p.pts ?? 0 }}</b></div>
                      <div class="sr"><span>REB</span><b>{{ p.reb ?? 0 }}</b></div>
                      <div class="sr"><span>AST</span><b>{{ p.ast ?? 0 }}</b></div>
                      <div class="sr"><span>STL</span><b>{{ p.stl ?? 0 }}</b></div>
                      <div class="sr"><span>BLK</span><b>{{ p.blk ?? 0 }}</b></div>
                      <div class="sr"><span>FG%</span><b>{{ p.fgp ? (p.fgp*100).toFixed(0)+'%' : '—' }}</b></div>
                      <div class="sr"><span>MIN</span><b>{{ p.min ?? 0 }}</b></div>
                    </template>
                    <template v-else>
                      <div v-for="(v, k) in p.stats" :key="k" class="sr"><span>{{ k.toUpperCase() }}</span><b>{{ v }}</b></div>
                    </template>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Social Reaction Feed -->
          <div class="social-feed">
            <div class="sf-hd">
              <h3>
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                Live Reactions
              </h3>
              <div class="sf-filters">
                <button class="sff" :class="{ on: socF === 'all' }" @click="socF = 'all'">All</button>
                <button class="sff" :class="{ on: socF === 'home' }" @click="socF = 'home'">Home Fans</button>
                <button class="sff" :class="{ on: socF === 'away' }" @click="socF = 'away'">Away Fans</button>
                <button class="sff" :class="{ on: socF === 'commentator' }" @click="socF = 'commentator'">Commentators</button>
              </div>
            </div>
            <div class="sf-scroll">
              <div v-if="filteredSoc.length === 0" class="empty"><p>Waiting for reactions…</p></div>
              <div v-for="(r, i) in filteredSoc" :key="'r'+i" class="react-card">
                <div class="r-av">{{ r.avatar || '👤' }}</div>
                <div class="r-body">
                  <div class="r-top"><span class="r-handle">{{ r.handle || '@fan' }}</span><span class="r-type" :class="r.type">{{ r.type }}</span></div>
                  <p class="r-txt">{{ r.text }}</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- ===================== STEP 4: POST-GAME ===================== -->
        <section v-else-if="currentStep === 4" key="postgame" class="panel">
          <div class="panel-head">
            <h2>Post-Game Report</h2>
            <p class="sub">Full box score, grades, and press conference</p>
          </div>

          <div v-if="loadingPost" class="skel-wrap">
            <div class="skel"></div><div class="skel"></div><div class="skel short"></div>
          </div>

          <div v-else-if="post" class="post-content">
            <!-- Final Score -->
            <div class="final-score">
              <div class="fs-team">
                <span class="fs-name">{{ workspace?.home_team_query || 'Home' }}</span>
                <span class="fs-num" :class="{ win: post.winner === 'home' }">{{ post.home_score ?? homeScore }}</span>
              </div>
              <div class="fs-label">FINAL</div>
              <div class="fs-team">
                <span class="fs-name">{{ workspace?.away_team_query || 'Away' }}</span>
                <span class="fs-num" :class="{ win: post.winner === 'away' }">{{ post.away_score ?? awayScore }}</span>
              </div>
            </div>

            <!-- MVP -->
            <div v-if="post.mvp" class="mvp-card">
              <div class="mvp-badge">🏆 Game Ball</div>
              <h3>{{ post.mvp.name }}</h3>
              <p>{{ post.mvp.team }} · {{ post.mvp.stats }}</p>
            </div>

            <!-- Top Performers -->
            <section class="sec">
              <h3 class="sec-title">Top Performers</h3>
              <div class="perf-grid">
                <div v-for="(p, i) in post.top_performers || []" :key="i" class="perf-card">
                  <span class="perf-name">{{ p.name }}</span>
                  <span class="perf-team">{{ p.team }}</span>
                  <span class="perf-stats">{{ p.stats }}</span>
                </div>
              </div>
            </section>

            <!-- Box Score -->
            <section class="sec">
              <h3 class="sec-title">Box Score</h3>
              <div class="bs-wrap">
                <table class="bs-table">
                  <thead>
                    <tr><th>Player</th><th>POS</th><th>PTS</th><th>REB</th><th>AST</th><th>STL</th><th>BLK</th><th>FG%</th><th>MIN</th><th>Grade</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="(r, i) in post.box_score || []" :key="i" :class="r.team_side">
                      <td class="bs-player">{{ r.name }}</td>
                      <td>{{ r.position }}</td>
                      <td><b>{{ r.pts }}</b></td>
                      <td>{{ r.reb }}</td>
                      <td>{{ r.ast }}</td>
                      <td>{{ r.stl }}</td>
                      <td>{{ r.blk }}</td>
                      <td>{{ r.fg_pct }}</td>
                      <td>{{ r.min }}</td>
                      <td class="bs-grade" :class="gradeCls(r.grade)">{{ r.grade }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            <!-- Coach Quotes -->
            <section v-if="post.coach_quotes?.length" class="sec">
              <h3 class="sec-title">Press Conference</h3>
              <div class="quotes-grid">
                <blockquote v-for="(q, i) in post.coach_quotes" :key="i" class="quote-card">
                  <p>"{{ q.quote }}"</p>
                  <cite>— {{ q.speaker }}</cite>
                </blockquote>
              </div>
            </section>

            <!-- Media Reaction -->
            <section v-if="post.media_reaction?.length" class="sec">
              <h3 class="sec-title">Media Reaction</h3>
              <div class="media-list">
                <div v-for="(m, i) in post.media_reaction" :key="i" class="media-card">
                  <span class="m-src">{{ m.source }}</span>
                  <p>{{ m.text }}</p>
                </div>
              </div>
            </section>
          </div>

          <div class="panel-foot">
            <button class="ghost" @click="goStep(3)">← Back to Game</button>
            <button class="primary" @click="goStep(5)">Go to Chat →</button>
          </div>
        </section>

        <!-- ===================== STEP 5: CHAT ===================== -->
        <section v-else-if="currentStep === 5" key="chat" class="panel">
          <div class="panel-head">
            <h2>Persona Chat</h2>
            <p class="sub">Talk to players, coaches, and commentators</p>
          </div>

          <div class="chat-layout">
            <!-- Sidebar -->
            <div class="chat-side">
              <label class="fld-label">Select Persona</label>
              <select v-model="chatPersona" class="txt chat-sel">
                <option value="Match Analyst">Match Analyst</option>
                <option v-for="p in availPersonas" :key="p.name" :value="p.name">{{ p.name }} ({{ p.kind }})</option>
              </select>
              <div v-if="chatDossier" class="dossier">
                <h4>{{ chatDossier.name }}</h4>
                <span class="d-kind">{{ chatDossier.kind }}</span>
                <p v-if="chatDossier.archetype">{{ chatDossier.archetype }}</p>
                <p v-if="chatDossier.style">{{ chatDossier.style }}</p>
              </div>
            </div>

            <!-- Chat area -->
            <div class="chat-main">
              <div ref="chatRef" class="chat-msgs">
                <div v-if="chatLog.length === 0" class="chat-empty">
                  <p>Ask {{ chatPersona }} about the game, strategies, or player decisions.</p>
                </div>
                <div v-for="(e, i) in chatLog" :key="i" class="cmsg" :class="e.role">
                  <div class="cmsg-bub">
                    <span class="cmsg-from">{{ e.role === 'assistant' ? chatPersona : 'You' }}</span>
                    <p>{{ e.content }}</p>
                  </div>
                </div>
                <div v-if="chatSending" class="cmsg assistant">
                  <div class="cmsg-bub typing"><span class="tdots"></span></div>
                </div>
              </div>
              <div class="chat-input">
                <textarea v-model="chatMsg" class="chat-ta" placeholder="Type your message…" rows="3" @keydown.enter.exact.prevent="sendChat"></textarea>
                <button class="send-btn" @click="sendChat" :disabled="chatSending || !chatMsg.trim()">
                  <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
                </button>
              </div>
            </div>
          </div>
        </section>

      </Transition>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  chatWithSportsPersona,
  generateSportsPostgame,
  generateSportsPregame,
  getSportsEvents,
  getSportsPlanStatus,
  getSportsPostgame,
  getSportsPregame,
  getSportsReactions,
  getSportsReport,
  getSportsSimulationStatus,
  getSportsWorkspace,
  planSportsGame,
  startSportsSimulation
} from '../api/sports'

const route = useRoute()
const router = useRouter()
const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'

const steps = [
  { id: 1, label: 'Matchup' },
  { id: 2, label: 'Pre-Game' },
  { id: 3, label: 'Live Game' },
  { id: 4, label: 'Post-Game' },
  { id: 5, label: 'Chat' }
]

const sportOptions = [
  { id: 'basketball', name: 'Basketball', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2v20M2 12h20M6 6c4 3 6 6 6 6s2-3 6-6M6 18c4-3 6-6 6-6s2 3 6 6"/></svg>' },
  { id: 'soccer', name: 'Soccer', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="12,4 16,8 15,13 9,13 8,8"/></svg>' },
  { id: 'football', name: 'American Football', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="12" rx="10" ry="6" transform="rotate(-30 12 12)"/><line x1="12" y1="6" x2="12" y2="18"/></svg>' }
]

const teamDB = {
  basketball: ['Lakers','Celtics','Warriors','Bulls','Heat','Nets','76ers','Bucks','Nuggets','Suns','Mavericks','Knicks','Clippers','Thunder','Timberwolves','Cavaliers','Magic','Pacers','Hawks','Rockets'],
  soccer: ['Manchester United','Manchester City','Liverpool','Arsenal','Chelsea','Barcelona','Real Madrid','Bayern Munich','PSG','Juventus','AC Milan','Inter Milan','Dortmund','Atletico Madrid','Tottenham','Napoli'],
  football: ['Chiefs','Eagles','49ers','Cowboys','Bills','Ravens','Bengals','Lions','Dolphins','Browns','Packers','Vikings','Rams','Buccaneers','Chargers','Saints']
}

// Form
const form = ref({ homeTeam: route.query.homeTeam || '', awayTeam: route.query.awayTeam || '', sport: route.query.sport || '', league: route.query.league || '' })

// Workspace
const workspace = ref(null)
const currentStep = ref(1)
const uiError = ref('')

// Research
const researching = ref(false)
const researchDone = ref(false)
const searchingHome = ref(false)
const searchingAway = ref(false)
const homeSug = ref([])
const awaySug = ref([])

// Pre-game
const pre = ref(null)
const loadingPre = ref(false)

// Simulation
const sim = ref(null)
const events = ref([])
const simStarting = ref(false)

// Live state
const homeScore = ref(0)
const awayScore = ref(0)
const homeUp = ref(false)
const awayUp = ref(false)
const scoreFlash = ref(false)
const gameClock = ref('12:00')
const gamePeriod = ref('1st Quarter')
const possession = ref('')
const pbpF = ref('all')
const statT = ref('home')
const socF = ref('all')
const pbpRef = ref(null)
const shots = ref([])
const fieldEvts = ref([])
const ball = ref(null)
const playerStats = ref([])
const reactions = ref([])

// Post-game
const post = ref(null)
const loadingPost = ref(false)

// Chat
const chatLog = ref([])
const chatMsg = ref('')
const chatSending = ref(false)
const chatPersona = ref('Match Analyst')
const chatRef = ref(null)

// Timers
let plannerTimer = null
let liveTimer = null

const activeError = computed(() => uiError.value || sim.value?.error || workspace.value?.error || '')
const isLive = computed(() => sim.value?.status === 'running')
const isBBall = computed(() => workspace.value?.sport === 'basketball' || form.value.sport === 'basketball')
const isSoccer = computed(() => workspace.value?.sport === 'soccer' || form.value.sport === 'soccer')
const isFootball = computed(() => workspace.value?.sport === 'football' || form.value.sport === 'football')
const canResearch = computed(() => form.value.homeTeam.trim() && form.value.awayTeam.trim() && form.value.sport)
const matchupLabel = computed(() => {
  if (workspace.value) return `${workspace.value.home_team_query} vs ${workspace.value.away_team_query || workspace.value.away_query || ''}`
  if (form.value.homeTeam && form.value.awayTeam) return `${form.value.homeTeam} vs ${form.value.awayTeam}`
  return 'New Simulation'
})
const homeShort = computed(() => {
  const n = workspace.value?.home_team_query || form.value.homeTeam || 'HOME'
  return n.length > 10 ? n.slice(0, 8) + '…' : n
})
const awayShort = computed(() => {
  const n = workspace.value?.away_team_query || form.value.awayTeam || 'AWAY'
  return n.length > 10 ? n.slice(0, 8) + '…' : n
})

const availPersonas = computed(() => {
  if (!workspace.value?.participants) return []
  return workspace.value.participants.filter(p => p.name).slice(0, 30)
})

const chatDossier = computed(() => {
  const p = availPersonas.value.find(p => p.name === chatPersona.value)
  return p?.profile ? { name: p.name, kind: p.kind, ...p.profile } : null
})

const filteredPbp = computed(() => {
  const evts = events.value.slice().reverse()
  if (pbpF.value === 'all') return evts
  return evts.filter(e => e.team_side === pbpF.value)
})

const filteredSoc = computed(() => {
  if (socF.value === 'all') return reactions.value
  return reactions.value.filter(r => r.type === socF.value)
})

const curStats = computed(() => playerStats.value.filter(p => p.team_side === statT.value))

function stepDone(id) {
  if (id === 1) return researchDone.value || (workspace.value?.status && workspace.value.status !== 'planning')
  if (id === 2) return pre.value !== null
  if (id === 3) return sim.value?.status === 'completed'
  if (id === 4) return post.value !== null
  return false
}

function canAccessStep(id) {
  if (id === 1) return true
  if (id === 2) return ['ready','simulated','report_ready'].includes(workspace.value?.status) || researchDone.value
  if (id === 3) return ['ready','simulated','report_ready'].includes(workspace.value?.status)
  if (id === 4) return sim.value?.status === 'completed'
  if (id === 5) return true
  return false
}

function goStep(id) {
  if (!canAccessStep(id)) return
  currentStep.value = id
  if (id === 2) loadPre()
  if (id === 4) loadPost()
}

function selectStep(id) { goStep(id) }

// Team suggestions
function suggest(side) {
  const q = side === 'home' ? form.value.homeTeam : form.value.awayTeam
  if (q.length < 2) { if (side === 'home') homeSug.value = []; else awaySug.value = []; return }
  const list = teamDB[form.value.sport] || []
  const m = list.filter(t => t.toLowerCase().includes(q.toLowerCase())).slice(0, 5)
  if (side === 'home') { searchingHome.value = true; setTimeout(() => { homeSug.value = m; searchingHome.value = false }, 300) }
  else { searchingAway.value = true; setTimeout(() => { awaySug.value = m; searchingAway.value = false }, 300) }
}

// Research
async function doResearch() {
  uiError.value = ''
  researching.value = true
  try {
    const res = await planSportsGame({ home_team: form.value.homeTeam, away_team: form.value.awayTeam, sport: form.value.sport, league: form.value.league })
    const wid = res.data.workspace_id
    router.replace({ name: 'SportsProcess', params: { workspaceId: wid } })
    startPlanner(wid)
  } catch (err) { uiError.value = err.message || 'Research failed.' }
  finally { researching.value = false }
}

function startPlanner(wid) {
  if (plannerTimer) clearInterval(plannerTimer)
  plannerTimer = setInterval(async () => {
    try {
      const taskId = route.query.task
      const res = await getSportsPlanStatus(taskId ? { task_id: taskId } : { workspace_id: wid })
      const d = res.data || {}
      if (d.status === 'completed' || d.status === 'ready') { clearInterval(plannerTimer); plannerTimer = null; researchDone.value = true; await loadWs() }
    } catch { /* keep polling */ }
  }, 2000)
}

// Workspace
async function loadWs() {
  try {
    const res = await getSportsWorkspace(route.params.workspaceId)
    workspace.value = res.data
    if (res.data?.home_team_query && !form.value.homeTeam) form.value.homeTeam = res.data.home_team_query
    if (res.data?.away_team_query && !form.value.awayTeam) form.value.awayTeam = res.data.away_team_query
    if (res.data?.sport && !form.value.sport) form.value.sport = res.data.sport
    if (res.data?.league && !form.value.league) form.value.league = res.data.league
    if (['ready','simulated'].includes(res.data?.status)) researchDone.value = true
    if (res.data?.latest_simulation_id) await loadSimStatus()
  } catch (err) { uiError.value = err.message || 'Unable to load workspace.' }
}

// Pre-game
async function loadPre() {
  loadingPre.value = true
  try {
    const wid = route.params.workspaceId
    const res = await getSportsPregame(wid)
    pre.value = res.data || { storylines: ['Storylines will appear once research is complete.'], key_matchups: [], home_lineup: [], away_lineup: [], what_to_watch: [] }
  } catch {
    try {
      const wid = route.params.workspaceId
      await generateSportsPregame(wid)
      const res = await getSportsPregame(wid)
      pre.value = res.data || { storylines: ['Storylines will appear once research is complete.'], key_matchups: [], home_lineup: [], away_lineup: [], what_to_watch: [] }
    } catch {
      pre.value = { storylines: ['Storylines will appear once research is complete.'], key_matchups: [], home_lineup: [], away_lineup: [], what_to_watch: [] }
    }
  } finally { loadingPre.value = false }
}

// Simulation
async function beginSim() {
  uiError.value = ''
  simStarting.value = true
  try {
    await startSportsSimulation({ workspace_id: route.params.workspaceId })
    currentStep.value = 3
    startLivePoll()
  } catch (err) { uiError.value = err.message || 'Unable to start simulation.' }
  finally { simStarting.value = false }
}

function startLivePoll() {
  if (liveTimer) clearInterval(liveTimer)
  liveTimer = setInterval(async () => {
    try {
      await loadSimStatus()
      await loadEvts()
      await loadReactions()
      updatePlayerStats()
      updateCourt()
      if (sim.value?.status === 'completed') { clearInterval(liveTimer); liveTimer = null }
    } catch { /* keep polling */ }
  }, 1500)
}

async function loadSimStatus() {
  const wid = route.params.workspaceId
  if (!workspace.value?.latest_simulation_id) return
  const res = await getSportsSimulationStatus({ workspace_id: wid, simulation_id: workspace.value.latest_simulation_id })
  const pH = homeScore.value, pA = awayScore.value
  sim.value = res.data
  homeScore.value = res.data.home_score ?? homeScore.value
  awayScore.value = res.data.away_score ?? awayScore.value
  gameClock.value = res.data.clock || gameClock.value
  gamePeriod.value = res.data.period || gamePeriod.value
  possession.value = res.data.possession || ''
  if (homeScore.value !== pH) { homeUp.value = true; scoreFlash.value = true; setTimeout(() => { homeUp.value = false; scoreFlash.value = false }, 800) }
  if (awayScore.value !== pA) { awayUp.value = true; scoreFlash.value = true; setTimeout(() => { awayUp.value = false; scoreFlash.value = false }, 800) }
}

async function loadEvts() {
  const wid = route.params.workspaceId
  if (!workspace.value?.latest_simulation_id) return
  const res = await getSportsEvents({ workspace_id: wid, simulation_id: workspace.value.latest_simulation_id })
  events.value = res.data || []
  nextTick(() => { if (pbpRef.value) pbpRef.value.scrollTop = pbpRef.value.scrollHeight })
}

async function loadReactions() {
  try {
    const wid = route.params.workspaceId
    const res = await getSportsReactions(wid)
    reactions.value = res.data?.reactions || res.data || []
  } catch {
    if (events.value.length > reactions.value.length + 2) reactions.value.push(...mockReactions())
  }
}

function mockReactions() {
  const h = ['@hoopsfan23','@ballislife','@coachK_fan','@statgeek','@courtside_view','@nba_insider','@swishanalytics','@dunkcity99']
  const t = ['WHAT A PLAY! 🔥','That defense is elite','MVP performance right there','Called it!','Best game of the season','Coach needs a timeout','Historic performance','This sim is insane!','Clutch gene activated']
  const tp = ['home','away','commentator']
  const av = ['🏀','⛹️','📊','🎤','🔥','💪','👑','🎯']
  return Array.from({ length: 2 }, () => ({ handle: h[Math.floor(Math.random()*h.length)], text: t[Math.floor(Math.random()*t.length)], type: tp[Math.floor(Math.random()*tp.length)], avatar: av[Math.floor(Math.random()*av.length)] }))
}

function updatePlayerStats() {
  if (!events.value.length) return
  const m = {}
  events.value.forEach(ev => {
    const a = ev.primary_actor
    if (!a) return
    if (!m[a]) m[a] = { name: a, number: Math.floor(Math.random()*99)+1, position: ev.position || 'G', team_side: ev.team_side || 'home', pts: 0, reb: 0, ast: 0, stl: 0, blk: 0, fgm: 0, fga: 0, min: 0 }
    const s = m[a], act = (ev.action_type || '').toLowerCase()
    if (act.includes('score') || act.includes('made') || act.includes('dunk') || act.includes('layup') || act.includes('three')) { s.pts += act.includes('three') ? 3 : 2; s.fgm++; s.fga++ }
    else if (act.includes('miss')) s.fga++
    else if (act.includes('rebound')) s.reb++
    else if (act.includes('assist')) s.ast++
    else if (act.includes('steal')) s.stl++
    else if (act.includes('block')) s.blk++
    s.min = Math.floor(events.value.length / 10)
  })
  playerStats.value = Object.values(m).map(p => ({ ...p, fgp: p.fga > 0 ? p.fgm / p.fga : 0, hot: p.pts >= 15, cold: p.fga > 3 && p.fgm === 0 }))
}

function updateCourt() {
  const recent = events.value.slice(-20)
  shots.value = []; fieldEvts.value = []
  recent.forEach((ev, i) => {
    const act = (ev.action_type || '').toLowerCase()
    if (isBBall.value && (act.includes('shot') || act.includes('score') || act.includes('miss') || act.includes('dunk') || act.includes('layup'))) {
      const made = !act.includes('miss')
      const side = ev.team_side === 'home' ? 'top' : 'bottom'
      shots.value.push({ x: 100 + Math.random()*300, y: side === 'top' ? 20 + Math.random()*200 : 250 + Math.random()*200, made, d: ev.play_by_play || ev.title })
    }
    fieldEvts.value.push({ x: 50 + Math.random()*400, y: 30 + Math.random()*280, t: ev.team_side || 'home', d: ev.play_by_play || ev.title })
    if (i === recent.length - 1) ball.value = { x: 100 + Math.random()*300, y: 50 + Math.random()*370 }
  })
}

function evEmoji(ev) {
  const a = (ev.action_type || '').toLowerCase()
  if (a.includes('dunk')) return '🏀'; if (a.includes('three')) return '🎯'; if (a.includes('score') || a.includes('made')) return '✅'; if (a.includes('miss')) return '❌'; if (a.includes('turnover')) return '🔄'; if (a.includes('foul')) return '⚠️'; if (a.includes('rebound')) return '📦'; if (a.includes('assist')) return '🤝'; if (a.includes('steal')) return '🖐️'; if (a.includes('block')) return '🚫'; return '▶️'
}

// Post-game
async function loadPost() {
  loadingPost.value = true
  try {
    const wid = route.params.workspaceId
    const res = await getSportsPostgame(wid)
    post.value = res.data || { home_score: homeScore.value, away_score: awayScore.value, winner: homeScore.value >= awayScore.value ? 'home' : 'away', top_performers: [], box_score: [], coach_quotes: [], media_reaction: [] }
  } catch {
    try {
      const wid = route.params.workspaceId
      await generateSportsPostgame(wid)
      const res = await getSportsPostgame(wid)
      post.value = res.data || { home_score: homeScore.value, away_score: awayScore.value, winner: homeScore.value >= awayScore.value ? 'home' : 'away', top_performers: [], box_score: [], coach_quotes: [], media_reaction: [] }
    } catch {
      post.value = { home_score: homeScore.value, away_score: awayScore.value, winner: homeScore.value >= awayScore.value ? 'home' : 'away', top_performers: [], box_score: [], coach_quotes: [], media_reaction: [] }
    }
  } finally { loadingPost.value = false }
}

function gradeCls(g) {
  if (!g) return ''; if (g === 'A' || g === 'A+') return 'gA'; if (g === 'B' || g === 'B+') return 'gB'; if (g === 'C') return 'gC'; if (g === 'D') return 'gD'; if (g === 'F') return 'gF'; return ''
}

// Chat
async function sendChat() {
  if (!chatMsg.value.trim()) return
  const msg = chatMsg.value.trim()
  chatLog.value.push({ role: 'user', content: msg })
  chatMsg.value = ''
  chatSending.value = true
  try {
    const res = await chatWithSportsPersona({ workspace_id: route.params.workspaceId, persona: chatPersona.value, message: msg, chat_history: chatLog.value })
    chatLog.value.push({ role: 'assistant', content: res.data.reply })
  } catch (err) { chatLog.value.push({ role: 'assistant', content: err.message || 'Unable to get response.' }) }
  finally {
    chatSending.value = false
    nextTick(() => { if (chatRef.value) chatRef.value.scrollTop = chatRef.value.scrollHeight })
  }
}

function clearTimers() {
  if (plannerTimer) clearInterval(plannerTimer)
  if (liveTimer) clearInterval(liveTimer)
  plannerTimer = null; liveTimer = null
}

onMounted(async () => {
  await loadWs()
  if (workspace.value?.status === 'planning') startPlanner(route.params.workspaceId)
  if (workspace.value?.latest_simulation_id && sim.value?.status === 'running') startLivePoll()
})

onUnmounted(clearTimers)
</script>

<style scoped>
.sports-shell {
  --bg: #0a1628;
  --card: #132238;
  --card-h: #1a2d4a;
  --blue: #0078ff;
  --orange: #ff6b35;
  --tp: #ffffff;
  --ts: #8899aa;
  --bdr: rgba(255,255,255,0.08);
  --bdr-a: rgba(0,120,255,0.3);
  --glow-b: rgba(0,120,255,0.15);
  --glow-o: rgba(255,107,53,0.15);
  --green: #00c853;
  --red: #ff1744;
  min-height: 100vh;
  background: linear-gradient(180deg, #0a1628 0%, #0d1f3c 50%, #0a1628 100%);
  color: var(--tp);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Header */
.broadcast-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 24px; background: rgba(10,22,40,0.95); border-bottom: 1px solid var(--bdr);
  position: sticky; top: 0; z-index: 100; backdrop-filter: blur(12px);
}
.header-left { display: flex; align-items: center; gap: 20px; }
.back-btn {
  display: flex; align-items: center; gap: 6px; background: none; border: 1px solid var(--bdr);
  color: var(--ts); padding: 6px 12px; border-radius: 8px; cursor: pointer; font: inherit; font-size: 13px; transition: all 0.2s;
}
.back-btn:hover { border-color: var(--blue); color: var(--tp); }
.brand { display: flex; align-items: center; gap: 8px; }
.brand svg { color: var(--blue); }
.brand-name {
  font-size: 18px; font-weight: 800; letter-spacing: 0.1em;
  background: linear-gradient(135deg, var(--blue), #00c6ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.brand-divider { color: var(--bdr); }
.matchup-label { font-size: 14px; font-weight: 600; }
.live-badge {
  display: flex; align-items: center; gap: 6px; background: rgba(255,77,77,0.15); color: var(--red);
  padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; letter-spacing: 0.1em;
}
.live-dot { width: 6px; height: 6px; background: var(--red); border-radius: 50%; animation: lp 1.5s ease-in-out infinite; }
@keyframes lp { 0%,100%{opacity:1} 50%{opacity:0.3} }
.header-right { display: flex; gap: 8px; }
.sport-pill, .league-pill {
  padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
}
.sport-pill { background: var(--glow-b); color: var(--blue); }
.league-pill { background: var(--glow-o); color: var(--orange); }

/* Step Nav */
.step-nav {
  display: grid; grid-template-columns: repeat(5, 1fr); gap: 2px; padding: 0 24px;
  background: var(--card); border-bottom: 1px solid var(--bdr);
}
.step-tab {
  display: flex; align-items: center; gap: 10px; padding: 14px 16px; background: none; border: none;
  border-bottom: 2px solid transparent; color: var(--ts); cursor: pointer; font: inherit; font-size: 13px; transition: all 0.2s;
}
.step-tab:hover:not(.disabled) { color: var(--tp); background: rgba(255,255,255,0.03); }
.step-tab.active { color: var(--blue); border-bottom-color: var(--blue); background: rgba(0,120,255,0.05); }
.step-tab.disabled { opacity: 0.35; cursor: not-allowed; }
.step-tab.done { color: var(--green); }
.step-num {
  display: flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 50%;
  background: var(--card-h); font-size: 11px; font-weight: 700;
}
.step-tab.active .step-num { background: var(--blue); color: #fff; }
.step-tab.done .step-num { background: var(--green); color: #fff; }
.step-label { font-weight: 600; }

/* Main */
.main-content { padding: 24px; max-width: 1600px; margin: 0 auto; }
.panel { animation: fi 0.3s ease-out; }
@keyframes fi { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.fade-enter-from { opacity: 0; transform: translateY(8px); }
.fade-leave-to { opacity: 0; transform: translateY(-8px); }

/* Error */
.error-banner {
  display: flex; align-items: center; gap: 10px; padding: 12px 16px; margin-bottom: 16px;
  background: rgba(255,77,77,0.1); border: 1px solid rgba(255,77,77,0.25); border-radius: 10px; color: var(--red); font-size: 13px;
}
.dismiss { margin-left: auto; background: none; border: none; color: var(--red); cursor: pointer; font-size: 16px; }

/* Panel head */
.panel-head { margin-bottom: 24px; }
.panel-head h2 { font-size: 24px; font-weight: 700; margin: 0 0 6px; }
.sub { color: var(--ts); font-size: 14px; margin: 0; }
.sec { margin-bottom: 28px; }
.sec-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; margin: 0 0 16px; }

/* Setup */
.setup-grid { display: flex; flex-direction: column; gap: 24px; margin-bottom: 24px; }
.fld-label { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--ts); margin-bottom: 8px; display: block; }
.opt { font-weight: 400; text-transform: none; letter-spacing: 0; }
.txt {
  background: rgba(10,22,40,0.6); border: 1px solid var(--bdr); border-radius: 8px; padding: 12px 16px;
  color: var(--tp); font: inherit; font-size: 15px; transition: border-color 0.2s; width: 100%; box-sizing: border-box;
}
.txt:focus { outline: none; border-color: var(--blue); }
.txt::placeholder { color: var(--ts); }
.txt option { background: var(--card); color: var(--tp); }

.sport-options { display: flex; gap: 12px; }
.sport-opt {
  display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 16px 24px;
  background: var(--card); border: 1px solid var(--bdr); border-radius: 12px; color: var(--ts);
  cursor: pointer; transition: all 0.2s; flex: 1;
}
.sport-opt:hover { border-color: var(--bdr-a); color: var(--tp); }
.sport-opt.sel { border-color: var(--blue); background: rgba(0,120,255,0.1); color: var(--tp); }
.sport-ico { width: 32px; height: 32px; }
.sport-ico svg { width: 100%; height: 100%; }

.teams-row { display: flex; align-items: flex-end; gap: 16px; }
.team-field { flex: 1; }
.input-wrap { position: relative; }
.vs { font-size: 14px; font-weight: 700; color: var(--orange); padding-bottom: 12px; }
.spin {
  position: absolute; right: 12px; top: 50%; transform: translateY(-50%);
  width: 16px; height: 16px; border: 2px solid var(--bdr); border-top-color: var(--blue);
  border-radius: 50%; animation: sp 0.8s linear infinite;
}
@keyframes sp { to { transform: translateY(-50%) rotate(360deg); } }
.sug-list {
  position: absolute; top: 100%; left: 0; right: 0; background: var(--card); border: 1px solid var(--bdr);
  border-radius: 8px; margin-top: 4px; padding: 0; list-style: none; z-index: 10; max-height: 200px; overflow-y: auto;
}
.sug-list li { padding: 10px 16px; cursor: pointer; transition: background 0.2s; }
.sug-list li:hover { background: var(--card-h); }

/* Research */
.research-bar { text-align: center; margin-bottom: 24px; }
.research-btn {
  display: inline-flex; align-items: center; gap: 8px; padding: 14px 32px; background: var(--blue);
  color: #fff; border: none; border-radius: 10px; font-size: 15px; font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.research-btn:hover:not(:disabled) { background: #0066dd; box-shadow: 0 4px 16px var(--glow-b); transform: translateY(-2px); }
.research-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-spin {
  width: 18px; height: 18px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff;
  border-radius: 50%; animation: sp 0.8s linear infinite;
}
.hint { color: var(--ts); font-size: 12px; margin-top: 8px; }

/* Skeletons */
.skel-wrap { display: flex; flex-direction: column; gap: 12px; padding: 24px; background: var(--card); border-radius: 12px; border: 1px solid var(--bdr); }
.skel {
  height: 60px; background: linear-gradient(90deg, var(--card-h) 25%, #1e3554 50%, var(--card-h) 75%);
  background-size: 200% 100%; animation: shim 1.5s infinite; border-radius: 8px;
}
.skel.short { height: 40px; width: 60%; }
@keyframes shim { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
.skel-text { color: var(--ts); font-size: 14px; text-align: center; margin-top: 8px; }

/* Done card */
.done-card {
  text-align: center; padding: 32px; background: var(--card); border-radius: 12px; border: 1px solid var(--green);
}
.done-check { font-size: 48px; color: var(--green); margin-bottom: 12px; }
.done-card h3 { margin: 0 0 8px; font-size: 20px; }
.done-card p { color: var(--ts); margin: 0 0 20px; }
.go-btn {
  padding: 14px 32px; background: var(--orange); color: #fff; border: none; border-radius: 10px;
  font-size: 15px; font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.go-btn:hover { background: #e85a28; box-shadow: 0 4px 16px var(--glow-o); transform: translateY(-2px); }

/* Pre-game content */
.pre-content { display: flex; flex-direction: column; gap: 32px; }
.story-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.story-card { display: flex; gap: 12px; padding: 16px; background: var(--card); border: 1px solid var(--bdr); border-radius: 10px; }
.story-n {
  display: flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 50%;
  background: var(--blue); color: #fff; font-size: 12px; font-weight: 700; flex-shrink: 0;
}
.story-card p { margin: 0; font-size: 14px; line-height: 1.5; }

.mu-list { display: flex; flex-direction: column; gap: 8px; }
.mu-row {
  display: flex; align-items: center; justify-content: center; gap: 16px; padding: 12px 16px;
  background: var(--card); border: 1px solid var(--bdr); border-radius: 8px;
}
.mu-p { font-weight: 600; font-size: 14px; }
.mu-p.home { color: var(--blue); }
.mu-p.away { color: var(--orange); }
.mu-vs { color: var(--ts); font-size: 12px; font-weight: 700; }

.lu-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.lu-col { padding: 16px; background: var(--card); border: 1px solid var(--bdr); border-radius: 10px; }
.lu-col.home { border-top: 3px solid var(--blue); }
.lu-col.away { border-top: 3px solid var(--orange); }
.lu-col h4 { margin: 0 0 12px; font-size: 16px; font-weight: 700; }
.lu-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
.lu-list li { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--bdr); font-size: 14px; }
.lu-list li:last-child { border-bottom: none; }
.lu-num { font-weight: 700; color: var(--ts); min-width: 28px; }
.lu-name { flex: 1; font-weight: 500; }
.lu-pos { color: var(--ts); font-size: 12px; }

.watch-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.watch-list li { padding: 12px 16px; background: var(--card); border: 1px solid var(--bdr); border-radius: 8px; font-size: 14px; line-height: 1.5; }

/* Panel footer */
.panel-foot { display: flex; justify-content: space-between; gap: 12px; margin-top: 32px; padding-top: 24px; border-top: 1px solid var(--bdr); }
.primary {
  padding: 12px 24px; background: var(--orange); color: #fff; border: none; border-radius: 8px;
  font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.primary:hover:not(:disabled) { background: #e85a28; box-shadow: 0 4px 16px var(--glow-o); }
.primary:disabled { opacity: 0.5; cursor: not-allowed; }
.ghost {
  padding: 12px 24px; background: var(--card); color: var(--ts); border: 1px solid var(--bdr);
  border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; transition: all 0.2s;
}
.ghost:hover { border-color: var(--blue); color: var(--tp); }

/* Scoreboard */
.scoreboard {
  display: flex; align-items: center; justify-content: space-between; padding: 16px 24px;
  background: linear-gradient(135deg, #0d1f3c, #132238); border: 1px solid var(--bdr);
  border-radius: 12px; margin-bottom: 16px; transition: box-shadow 0.3s;
}
.scoreboard.flash { box-shadow: 0 0 20px rgba(0,200,83,0.2); }
.sb-team { display: flex; flex-direction: column; align-items: center; gap: 4px; min-width: 120px; }
.sb-name { font-size: 14px; font-weight: 600; }
.sb-score { font-size: 36px; font-weight: 800; transition: all 0.3s; }
.sb-score.up { color: var(--green); transform: scale(1.1); }
.sb-rec { font-size: 11px; color: var(--ts); }
.sb-center { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.sb-clock { font-size: 28px; font-weight: 800; font-variant-numeric: tabular-nums; }
.sb-period { font-size: 12px; color: var(--ts); text-transform: uppercase; letter-spacing: 0.05em; }
.poss { display: flex; align-items: center; }
.poss.home svg { color: var(--blue); }
.poss.away svg { color: var(--orange); }

/* State chips */
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
.chip {
  display: flex; flex-direction: column; align-items: center; padding: 8px 14px;
  background: var(--card); border: 1px solid var(--bdr); border-radius: 8px; font-size: 12px;
}
.chip b { font-size: 10px; text-transform: uppercase; color: var(--ts); letter-spacing: 0.05em; }
.chip span { font-weight: 600; }

/* Live grid */
.live-grid { display: grid; grid-template-columns: 30% 40% 30%; gap: 16px; margin-bottom: 16px; }
.col-hd { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-bottom: 1px solid var(--bdr); }
.col-hd h3 { font-size: 14px; font-weight: 600; margin: 0; }
.sport-tag { font-size: 11px; color: var(--ts); text-transform: uppercase; }

/* PBP column */
.pbp-col { background: var(--card); border: 1px solid var(--bdr); border-radius: 12px; display: flex; flex-direction: column; max-height: 600px; }
.filters { display: flex; gap: 4px; }
.fbtn {
  padding: 4px 10px; background: none; border: 1px solid var(--bdr); border-radius: 6px;
  color: var(--ts); font-size: 11px; cursor: pointer; transition: all 0.2s;
}
.fbtn.on { background: var(--blue); border-color: var(--blue); color: #fff; }
.pbp-feed { flex: 1; overflow-y: auto; padding: 8px; display: flex; flex-direction: column; gap: 4px; }
.pbp-feed::-webkit-scrollbar { width: 4px; }
.pbp-feed::-webkit-scrollbar-thumb { background: var(--bdr); border-radius: 2px; }
.pbp-ev { display: flex; align-items: flex-start; gap: 10px; padding: 10px; border-radius: 8px; transition: background 0.2s; }
.pbp-ev:hover { background: var(--card-h); }
.pbp-ev.home { border-left: 3px solid var(--blue); }
.pbp-ev.away { border-left: 3px solid var(--orange); }
.pbp-time { font-size: 11px; color: var(--ts); font-variant-numeric: tabular-nums; min-width: 50px; }
.pbp-emoji { font-size: 16px; min-width: 24px; text-align: center; }
.pbp-body { flex: 1; }
.pbp-txt { margin: 0 0 4px; font-size: 13px; line-height: 1.4; }
.pbp-actor { font-size: 11px; color: var(--ts); }
.empty { display: flex; align-items: center; justify-content: center; padding: 32px; color: var(--ts); font-size: 14px; }

/* Court column */
.court-col { background: var(--card); border: 1px solid var(--bdr); border-radius: 12px; display: flex; flex-direction: column; }
.court-wrap { flex: 1; display: flex; align-items: center; justify-content: center; padding: 16px; min-height: 400px; }
.court-svg { max-width: 100%; max-height: 450px; }
.generic-field { text-align: center; color: var(--ts); }
.generic-field svg { margin-bottom: 12px; opacity: 0.5; }
.generic-field p { font-size: 14px; }

/* Stats column */
.stats-col { background: var(--card); border: 1px solid var(--bdr); border-radius: 12px; display: flex; flex-direction: column; max-height: 600px; }
.team-tog { display: flex; gap: 4px; }
.tbtn {
  padding: 4px 10px; background: none; border: 1px solid var(--bdr); border-radius: 6px;
  color: var(--ts); font-size: 11px; cursor: pointer; transition: all 0.2s;
}
.tbtn.on { background: var(--blue); border-color: var(--blue); color: #fff; }
.stats-scroll { flex: 1; overflow-y: auto; padding: 8px; display: flex; flex-direction: column; gap: 6px; }
.stats-scroll::-webkit-scrollbar { width: 4px; }
.stats-scroll::-webkit-scrollbar-thumb { background: var(--bdr); border-radius: 2px; }
.stat-card { padding: 12px; background: var(--card-h); border: 1px solid var(--bdr); border-radius: 8px; transition: all 0.3s; }
.stat-card.hot { border-color: var(--green); box-shadow: 0 0 12px rgba(0,200,83,0.2); }
.stat-card.cold { border-color: var(--red); box-shadow: 0 0 12px rgba(255,23,68,0.2); }
.sc-hd { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.sc-num { font-size: 18px; font-weight: 800; color: var(--ts); }
.sc-info { display: flex; flex-direction: column; }
.sc-name { font-size: 13px; font-weight: 600; }
.sc-pos { font-size: 11px; color: var(--ts); }
.sc-body { display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; }
.sr { display: flex; flex-direction: column; align-items: center; padding: 4px; background: rgba(10,22,40,0.4); border-radius: 4px; }
.sr span { font-size: 9px; color: var(--ts); text-transform: uppercase; }
.sr b { font-size: 14px; font-weight: 700; }

/* Social feed */
.social-feed { background: var(--card); border: 1px solid var(--bdr); border-radius: 12px; overflow: hidden; }
.sf-hd { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-bottom: 1px solid var(--bdr); }
.sf-hd h3 { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 600; margin: 0; }
.sf-filters { display: flex; gap: 4px; }
.sff {
  padding: 4px 10px; background: none; border: 1px solid var(--bdr); border-radius: 6px;
  color: var(--ts); font-size: 11px; cursor: pointer; transition: all 0.2s;
}
.sff.on { background: var(--orange); border-color: var(--orange); color: #fff; }
.sf-scroll { display: flex; gap: 12px; padding: 12px 16px; overflow-x: auto; }
.sf-scroll::-webkit-scrollbar { height: 4px; }
.sf-scroll::-webkit-scrollbar-thumb { background: var(--bdr); border-radius: 2px; }
.react-card {
  display: flex; gap: 10px; padding: 12px; background: var(--card-h); border: 1px solid var(--bdr);
  border-radius: 10px; min-width: 260px; flex-shrink: 0;
}
.r-av { font-size: 24px; flex-shrink: 0; }
.r-top { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.r-handle { font-size: 12px; font-weight: 600; }
.r-type { font-size: 10px; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; font-weight: 600; }
.r-type.home { background: rgba(0,120,255,0.2); color: var(--blue); }
.r-type.away { background: rgba(255,107,53,0.2); color: var(--orange); }
.r-type.commentator { background: rgba(255,255,255,0.1); color: var(--ts); }
.r-txt { margin: 0; font-size: 13px; line-height: 1.4; }

/* Post-game */
.final-score {
  display: flex; align-items: center; justify-content: center; gap: 32px; padding: 24px;
  background: var(--card); border: 1px solid var(--bdr); border-radius: 12px; margin-bottom: 24px;
}
.fs-team { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.fs-name { font-size: 16px; font-weight: 600; }
.fs-num { font-size: 48px; font-weight: 800; }
.fs-num.win { color: var(--green); }
.fs-label { font-size: 14px; font-weight: 700; color: var(--ts); text-transform: uppercase; letter-spacing: 0.1em; }

.mvp-card {
  text-align: center; padding: 24px; background: linear-gradient(135deg, rgba(255,107,53,0.1), rgba(0,120,255,0.1));
  border: 1px solid var(--orange); border-radius: 12px; margin-bottom: 24px;
}
.mvp-badge { font-size: 14px; font-weight: 700; color: var(--orange); margin-bottom: 8px; }
.mvp-card h3 { margin: 0 0 4px; font-size: 24px; }
.mvp-card p { color: var(--ts); margin: 0; }

.perf-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.perf-card { padding: 16px; background: var(--card); border: 1px solid var(--bdr); border-radius: 10px; display: flex; flex-direction: column; gap: 4px; }
.perf-name { font-weight: 600; font-size: 14px; }
.perf-team { font-size: 12px; color: var(--ts); }
.perf-stats { font-size: 13px; color: var(--blue); font-weight: 600; }

.bs-wrap { overflow-x: auto; border-radius: 10px; border: 1px solid var(--bdr); }
.bs-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.bs-table th {
  padding: 10px 12px; text-align: left; background: var(--card-h); color: var(--ts);
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;
}
.bs-table td { padding: 8px 12px; border-top: 1px solid var(--bdr); }
.bs-table tr.home td { background: rgba(0,120,255,0.05); }
.bs-table tr.away td { background: rgba(255,107,53,0.05); }
.bs-player { font-weight: 600; }
.bs-grade { font-weight: 800; font-size: 14px; }
.gA { color: var(--green); } .gB { color: #66bb6a; } .gC { color: #ffc107; } .gD { color: var(--orange); } .gF { color: var(--red); }

.quotes-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; }
.quote-card { padding: 16px; background: var(--card); border: 1px solid var(--bdr); border-radius: 10px; border-left: 3px solid var(--blue); }
.quote-card p { margin: 0 0 8px; font-size: 14px; line-height: 1.5; font-style: italic; }
.quote-card cite { color: var(--ts); font-size: 12px; font-style: normal; }

.media-list { display: flex; flex-direction: column; gap: 8px; }
.media-card { padding: 12px 16px; background: var(--card); border: 1px solid var(--bdr); border-radius: 8px; }
.m-src { font-size: 11px; font-weight: 700; color: var(--blue); text-transform: uppercase; }
.media-card p { margin: 4px 0 0; font-size: 14px; line-height: 1.5; }

/* Chat */
.chat-layout { display: grid; grid-template-columns: 260px 1fr; gap: 16px; min-height: 500px; }
.chat-side { background: var(--card); border: 1px solid var(--bdr); border-radius: 12px; padding: 16px; display: flex; flex-direction: column; gap: 16px; }
.chat-sel { width: 100%; }
.dossier { padding: 12px; background: var(--card-h); border-radius: 8px; }
.dossier h4 { margin: 0 0 4px; font-size: 14px; }
.d-kind { display: inline-block; padding: 2px 8px; background: var(--blue); color: #fff; border-radius: 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; }
.dossier p { margin: 4px 0 0; font-size: 12px; color: var(--ts); line-height: 1.4; }

.chat-main { background: var(--card); border: 1px solid var(--bdr); border-radius: 12px; display: flex; flex-direction: column; }
.chat-msgs { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.chat-msgs::-webkit-scrollbar { width: 4px; }
.chat-msgs::-webkit-scrollbar-thumb { background: var(--bdr); border-radius: 2px; }
.chat-empty { display: flex; align-items: center; justify-content: center; flex: 1; color: var(--ts); font-size: 14px; text-align: center; }
.cmsg { display: flex; }
.cmsg.user { justify-content: flex-end; }
.cmsg.assistant { justify-content: flex-start; }
.cmsg-bub { max-width: 70%; padding: 12px 16px; border-radius: 12px; font-size: 14px; line-height: 1.5; }
.cmsg.user .cmsg-bub { background: var(--blue); color: #fff; border-bottom-right-radius: 4px; }
.cmsg.assistant .cmsg-bub { background: var(--card-h); border: 1px solid var(--bdr); border-bottom-left-radius: 4px; }
.cmsg-from { display: block; font-size: 11px; font-weight: 600; margin-bottom: 4px; opacity: 0.7; }
.cmsg-bub p { margin: 0; }
.cmsg-bub.typing { padding: 16px; }
.tdots { display: inline-block; width: 24px; height: 12px; position: relative; }
.tdots::before, .tdots::after {
  content: ''; position: absolute; width: 6px; height: 6px; border-radius: 50%;
  background: var(--ts); animation: typ 1.4s infinite;
}
.tdots::before { left: 0; animation-delay: 0s; }
.tdots::after { left: 9px; animation-delay: 0.2s; }
@keyframes typ { 0%,60%,100%{opacity:0.3;transform:translateY(0)} 30%{opacity:1;transform:translateY(-4px)} }

.chat-input { display: flex; gap: 8px; padding: 12px 16px; border-top: 1px solid var(--bdr); }
.chat-ta {
  flex: 1; background: rgba(10,22,40,0.6); border: 1px solid var(--bdr); border-radius: 8px;
  padding: 12px; color: var(--tp); font: inherit; font-size: 14px; resize: none;
}
.chat-ta:focus { outline: none; border-color: var(--blue); }
.send-btn {
  display: flex; align-items: center; justify-content: center; width: 44px; height: 44px;
  background: var(--blue); border: none; border-radius: 8px; color: #fff; cursor: pointer; transition: all 0.2s; flex-shrink: 0;
}
.send-btn:hover:not(:disabled) { background: #0066dd; }
.send-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* Responsive */
@media (max-width: 1200px) {
  .live-grid { grid-template-columns: 1fr 1fr; }
  .court-col { grid-column: 1 / -1; order: -1; }
}
@media (max-width: 960px) {
  .live-grid { grid-template-columns: 1fr; }
  .pbp-col, .court-col, .stats-col { max-height: 400px; }
  .chat-layout { grid-template-columns: 1fr; }
  .chat-side { flex-direction: row; flex-wrap: wrap; }
  .lu-grid { grid-template-columns: 1fr; }
  .teams-row { flex-direction: column; }
  .vs { display: none; }
  .sport-options { flex-direction: column; }
  .final-score { flex-direction: column; gap: 16px; }
  .broadcast-header { flex-direction: column; gap: 8px; padding: 12px 16px; }
  .step-nav { padding: 8px 16px; }
  .main-content { padding: 16px; }
}
@media (max-width: 640px) {
  .sb-score { font-size: 28px; }
  .sb-clock { font-size: 22px; }
  .sc-body { grid-template-columns: repeat(3, 1fr); }
  .quotes-grid { grid-template-columns: 1fr; }
  .step-label { display: none; }
  .step-tab { justify-content: center; }
}
</style>