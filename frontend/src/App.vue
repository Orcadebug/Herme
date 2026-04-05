<template>
  <div id="app-root">
    <router-view />
  </div>
</template>

<script setup>
</script>

<style>
/* Design System — Hermes Minimal */
:root {
  --bg: #ffffff;
  --surface: #f5f5f5;
  --border: #e5e5e5;
  --text: #171717;
  --muted: #737373;
  --subtle: #a3a3a3;
  --gold: #D4AF37;
  --gold-hover: #b8962e;
  --danger: #dc2626;

  --font-display: 'Barlow Condensed', sans-serif;
  --font-body: 'Barlow', sans-serif;

  --radius: 4px;
  --radius-md: 8px;
  --transition: 200ms ease;
}

/* Reset */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-size: 16px;
  scroll-behavior: smooth;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-body);
  font-weight: 400;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app-root {
  min-height: 100vh;
}

a {
  color: inherit;
  text-decoration: none;
}

button {
  font-family: var(--font-body);
  cursor: pointer;
}

input, select, textarea {
  font-family: var(--font-body);
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track { background: var(--surface); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--subtle); }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
