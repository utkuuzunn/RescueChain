<script setup>
import { onMounted, ref } from 'vue'
import axios from 'axios'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css' // Harita CSS'i

const transactions = ref([])
// IP GÜNCELLE!
const API_BASE = 'http://192.168.217.129:5000/api'

onMounted(async () => {
  // 1. Haritayı Başlat (Türkiye Odaklı)
  const map = L.map('map').setView([39.0, 35.0], 6)
  
  // OpenStreetMap katmanını ekle
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map)

  // 2. Depoları Çek ve Pinle
  const wRes = await axios.get(`${API_BASE}/warehouses`)
  wRes.data.forEach(w => {
    // Depo içindeki stokları HTML listesi yap
    let stockHtml = '<b>' + w.name + '</b><br><hr>'
    if(w.inventory && w.inventory.length > 0) {
        w.inventory.forEach(i => {
            stockHtml += `${i.item_name}: ${i.quantity}<br>`
        })
    } else {
        stockHtml += "<i>Depo Boş</i>"
    }

    // Haritaya Marker Ekle
    L.marker([w.latitude, w.longitude])
      .addTo(map)
      .bindPopup(stockHtml)
  })

  // 3. İşlem Geçmişini Çek
  const tRes = await axios.get(`${API_BASE}/transactions`)
  transactions.value = tRes.data
})
</script>

<template>
  <div class="admin-page">
    <header>
      <h2>🌍 Komuta Kontrol Merkezi (Admin)</h2>
      <router-link to="/">Çıkış</router-link>
    </header>

    <div id="map"></div>

    <div class="logs">
      <h3>📡 Canlı Operasyon Akışı</h3>
      <table>
        <thead>
          <tr>
            <th>Zaman</th>
            <th>İşlem</th>
            <th>Personel</th>
            <th>Detay</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in transactions" :key="t.id">
            <td>{{ new Date(t.created_at).toLocaleTimeString() }}</td>
            <td><span :class="'badge ' + t.type">{{ t.type }}</span></td>
            <td>{{ t.user_name }}</td>
            <td>{{ t.source_name }} deposuna {{ t.quantity }} adet {{ t.item_name }} girişi yaptı.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.admin-page { padding: 20px; font-family: sans-serif; }
header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
#map { height: 400px; width: 100%; border-radius: 10px; border: 2px solid #34495e; margin-bottom: 30px; }
table { width: 100%; border-collapse: collapse; margin-top: 10px; }
th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
th { background: #f4f4f4; }
.badge { padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; color: white; }
.STOCK_IN { background: #27ae60; }
.TRANSFER { background: #f39c12; }
</style>
