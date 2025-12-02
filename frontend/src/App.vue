<script setup>
</script>

<template>
  <router-view></router-view>
</template>

<style>
/* GLOBAL MODERN TEMA */
:root {
  --bg-color: #1e1e2e;       /* Koyu Arka Plan */
  --card-bg: #2a2a3c;        /* Kart Rengi */
  --text-color: #e0e0e0;     /* Açık Gri Yazı */
  --primary: #3498db;        /* Mavi Vurgu */
  --success: #2ecc71;        /* Yeşil */
  --danger: #e74c3c;         /* Kırmızı */
}

body {
  margin: 0;
  background-color: var(--bg-color);
  color: var(--text-color);
  font-family: 'Inter', 'Segoe UI', sans-serif;
  -webkit-font-smoothing: antialiased;
}

h1, h2, h3 { color: #ffffff; }

/* Kart Tasarımları */
.card, .form-card, .login-card {
  background-color: var(--card-bg);
  border: 1px solid #3d3d50;
  color: var(--text-color);
  box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}

/* Form Elemanları */
input, select {
  background-color: #181825;
  border: 1px solid #454555;
  color: white;
  padding: 10px;
  border-radius: 6px;
}
input:focus, select:focus {
  outline: 2px solid var(--primary);
  border-color: transparent;
}

/* Butonlar */
button {
  cursor: pointer;
  transition: all 0.2s;
}
button:hover { opacity: 0.9; transform: scale(1.02); }

/* Linkler */
a { color: var(--primary); text-decoration: none; }
</style>
