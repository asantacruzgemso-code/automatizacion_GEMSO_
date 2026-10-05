<script setup>
import { onMounted, ref } from 'vue'

const health = ref(null)
const error = ref('')
const checking = ref(false)

async function checkHealth() {
  checking.value = true
  error.value = ''

  try {
    const response = await fetch('/api/testdb')
    if (!response.ok) throw new Error(`API respondió ${response.status}`)
    health.value = await response.json()
  } catch (err) {
    health.value = null
    error.value = err.message || 'No se pudo conectar con la API'
  } finally {
    checking.value = false
  }
}

onMounted(checkHealth)
</script>

<template>
  <main class="shell">
    <header class="topbar">
      <a class="wordmark" href="/" aria-label="Proyecto Pulsador, inicio">
        <span class="mark">S</span>
        <span>PROYECTO <strong>Pulsador</strong></span>
      </a>
      <span class="environment"><i></i> ENTORNO LOCAL</span>
    </header>

    <section class="services" aria-label="Estado de los servicios">
      <div class="section-heading">
        <h2>SERVICIOS</h2>
        <button class="refresh" type="button" :disabled="checking" @click="checkHealth">
          <span :class="{ spinning: checking }" aria-hidden="true">↻</span>
          {{ checking ? 'VERIFICANDO' : 'COMPROBAR' }}
        </button>
      </div>

      <div class="service-row">
        <span class="service-index">01</span>
        <span class="service-name">Frontend</span>
        <span class="service-detail">Vue 3 <b>/</b> Vite</span>
        <span class="status"><i class="dot live"></i> ACTIVO</span>
      </div>
      <div class="service-row">
        <span class="service-index">02</span>
        <span class="service-name">API</span>
        <span class="service-detail">FastAPI <b>/</b> Python</span>
        <span class="status" :class="{ failed: error }">
          <i class="dot" :class="health ? 'live' : error ? 'down' : 'pending'"></i>
          {{ health ? 'CONECTADA' : error ? 'SIN CONEXIÓN' : 'VERIFICANDO' }}
        </span>
      </div>
      <div class="service-row">
        <span class="service-index">03</span>
        <span class="service-name">Base de datos</span>
        <span class="service-detail">PostgreSQL <b>/</b> Compose</span>
        <span class="status" :class="{ failed: error }">
          <i class="dot" :class="health?.database === 'connected' ? 'live' : error ? 'down' : 'pending'"></i>
          {{ health?.database === 'connected' ? 'CONECTADA' : error ? 'SIN CONEXIÓN' : 'VERIFICANDO' }}
        </span>
      </div>
      <p v-if="error" class="error-message" role="status">{{ error }}. Revisa que los servicios estén iniciados.</p>
    </section>

    <footer class="footer">
      <a href="http://localhost:8003/docs" target="_blank" rel="noreferrer">EXPLORAR API <span>↗</span></a>
    </footer>
  </main>
</template>
