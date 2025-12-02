<script setup>
import { onMounted, ref } from 'vue'
import axios from 'axios'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet-routing-machine'
import 'leaflet-routing-machine/dist/leaflet-routing-machine.css'

const transactions = ref([])
const activeTrucks = {} 
let map = null

// ⚠️ BURAYI KENDİ IP ADRESİNLE DEĞİŞTİR! (Örn: 192.168.1.35)
const API_BASE = 'http://192.168.217.129:5000/api'

// Kamyon İkonu
const truckIcon = L.divIcon({
  className: 'truck-marker',
  html: '<div style="font-size: 30px;">🚚</div>',
  iconSize: [40, 40],
  iconAnchor: [20, 20]
})

onMounted(async () => {
  // 1. Haritayı Başlat (Standart Aydınlık Görünüm)
  map = L.map('map').setView([39.0, 35.0], 6)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 18
  }).addTo(map)

  // 2. Verileri Çek
  await loadMapData()

  // 3. Animasyon Döngüsünü Başlat
  startAnimationLoop()
})

const loadMapData = async () => {
  try {
    // Depoları Çek ve Pinle
    const wRes = await axios.get(`${API_BASE}/warehouses`)
    
    wRes.data.forEach(w => {
      let stockHtml = `<b style="font-size:14px;">${w.name}</b><br><hr>`
      if(w.inventory && w.inventory.length > 0) {
        w.inventory.forEach(i => { stockHtml += `${i.item_name}: <b>${i.quantity}</b><br>` })
      } else { stockHtml += "<i>Depo Boş</i>" }

      L.marker([w.latitude, w.longitude], { zIndexOffset: 1000 }).addTo(map).bindPopup(stockHtml)
    })

    // İşlem Geçmişini Çek
    const tRes = await axios.get(`${API_BASE}/transactions`)
    transactions.value = tRes.data

    // SADECE 'PENDING' (Yolda) olanları haritada canlandır
    const pendingTransfers = transactions.value.filter(t => t.type === 'TRANSFER' && t.status === 'PENDING')
    
    pendingTransfers.forEach(transfer => {
      drawRouteAndTruck(transfer)
    })

  } catch (e) {
    console.error("Veri hatası (IP Adresini kontrol et):", e)
    alert("Veriler yüklenemedi! Lütfen koddaki IP adresini kontrol et.")
  }
}

const drawRouteAndTruck = (transfer) => {
  if (activeTrucks[transfer.id]) return

  const router = L.Routing.control({
    waypoints: [
      L.latLng(transfer.source_lat, transfer.source_lng),
      L.latLng(transfer.target_lat, transfer.target_lng)
    ],
    router: L.Routing.osrmv1({ serviceUrl: 'https://router.project-osrm.org/route/v1' }),
    lineOptions: {
      styles: [{ color: '#e67e22', opacity: 0.8, weight: 6 }],
      interactive: false,
      addWaypoints: false
    },
    show: false, 
    addWaypoints: false,
    fitSelectedRoutes: false
  }).addTo(map)

  router.on('routesfound', function(e) {
    const coordinates = e.routes[0].coordinates 
    const marker = L.marker([transfer.source_lat, transfer.source_lng], { icon: truckIcon })
      .addTo(map)
      .bindPopup(`<b>🚛 Sevkiyat</b><br>${transfer.quantity} adet ${transfer.item_name}<br>Hedef: ${transfer.target_name}`)

    activeTrucks[transfer.id] = {
      marker: marker,
      path: coordinates,
      startTime: new Date(transfer.created_at).getTime(),
      duration: 60000 
    }
  })
}

const startAnimationLoop = () => {
  setInterval(() => {
    const now = Date.now()
    Object.keys(activeTrucks).forEach(id => {
      const truck = activeTrucks[id]
      const elapsed = now - truck.startTime
      const progress = (elapsed % truck.duration) / truck.duration
      const currentIndex = Math.floor(progress * truck.path.length)
      
      if (truck.path[currentIndex]) {
        truck.marker.setLatLng([truck.path[currentIndex].lat, truck.path[currentIndex].lng])
      }
    })
  }, 100)
}
</script>

<template>
  <div class="admin-page">
    <header>
      <h2>🌍 Komuta Kontrol Merkezi</h2>
      <div class="header-right">
         <span class="live-indicator">● CANLI AKIŞ</span>
         <router-link to="/" class="logout-btn">Çıkış</router-link>
      </div>
    </header>

    <div id="map"></div>

    <div class="logs">
      <h3>📡 Operasyon Günlüğü</h3>
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
            <td>{{ new Date(t.created_at).toLocaleString('tr-TR') }}</td>
            <td>
              <span :class="'badge ' + t.type">{{ t.type === 'STOCK_IN' ? 'GİRİŞ' : 'TRANSFER' }}</span>
              <span v-if="t.type === 'TRANSFER'" :class="'status-badge ' + t.status">{{ t.status }}</span>
            </td>
            <td>{{ t.user_name }}</td>
            <td>
              <span v-if="t.type === 'STOCK_IN'">
                {{ t.source_name }} deposuna <b>{{ t.quantity }} adet {{ t.item_name }}</b> girişi yaptı.
              </span>
              <span v-else-if="t.type === 'TRANSFER'">
                {{ t.target_name }} deposuna <b>{{ t.quantity }} adet {{ t.item_name }}</b> transferi gerçekleştirdi.
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
/* Genel Sayfa Yapısı */
.admin-page { 
  padding: 20px; 
  font-family: 'Segoe UI', sans-serif; 
  background-color: #1e1e2e; /* Arka plan koyu kalabilir, şık durur */
  color: #ecf0f1; 
  min-height: 100vh; 
}

header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 20px; 
  border-bottom: 1px solid #34495e; 
  padding-bottom: 15px;
}
header h2 { margin: 0; color: #3498db; }

.live-indicator { color: #e74c3c; font-weight: bold; margin-right: 20px; animation: blink 2s infinite; }
@keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }

.logout-btn { color: #bdc3c7; text-decoration: none; border: 1px solid #555; padding: 5px 10px; border-radius: 4px; }
.logout-btn:hover { background: #e74c3c; color: white; border-color: #e74c3c; }

/* Harita Ayarları */
#map { 
  height: 500px; /* Yükseklik sabit */
  width: 100%; 
  border-radius: 10px; 
  border: 4px solid #34495e; 
  margin-bottom: 30px; 
  z-index: 1;
  background-color: white; /* Harita yüklenmezse beyaz görünsün */
}

/* Tablo Tasarımı */
.logs { background: #2a2a3c; padding: 20px; border-radius: 10px; border: 1px solid #3d3d50; }
.logs h3 { margin-top: 0; color: #f1c40f; border-bottom: 1px solid #444; padding-bottom: 10px; }

table { width: 100%; border-collapse: collapse; margin-top: 10px; }
th { background-color: #2c3e50; color: white; padding: 12px; text-align: left; border-bottom: 2px solid #3498db; }
td { padding: 12px; border-bottom: 1px solid #444; color: #bdc3c7; }
tbody tr:hover { background-color: #34495e; }

/* Rozetler */
.badge { padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; color: white; font-weight: bold; }
.STOCK_IN { background: #27ae60; }
.TRANSFER { background: #f39c12; }
.status-badge { font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; margin-left: 5px; color: #fff; text-transform: uppercase; }
.PENDING { background-color: #e67e22; }
.COMPLETED { background-color: #27ae60; }
.CANCELLED { background-color: #c0392b; }
</style>
