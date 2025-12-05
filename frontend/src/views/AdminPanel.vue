<script setup>
import { onMounted, onUnmounted, ref } from 'vue' // onUnmounted eklendi
import axios from 'axios'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet-routing-machine'
import 'leaflet-routing-machine/dist/leaflet-routing-machine.css'

const transactions = ref([])
const activeTrucks = {}
let map = null
let warehouseLayer = null // Depolar için katman
let truckLayer = null     // Kamyonlar için katman (Bunu da ayırdık)

// ⚠️ IP Adresini Kontrol Et
const API_BASE = 'http://192.168.217.130:5000/api'

// --- İKONLAR ---
const vanIcon = L.divIcon({ className: 'vehicle-marker van', html: '<div style="font-size: 24px;">🚐</div>', iconSize: [40, 40], iconAnchor: [20, 20] })
const truckIcon = L.divIcon({ className: 'vehicle-marker truck', html: '<div style="font-size: 32px;">🚚</div>', iconSize: [50, 50], iconAnchor: [25, 25] })
const trailerIcon = L.divIcon({ className: 'vehicle-marker trailer', html: '<div style="font-size: 40px;">🚛</div>', iconSize: [60, 60], iconAnchor: [30, 30] })

const createWarehouseIcon = (colorClass) => {
  return L.divIcon({
    className: `warehouse-marker ${colorClass}`,
    html: '<div class="pin"></div>',
    iconSize: [40, 40],
    iconAnchor: [20, 40]
  })
}

// --- HARİTA BAŞLATMA ---
onMounted(async () => {
  // 1. ÖNCE ESKİ HARİTAYI KONTROL ET VE VARSA SİL (Duplicate Sorunu Çözümü)
  if (map) {
    map.remove()
    map = null
  }

  // 2. Haritayı Sıfırdan Başlat
  map = L.map('map').setView([39.0, 35.0], 6)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 18
  }).addTo(map)

  // 3. Katmanları Oluştur ve Haritaya Ekle
  warehouseLayer = L.layerGroup().addTo(map)
  truckLayer = L.layerGroup().addTo(map) // Kamyonlar için ayrı katman

  await loadMapData()
  startAnimationLoop()
})

// Sayfadan çıkınca haritayı temizle (Hafıza şişmesini önler)
onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})

const loadMapData = async () => {
  try {
    // 4. DEPOLAR KATMANINI TEMİZLE (Üst üste binmeyi engeller)
    if (warehouseLayer) warehouseLayer.clearLayers()

    // A. DEPOLARI ÇEK
    const wRes = await axios.get(`${API_BASE}/warehouses`)
    
    if (wRes.data && Array.isArray(wRes.data)) {
      wRes.data.forEach(w => {
        let totalStock = 0
        let popupHtml = `<div style="min-width:160px;"><h3 style="margin:0; color:#2c3e50;">${w.name}</h3><small>${w.city}</small><hr style="margin:5px 0;">`
        
        if(w.inventory && w.inventory.length > 0) {
          w.inventory.forEach(i => { 
            const qty = parseInt(i.quantity) || 0
            totalStock += qty 
            popupHtml += `<div style="display:flex; justify-content:space-between;"><span>${i.item_name}:</span> <b>${qty}</b></div>`
          })
        } else { popupHtml += "<i>Depo Boş</i>" }
        
        popupHtml += `<hr style="margin:5px 0;"><div style="display:flex; justify-content:space-between; font-size:1.1rem; color:#2c3e50;"><strong>TOPLAM STOK:</strong> <strong>${totalStock}</strong></div></div>`

        // Renk Mantığı
        let colorClass = 'blue'
        if (totalStock < 1000) colorClass = 'red'
        else if (totalStock > 5000) colorClass = 'green'

        // DİKKAT: warehouseLayer'a ekliyoruz (map'e değil)
        L.marker([w.latitude, w.longitude], { 
          icon: createWarehouseIcon(colorClass),
          zIndexOffset: 1000 
        }).addTo(warehouseLayer).bindPopup(popupHtml)
      })
    }

    // B. LOGLARI ÇEK
    const tRes = await axios.get(`${API_BASE}/transactions`)
    transactions.value = tRes.data

    // C. AKTİF SEVKİYATLARI ÇEK
    const sRes = await axios.get(`${API_BASE}/map/active-shipments`)
    if (sRes.data && Array.isArray(sRes.data)) {
        const activeShipments = sRes.data
        activeShipments.forEach(shipment => drawRouteAndTruck(shipment))
    }

  } catch (e) {
    console.error("Veri Hatası:", e)
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
    show: false, addWaypoints: false, fitSelectedRoutes: false
  }).addTo(map) // Rota çizgisi ana haritaya eklenebilir

  router.on('routesfound', function(e) {
    const coordinates = e.routes[0].coordinates 
    
    let selectedIcon = truckIcon
    let popupTitle = '🚚 STANDART SEVKİYAT'

    // 2. Hafif Araç (Van)
    if (transfer.vehicle_type === 'VAN') {
        selectedIcon = vanIcon
        popupTitle = '🚐 HAFİF SEVKİYAT'
    } 
    // 3. Ağır Araç (Tır)
    else if (transfer.vehicle_type === 'TRAILER') {
        selectedIcon = trailerIcon
        popupTitle = '🚛 AĞIR NAKLİYE'
    }

    // Marker oluştururken artık dinamik 'popupTitle' kullanıyoruz
    const marker = L.marker([transfer.source_lat, transfer.source_lng], { icon: selectedIcon })
      .addTo(truckLayer)
      .bindPopup(`
        <div style="text-align:center;">
            <b style="font-size:1.1rem; color:#2c3e50;">${popupTitle}</b>
        </div>
        <hr style="margin:5px 0; border-top:1px solid #eee;">
        <div style="max-width:200px; word-wrap:break-word; margin-bottom:5px;">
            ${transfer.summary}
        </div>
        <div style="background:#eee; padding:2px 5px; border-radius:4px; display:inline-block;">
            Toplam: <b>${transfer.total_weight} kg</b>
        </div>
      `)

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

// --- OTONOM SİSTEM DÖNGÜSÜ ---
const startAILoop = () => {
  setInterval(async () => {
    try {
      // Backend'deki AI fonksiyonunu tetikle
      const res = await axios.post(`${API_BASE}/ai/trigger-emergency`)
      
      // Eğer AI bir işlem yaptıysa (log döndüyse)
      if (res.data.logs && res.data.logs.length > 0) {
        // Haritayı yenile ki yeni kırmızı kamyonu görelim
        loadMapData()
        
        // Uyarı göster (Basit bir alert veya console log, ya da özel bir kutu yapabiliriz)
        res.data.logs.forEach(log => {
            console.warn(log)
            // İstersen buraya görsel bir bildirim (Toast) ekleyebiliriz
            alert(log) 
        })
      }
    } catch (e) {
      console.error("AI Sistemi Hatası:", e)
    }
  }, 10000) // Her 10 saniyede bir kontrol et
}

// onMounted içine de eklemeyi unutma:
onMounted(async () => {
  // ... (diğer kodlar) ...
  startAnimationLoop()
  startAILoop() // <--- BUNU EKLE
})

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
/* GENEL */
.admin-page { padding: 20px; font-family: 'Segoe UI', sans-serif; background-color: #1e1e2e; color: #ecf0f1; min-height: 100vh; }
header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #34495e; padding-bottom: 15px;}
header h2 { margin: 0; color: #3498db; }
.live-indicator { color: #e74c3c; font-weight: bold; margin-right: 20px; animation: blink 2s infinite; }
@keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
.logout-btn { color: #bdc3c7; text-decoration: none; border: 1px solid #555; padding: 5px 10px; border-radius: 4px; }
.logout-btn:hover { background: #e74c3c; color: white; border-color: #e74c3c; }

/* HARİTA */
#map { height: 500px; width: 100%; border-radius: 10px; border: 4px solid #34495e; margin-bottom: 30px; z-index: 1; background-color: white; }

/* TABLO */
.logs { background: #2a2a3c; padding: 20px; border-radius: 10px; border: 1px solid #3d3d50; }
.logs h3 { margin-top: 0; color: #f1c40f; border-bottom: 1px solid #444; padding-bottom: 10px; }
table { width: 100%; border-collapse: collapse; margin-top: 10px; }
th { background-color: #2c3e50; color: white; padding: 12px; text-align: left; border-bottom: 2px solid #3498db; }
td { padding: 12px; border-bottom: 1px solid #444; color: #bdc3c7; }
tbody tr:hover { background-color: #34495e; }

/* ROZETLER */
.badge { padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; color: white; font-weight: bold; }
.STOCK_IN { background: #27ae60; }
.TRANSFER { background: #f39c12; }
.status-badge { font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; margin-left: 5px; color: #fff; text-transform: uppercase; }
.PENDING { background-color: #e67e22; }
.COMPLETED { background-color: #27ae60; }
.CANCELLED { background-color: #c0392b; }

/* --- GLOBAL STİLLER (Harita Elementleri İçin) --- */
:deep(.vehicle-marker) {
  background: transparent;
  display: flex; justify-content: center; align-items: center;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5)); 
}

:deep(.warehouse-marker .pin) {
  width: 40px; height: 40px;
  border-radius: 50% 50% 50% 0;
  transform: rotate(-45deg);
  border: 3px solid white;
  box-shadow: 0 8px 15px rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center;
}
:deep(.warehouse-marker .pin::after) { content: ''; width: 12px; height: 12px; background: white; border-radius: 50%; }

:deep(.warehouse-marker.blue .pin) { background: #3498db; }
:deep(.warehouse-marker.green .pin) { background: #2ecc71; }
:deep(.warehouse-marker.red .pin) { background: #e74c3c; animation: pulse 2s infinite; }

@keyframes pulse { 0% { transform: rotate(-45deg) scale(1); } 50% { transform: rotate(-45deg) scale(1.1); } 100% { transform: rotate(-45deg) scale(1); } }

:deep(.leaflet-popup-content-wrapper) { background: #fdfdfd; color: #333; }
:deep(.leaflet-popup-tip) { background: #fdfdfd; }
:deep(.leaflet-popup-content) { margin: 10px; line-height: 1.5; font-family: 'Segoe UI', sans-serif; }
</style>
