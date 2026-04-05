<template>
  <div class="app-shell">
    <nav class="top-nav">
      <div class="nav-brand">
        <span class="nav-logo">&#9881;</span>
        <span class="nav-title">Hermes</span>
      </div>
      <div class="nav-links">
        <a href="https://github.com" target="_blank" rel="noopener noreferrer" class="nav-link">GitHub</a>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
//Use Vue Router to manage pages
</script>

<style>
/* CSS Custom Properties - Dark ESPN Theme */
:root {
  --bg-primary: #0a1628;
  --bg-secondary: #132238;
  --bg-tertiary: #1a2d4a;
  --accent-primary: #0078ff;
  --accent-secondary: #ff6b35;
  --text-primary: #ffffff;
  --text-secondary: #8899aa;
  --text-muted: #556677;
  --border-color: #1e3350;
  --success: #00c853;
  --danger: #ff4444;
  --warning: #ffbb33;
  --card-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);

  --nav-height: 56px;
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --transition-fast: 150ms ease;
  --transition-normal: 250ms ease;

  --breakpoint-sm: 576px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 992px;
  --breakpoint-xl: 1200px;
}

/* Global Reset */
html {
  font-size: 16px;
  scroll-behavior: smooth;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* App Shell */
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-primary);
}

.main-content {
  flex: 1;
  padding: 24px;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
}

/* Top Navigation */
.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--nav-height);
  padding: 0 24px;
  background-color: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.nav-logo {
  font-size: 1.5rem;
  color: var(--accent-primary);
}

.nav-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.5px;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 16px;
}

.nav-link {
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  transition: color var(--transition-fast);
}

.nav-link:hover {
  color: var(--text-primary);
}

/* Body & App */
body {
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Inter', 'JetBrains Mono', 'Space Grotesk', 'Noto Sans SC', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  line-height: 1.6;
}

#app {
  min-height: 100vh;
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

/* Links */
a {
  color: var(--accent-primary);
  text-decoration: none;
  transition: color 0.2s ease;
}

a:hover {
  color: var(--accent-secondary);
}

/* Buttons */
button {
  font-family: inherit;
  cursor: pointer;
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  font-weight: 500;
  transition: all 0.2s ease;
}

/* Inputs */
input, textarea, select {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 8px 12px;
  font-family: inherit;
  font-size: 14px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

input:focus, textarea:focus, select:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px rgba(0, 120, 255, 0.15);
}

input::placeholder, textarea::placeholder {
  color: var(--text-muted);
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
  background: var(--bg-tertiary);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}

/* Utility Classes */
.card {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  box-shadow: var(--card-shadow);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.btn-primary {
  background-color: var(--accent-primary);
  color: var(--text-primary);
  font-weight: 600;
}

.btn-primary:hover {
  background-color: #0066dd;
  transform: translateY(-1px);
}

.btn-secondary {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  background-color: var(--border-color);
}

.btn-success {
  background-color: var(--success);
  color: var(--text-primary);
  font-weight: 600;
}

.btn-danger {
  background-color: var(--danger);
  color: var(--text-primary);
  font-weight: 600;
}

.text-accent {
  color: var(--accent-primary);
}

.text-secondary {
  color: var(--text-secondary);
}

.text-muted {
  color: var(--text-muted);
}

.text-success {
  color: var(--success);
}

.text-danger {
  color: var(--danger);
}

.text-warning {
  color: var(--warning);
}

.bg-primary {
  background-color: var(--bg-primary);
}

.bg-secondary {
  background-color: var(--bg-secondary);
}

.bg-tertiary {
  background-color: var(--bg-tertiary);
}

.border {
  border: 1px solid var(--border-color);
}

/* Responsive Breakpoints */
@media (max-width: 768px) {
  .main-content {
    padding: 16px;
  }

  .top-nav {
    padding: 0 16px;
  }

  .card {
    padding: 16px;
    border-radius: 8px;
  }

  .grid-2,
  .grid-3,
  .grid-4 {
    grid-template-columns: 1fr;
  }
}

@media (min-width: 769px) and (max-width: 992px) {
  .grid-3,
  .grid-4 {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 993px) and (max-width: 1200px) {
  .grid-4 {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 480px) {
  .card {
    padding: 12px;
  }
  
  button {
    padding: 6px 12px;
    font-size: 14px;
  }
}

/* Grid Utilities */
.grid {
  display: grid;
  gap: 20px;
}

.grid-2 {
  grid-template-columns: repeat(2, 1fr);
}

.grid-3 {
  grid-template-columns: repeat(3, 1fr);
}

.grid-4 {
  grid-template-columns: repeat(4, 1fr);
}

/* Flex Utilities */
.flex {
  display: flex;
}

.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.flex-col {
  flex-direction: column;
}

.gap-sm { gap: 8px; }
.gap-md { gap: 16px; }
.gap-lg { gap: 24px; }
</style>
