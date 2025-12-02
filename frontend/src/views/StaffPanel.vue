<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const warehouseId = route.params.id
const staffName = route.query.name
const userId = route.query.uid

// Sekme Kontrolü
const activeTab = ref('incoming') // Varsayılan sekme: Gelen Kutusu

// Veriler
const warehouses = ref([]) // Hedef depo seçimi için
const incomingTransfers = ref([]) // Onay bekleyenler
const message = ref('')
const errorMsg = ref('')

// Formlar
const stockForm = ref({ item_name: 'Su (Koli)', quantity: 10 })
const transferForm = ref({ target_id: '', item_name: 'Su (Koli)', quantity: 10 })

// IP ADRESİNİ GÜNCELLE!
const API_BASE = 'http://192.168.217.129:5000/api'

const outgoingTransfers = ref([])
const inventory = ref([])

// Verileri Yükle
const loadData = async () => {
  try {
    // 1. Diğer depoları çek (Transfer yapmak için)
    const wRes = await axios.get(`${API_BASE}/warehouses`)
    // Kendim hariç diğer depoları listele
    warehouses.value = wRes.data.filter(w => w.id != warehouseId)

    // 2. Gelen Transferleri Çek
    const tRes = await axios.get(	`${API_BASE}/transfer/incoming/${warehouseId}`)
    incomingTransfers.value = tRes.data

    const outRes = await axios.get(`${API_BASE}/transfer/outgoing/${warehouseId}`)
    outgoingTransfers.value = outRes.data

    const invRes = await axios.get(`${API_BASE}/inventory/${warehouseId}`)
    inventory.value = invRes.data
  } catch (e) {
    console.error(e)
  }
}

onMounted(loadData)

// --- FONKSİYONLAR ---

// 1. Stok Girişi (Bağış)
const submitStockIn = async () => {
  try {
    await axios.post(`${API_BASE}/stock-in`, {
      user_id: userId,
      warehouse_id: warehouseId,
      ...stockForm.value
    })
    showMessage('✅ Stok Girişi Başarılı!')
  } catch (e) {
    showError(e.response?.data?.error || 'Hata oluştu')
  }
}

// 2. Transfer Başlat (Gönder)
const startTransfer = async () => {
  if(!transferForm.value.target_id) return showError("Lütfen hedef depo seçin!")
  
  try {
    await axios.post(`${API_BASE}/transfer/start`, {
      user_id: userId,
      source_id: warehouseId,
      ...transferForm.value
    })
    showMessage('🚚 Transfer Başlatıldı! Stoktan düşüldü.')
    loadData() // Listeleri güncelle
  } catch (e) {
    showError(e.response?.data?.error || 'Yetersiz Stok veya Hata')
  }
}

// 3. Transferi Kabul Et (Onayla)
const acceptTransfer = async (transferId) => {
  try {
    await axios.post(`${API_BASE}/transfer/complete`, {
      transfer_id: transferId,
      warehouse_id: warehouseId
    })
    showMessage('✅ Ürünler Teslim Alındı!')
    loadData() // Listeden kaldır
  } catch (e) {
    showError('Onaylama hatası')
  }
}

const cancelTransfer = async (transferId, isReject = false) => {
  if(!confirm(isReject ? "Bu sevkiyatı reddetmek istiyor musunuz?" : "Transferi iptal etmek istiyor musunuz?")) return;

  try {
    await axios.post(`${API_BASE}/transfer/cancel`, {
      transfer_id: transferId,
      reason: isReject ? 'Reddedildi' : 'İptal Edildi'
    })
    showMessage(isReject ? '⛔ Sevkiyat Reddedildi, iade edildi.' : '⛔ Transfer İptal Edildi, stok geri alındı.')
    loadData()
  } catch (e) {
    showError('İşlem hatası')
  }
}

// Yardımcılar
const showMessage = (msg) => { message.value = msg; setTimeout(() => message.value = '', 3000) }
const showError = (msg) => { errorMsg.value = msg; setTimeout(() => errorMsg.value = '', 3000) }
</script>

<template>
  <div class="staff-page">
    <header>
      <div class="header-info">
        <h2>👷 {{ staffName }} <small style="font-size: 0.6em; margin-left: 10px;">(Depo ID: {{ warehouseId }})</small></h2>
      </div>
      <router-link to="/" class="logout-btn">Çıkış Yap</router-link>
    </header>

    <div class="tabs">
      <button :class="{ active: activeTab === 'inventory' }" @click="activeTab = 'inventory'">📦 Envanter</button>
      <button :class="{ active: activeTab === 'stockin' }" @click="activeTab = 'stockin'">📥 Bağış Kabul</button>
      <button :class="{ active: activeTab === 'transfer' }" @click="activeTab = 'transfer'">🚚 Stok Transferi</button>
      <button :class="{ active: activeTab === 'incoming' }" @click="activeTab = 'incoming'">
        📬 Transfer Onayları 
        <span v-if="incomingTransfers.length" class="badge">{{ incomingTransfers.length }}</span>
      </button>
    </div>

    <div v-if="activeTab === 'stockin'" class="card">
      <h3>📥 Gelen Bağışlar</h3>
      <div class="form-group">
        <label>Ürün:</label>
        <select v-model="stockForm.item_name">
          <option>Su (Koli)</option>
          <option>Konserve Gıda (Koli)</option>
          <option>Battaniye</option>
          <option>Çadır</option>
          <option>Uyku Tulumu</option>
          <option>Isıtıcı</option>
          <option>Jeneratör</option>
          <option>İlk Yardım Çantası</option>
          <option>Tıbbi Malzeme (İlaç vb.)</option>
          <option>Kıyafet</option>
        </select>
        <input type="number" v-model="stockForm.quantity" min="1">
      </div>
      <button class="action-btn green" @click="submitStockIn">STOĞA EKLE</button>
    </div>

    <div v-if="activeTab === 'incoming'" class="card">
      <h3>📬 Onay Bekleyen Sevkiyatlar</h3>
      <div v-if="incomingTransfers.length === 0" class="empty-state">Bekleyen sevkiyat yok.</div>
      
      <div v-else class="transfer-list">
        <div v-for="t in incomingTransfers" :key="t.id" class="transfer-item incoming">
          <div class="info">
            <strong>{{ t.source_name }}</strong> deposundan<br>
            <span>{{ t.quantity }} adet {{ t.item_name }}</span>
          </div>
         
          <div class="btn-group">
            <button @click="acceptTransfer(t.id)" class="confirm-btn">KABUL ET ✅</button>
            <button @click="cancelTransfer(t.id, true)" class="reject-btn">REDDET ⛔</button>
          </div>
        </div>
      </div>
    </div>
    

    <div v-if="activeTab === 'transfer'" class="card">
      <h3>🚚 Başka Depoya Ürün Gönder</h3>
      
      <div class="form-group">
        <label>Hedef Depo:</label>
        <select v-model="transferForm.target_id">
          <option disabled value="">Seçiniz...</option>
          <option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }} ({{ w.city }})</option>
        </select>
      </div>
      
      <div class="form-group">
        <label>Gönderilecek Ürün:</label>
        <select v-model="transferForm.item_name">
          <option>Su (Koli)</option>
          <option>Konserve Gıda (Koli)</option>
          <option>Battaniye</option>
          <option>Çadır</option>
          <option>Uyku Tulumu</option>
          <option>Isıtıcı</option>
          <option>Jeneratör</option>
          <option>İlk Yardım Çantası</option>
          <option>Tıbbi Malzeme (İlaç vb.)</option>
          <option>Kıyafet</option>
        </select>
        <input type="number" v-model="transferForm.quantity" min="1" placeholder="Adet">
      </div>
      
      <button class="action-btn orange" @click="startTransfer">TRANSFERİ BAŞLAT</button>
      <small class="hint">* Onaylanana kadar "Yolda" görünecektir.</small>

      <hr class="divider">

      <h4>⏳ Yoldaki (Bekleyen) Gönderimleriniz</h4>
      <div v-if="outgoingTransfers.length === 0" class="empty-state">Bekleyen gönderim yok.</div>
      
      <div v-else class="transfer-list">
        <div v-for="t in outgoingTransfers" :key="t.id" class="transfer-item outgoing">
          <div class="info">
            <strong>Hedef: {{ t.target_name }}</strong><br>
            <span>{{ t.quantity }} adet {{ t.item_name }}</span>
          </div>
          <button @click="cancelTransfer(t.id, false)" class="cancel-btn">İPTAL ET ❌</button>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'inventory'" class="inventory-container">
      
      <div class="card inventory-card">
        <h3>🏠 Depodaki Ürünler (Mevcut)</h3>
        <p class="sub-text">Kullanıma veya sevkiyata hazır stoklarınız.</p>
        
        <div v-if="inventory.length === 0" class="empty-state">Depo şu an boş.</div>
        
        <ul v-else class="stock-list">
          <li v-for="(item, index) in inventory" :key="index">
            <span class="item-name">{{ item.item_name }}</span>
            <span class="item-qty">{{ item.quantity }} Adet</span>
          </li>
        </ul>
      </div>

      <div class="card inventory-card">
        <h3>🚀 Transferdeki Ürünler (Yolda)</h3>
        <p class="sub-text">Stoktan düşülen, onay bekleyenler.</p>
        
        <div v-if="outgoingTransfers.length === 0" class="empty-state">Yolda ürün yok.</div>
        
        <ul v-else class="stock-list transfer-mode">
          <li v-for="t in outgoingTransfers" :key="t.id">
            <div class="transfer-info">
              <span class="item-name">{{ t.item_name }}</span>
              <small>Hedef: {{ t.target_name }}</small>
            </div>
            <span class="item-qty warning">{{ t.quantity }} Adet</span>
          </li>
        </ul>
    </div>
    </div>

    <div v-if="message" class="toast success">{{ message }}</div>
    <div v-if="errorMsg" class="toast error">{{ errorMsg }}</div>

  </div>
</template>

<style scoped>
/* Modern Tab Tasarımı */
.staff-page { max-width: 600px; margin: 0 auto; padding: 20px; }
header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.logout-btn { color: #e74c3c; font-weight: bold; }

.tabs { display: flex; margin-bottom: 20px; border-bottom: 2px solid #3d3d50; }
.tabs button {
  flex: 1; padding: 15px; background: transparent; border: none; color: #888; cursor: pointer; font-size: 1rem; position: relative;
}
.tabs button.active { color: white; border-bottom: 3px solid #3498db; font-weight: bold; }
.badge { background: #e74c3c; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.7rem; position: absolute; top: 5px; right: 10px;}

.card { padding: 20px; border-radius: 10px; background: #2a2a3c; }
.form-group { margin-bottom: 15px; }
select, input { width: 100%; padding: 12px; margin-top: 5px; background: #181825; color: white; border: 1px solid #444; border-radius: 5px;}

.action-btn { width: 100%; padding: 15px; font-size: 1rem; border: none; border-radius: 6px; color: white; font-weight: bold; margin-top: 10px; }
.green { background: #27ae60; }
.orange { background: #e67e22; }

/* Transfer Listesi */
.transfer-item { display: flex; justify-content: space-between; align-items: center; background: #1e1e2e; padding: 15px; margin-bottom: 10px; border-radius: 8px; border-left: 4px solid #f1c40f; }
.info { font-size: 0.9rem; color: #ccc; }
.info span { color: white; font-weight: bold; font-size: 1rem; }
.confirm-btn { background: #3498db; color: white; border: none; padding: 8px 15px; border-radius: 5px; font-weight: bold; }
.confirm-btn:hover { background: #2980b9; }

.toast { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); padding: 15px 30px; border-radius: 30px; color: white; font-weight: bold; box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
.success { background: #27ae60; }
.error { background: #e74c3c; }
.hint { display: block; margin-top: 10px; color: #888; font-size: 0.8rem; text-align: center; }

.divider { margin: 20px 0; border: 0; border-top: 1px solid #444; }
.empty-state { text-align: center; color: #777; padding: 20px; font-style: italic; }

.transfer-item.outgoing { border-left-color: #e67e22; } /* Turuncu Kenar */
.transfer-item.incoming { border-left-color: #f1c40f; } /* Sarı Kenar */

.cancel-btn { background: #c0392b; color: white; border: none; padding: 8px 12px; border-radius: 5px; font-weight: bold; font-size: 0.8rem; }
.cancel-btn:hover { background: #e74c3c; }

.btn-group { display: flex; gap: 10px; }
.confirm-btn { background: #27ae60; color: white; border: none; padding: 8px 12px; border-radius: 5px; font-weight: bold; cursor: pointer;}
.reject-btn { background: #c0392b; color: white; border: none; padding: 8px 12px; border-radius: 5px; font-weight: bold; cursor: pointer;}

.inventory-container {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.inventory-card {
  flex: 1;
  min-width: 250px;
}

.sub-text {
  font-size: 0.85rem;
  color: #888;
  margin-bottom: 15px;
}

.stock-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.stock-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid #3d3d50;
  background: #1e1e2e;
  margin-bottom: 5px;
  border-radius: 6px;
}

.item-name {
  font-weight: bold;
  color: #e0e0e0;
}

.item-qty {
  background: #3498db;
  color: white;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: bold;
}

.item-qty.warning {
  background: #e67e22; /* Transferdekiler Turuncu olsun */
}

.transfer-mode li {
  border-left: 3px solid #e67e22;
}

.transfer-info {
  display: flex;
  flex-direction: column;
}

.transfer-info small {
  color: #aaa;
  font-size: 0.75rem;
}
</style>
