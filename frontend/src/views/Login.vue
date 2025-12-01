<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const users = ref([])
const router = useRouter()
// IP ADRESİNİ GÜNCELLE!
const API_URL = 'http://192.168.217.129:5000/api/users'

onMounted(async () => {
  const res = await axios.get(API_URL)
  users.value = res.data
})

const login = (user) => {
  if (user.role === 'admin') {
    router.push('/admin')
  } else {
    router.push(`/staff/${user.warehouse_id}?name=${user.username}&uid=${user.id}`)
  }
}
</script>

<template>
  <div class="login-container">
    <h1>🔐 RescueChain Giriş</h1>
    <p>Lütfen kullanıcı seçin (Demo Modu)</p>
    <div class="user-grid">
      <button v-for="user in users" :key="user.id" @click="login(user)" :class="user.role">
        <span class="role-badge">{{ user.role.toUpperCase() }}</span>
        <span class="name">{{ user.full_name }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.login-container { max-width: 500px; margin: 50px auto; text-align: center; font-family: sans-serif; }
.user-grid { display: flex; flex-direction: column; gap: 10px; margin-top: 20px; }
button { padding: 15px; border: 1px solid #ddd; background: white; cursor: pointer; display: flex; justify-content: space-between; align-items: center; font-size: 1rem; border-radius: 8px; transition: 0.2s; }
button:hover { background: #f8f9fa; transform: translateY(-2px); }
.role-badge { font-size: 0.8rem; padding: 4px 8px; border-radius: 4px; color: white; }
.admin .role-badge { background: #e74c3c; } /* Kırmızı */
.staff .role-badge { background: #3498db; } /* Mavi */
</style>
