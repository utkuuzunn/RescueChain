<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('')
const password = ref('')
const errorMsg = ref('')
const isLoading = ref(false)

// IP ADRESİNİ GÜNCELLE!
const API_URL = 'http://192.168.217.129:5000/api/login'

const handleLogin = async () => {
  errorMsg.value = ''
  isLoading.value = true

  try {
    const res = await axios.post(API_URL, {
      username: username.value,
      password: password.value
    })

    const user = res.data.user
    
    // Yönlendirme
    if (user.role === 'admin') {
      router.push('/admin')
    } else {
      router.push(`/staff/${user.warehouse_id}?name=${user.full_name}&uid=${user.id}`)
    }

  } catch (e) {
    if (e.response && e.response.status === 401) {
      errorMsg.value = '❌ Kullanıcı bilgileri hatalı.'
    } else {
      errorMsg.value = '⚠️ Sunucuya erişilemiyor.'
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    
    <div class="left-panel">
      <div class="overlay">
        <div class="brand-content">
          <div class="logo-box">
            <h1>📦 RescueChain</h1>
          </div>
          <h2>Afet anında, yardım doğru yerde.</h2>
          <p>Huawei Cloud altyapısı ile güçlendirilmiş, yeni nesil lojistik yönetim sistemi.</p>
        </div>
        <div class="footer-brand">
          <span>Powered by <b>Huawei Cloud</b></span>
        </div>
      </div>
    </div>

    <div class="right-panel">
      <div class="form-wrapper">
        <div class="header">
          <h3>Hoş Geldiniz 👋</h3>
          <p>Lütfen hesabınıza giriş yapın</p>
        </div>

        <form @submit.prevent="handleLogin">
          
          <div class="input-group">
            <label>Kullanıcı Adı</label>
            <div class="input-wrapper">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
              <input type="text" v-model="username" placeholder="Kullanıcı adınız" required>
            </div>
          </div>

          <div class="input-group">
            <label>Şifre</label>
            <div class="input-wrapper">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
              <input type="password" v-model="password" placeholder="••••••" required>
            </div>
          </div>

          <button type="submit" :disabled="isLoading" class="login-btn">
            {{ isLoading ? 'Giriş Yapılıyor...' : 'GİRİŞ YAP' }}
            <svg v-if="!isLoading" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="arrow-icon"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
          </button>

          <div v-if="errorMsg" class="error-box">
            {{ errorMsg }}
          </div>
        </form>

        <div class="demo-info">
          <small>Demo: <b>admin</b> / <b>1234</b> veya <b>staff_istanbul</b> / <b>1234</b></small>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* KONTEYNER VE DÜZEN */
.login-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  background-color: #0f0f1a;
  color: #e0e0e0;
  overflow: hidden;
}

/* --- SOL PANEL (BRANDING) --- */
.left-panel {
  flex: 1.2;
  position: relative;
  background: linear-gradient(135deg, #0f0f1a 0%, #1e1e2e 100%), url('/login-bg.jpg'); 
  background-size: cover;
  background-position: center;
  /* Düzeltme Burası: İçeriği esnek kutu ile tam ortala */
  display: flex;
  align-items: center;     /* Dikey ortalama */
  justify-content: center; /* Yatay ortalama */
  text-align: center;      /* İçindeki metinleri ortala */
}

/* Resim üzerine koyu filtre */
.overlay {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(15, 15, 26, 0.85);
  /* Düzeltme Burası: Overlay de bir flex container olmalı */
  display: flex;
  flex-direction: column;
  align-items: center;      /* Yatayda ortala */
  justify-content: center;  /* Dikeyde ortala */
  padding: 40px;            /* Kenarlardan boşluk bırak */
}

.brand-content {
  /* Düzeltme: Maksimum genişlik verip ortalayalım */
  max-width: 600px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center; /* İçerikleri (Logo, yazı) ortala */
}

.logo-box {
  /* Logo kutusunu da garantiye alalım */
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}


/* --- SAĞ PANEL (FORM) --- */
.right-panel {
  flex: 1;
  background-color: #1e1e2e; /* Koyu Gri */
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  box-shadow: -10px 0 30px rgba(0,0,0,0.3); /* Soldan gölge */
  z-index: 2;
}

.form-wrapper {
  width: 100%;
  max-width: 400px;
}

.header { margin-bottom: 40px; }
.header h3 { font-size: 2rem; color: white; margin-bottom: 10px; }
.header p { color: #888; }

/* INPUT ALANLARI */
.input-group { margin-bottom: 25px; }
.input-group label { display: block; margin-bottom: 8px; font-size: 0.9rem; color: #ccc; font-weight: 600; }

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-wrapper input {
  width: 100%;
  padding: 15px 15px 15px 45px; /* İkon için soldan boşluk */
  background-color: #161622;
  border: 2px solid #2d2d3f;
  border-radius: 8px;
  color: white;
  font-size: 1rem;
  transition: all 0.3s;
}

.input-wrapper .icon {
  position: absolute;
  left: 15px;
  color: #666;
}

.input-wrapper input:focus {
  border-color: #3498db;
  background-color: #1a1a2e;
  outline: none;
  box-shadow: 0 0 0 4px rgba(52, 152, 219, 0.1);
}

.input-wrapper input:focus + .icon { color: #3498db; }

/* BUTON */
.login-btn {
  width: 100%;
  padding: 16px;
  background: linear-gradient(90deg, #3498db, #2980b9);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(52, 152, 219, 0.3);
}

.login-btn:disabled {
  background: #444;
  cursor: not-allowed;
  transform: none;
}

/* HATA MESAJI */
.error-box {
  margin-top: 20px;
  padding: 12px;
  background-color: rgba(231, 76, 60, 0.1);
  border: 1px solid #e74c3c;
  color: #e74c3c;
  border-radius: 6px;
  text-align: center;
  font-size: 0.9rem;
}

.demo-info {
  margin-top: 30px;
  text-align: center;
  color: #555;
  font-size: 0.85rem;
  border-top: 1px solid #2d2d3f;
  padding-top: 20px;
}

/* MOBİL UYUMLULUK */
@media (max-width: 900px) {
  .login-container { flex-direction: column; }
  .left-panel { flex: 0.4; padding: 20px; text-align: center; }
  .brand-content h1 { font-size: 2rem; }
  .brand-content h2 { display: none; }
  .brand-content p { display: none; }
  .right-panel { flex: 1; border-radius: 20px 20px 0 0; }
}
</style>
