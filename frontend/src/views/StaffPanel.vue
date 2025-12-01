<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()

// URL'den parametreleri al (Giriş sayfasından gelenler)
const warehouseId = route.params.id
const staffName = route.query.name || 'Personel'
const userId = route.query.uid

const form = ref({ item_name: 'Su (Koli)', quantity: 10 })
const message = ref('')

// IP GÜNCELLE!
const API_URL = 'http://192.168.217.129:5000/api/stock-in'

const submitStock = async () => {
  try {
    await axios.post(API_URL, {
      user_id: userId,
      warehouse_id: warehouseId,
      item_name: form.value.item_name,
      quantity: form.value.quantity
    })
    message.value = '✅ Stok Girişi Başarılı!'
    setTimeout(() => message.value = '', 3000)
  } catch (e) {
    alert('Hata: ' + e.message)
  }
}
</script>

<template>
  <div class="staff-page">
    <header>
      <h2>👷 Saha Operasyon: {{ staffName }}</h2>
      <router-link to="/" class="logout">Çıkış</router-link>
    </header>

    <div class="card">
      <h3>📥 Stok Girişi / Bağış Kabul</h3>
      <div class="form-group">
        <label>Ürün Tipi:</label>
        <select v-model="form.item_name">
          <option>Su (Koli)</option>
          <option>Battaniye</option>
          <option>Çadır</option>
          <option>Jeneratör</option>
          <option>Tıbbi Malzeme</option>
        </select>
      </div>

      <div class="form-group">
        <label>Adet:</label>
        <input type="number" v-model="form.quantity" min="1">
      </div>

      <button @click="submitStock" class="save-btn">KAYDET VE GÖNDER</button>
      
      <p v-if="message" class="success">{{ message }}</p>
    </div>
  </div>
</template>

<style scoped>
.staff-page { max-width: 600px; margin: 0 auto; padding: 20px; font-family: sans-serif; }
header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
.card { background: #f8f9fa; padding: 30px; border-radius: 10px; border: 1px solid #ddd; }
.form-group { margin-bottom: 20px; }
label { display: block; margin-bottom: 5px; font-weight: bold; }
select, input { width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 5px; }
.save-btn { width: 100%; padding: 15px; background: #27ae60; color: white; border: none; font-size: 1.1rem; border-radius: 5px; cursor: pointer; }
.save-btn:hover { background: #219150; }
.success { color: green; text-align: center; margin-top: 10px; font-weight: bold; }
.logout { color: #c0392b; text-decoration: none; font-weight: bold; }
</style>
