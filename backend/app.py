# nano app.py
from flask import Flask, jsonify, request
from db import get_db_connection
from flask_cors import CORS
import uuid

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({"message": "RescueChain API 2.0 (Admin/Staff) Calisiyor! 🚀"})

ITEM_WEIGHTS = {
    'Su (Koli)': 12,       # 1 koli su yaklaşık 12kg
    'Konserve Gıda (Koli)': 10,
    'Battaniye': 2,
    'Çadır': 50,           # Büyük afet çadırı
    'Uyku Tulumu': 1.5,
    'Isıtıcı': 5,
    'Jeneratör': 100,       # Ağır yük!
    'İlk Yardım Çantası': 3,
    'Tıbbi Malzeme (İlaç vb.)': 5,
    'Kıyafet': 10,         # 1 çuval/koli kıyafet
}

def calculate_vehicle(item_name, quantity):
    unit_weight = ITEM_WEIGHTS.get(item_name, 10) # Bilinmeyen ürünse varsayılan 10kg
    total_weight = unit_weight * quantity

    if total_weight < 5000:
        return 'VAN', total_weight # Kamyonet
    elif total_weight < 10000:
        return 'TRUCK', total_weight # Kamyon
    else:
        return 'TRAILER', total_weight # Tır

# --- YENİ EKLENECEK LOGIN FONKSİYONU ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Kullanıcıyı ve şifresini kontrol et
    # (Not: Gerçek hayatta şifreler hash'lenmeli ama MVP için düz metin kalsın)
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({
            "message": "Giriş Başarılı",
            "user": {
                "id": user['id'],
                "username": user['username'],
                "role": user['role'],
                "warehouse_id": user['warehouse_id'],
                "full_name": user['full_name']
            }
        }), 200
    else:
        return jsonify({"error": "Kullanıcı adı veya şifre hatalı!"}), 401

# 1. Login Simülasyonu (Kullanıcıları Listele)
@app.route('/api/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username, full_name, role, warehouse_id FROM users")
    users = cursor.fetchall()
    conn.close()
    return jsonify(users)

# 2. Admin: Tüm Depoları ve Stokları Getir (Harita İçin)
@app.route('/api/warehouses', methods=['GET'])
def get_warehouses_with_stock():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Depoları çek
    cursor.execute("SELECT * FROM warehouses")
    warehouses = cursor.fetchall()

    # Her deponun stoğunu içine göm
    for w in warehouses:
        cursor.execute("SELECT item_name, quantity FROM inventory WHERE warehouse_id = %s", (w['id'],))
        w['inventory'] = cursor.fetchall()

    conn.close()
    return jsonify(warehouses)

# 3. Admin: Tüm İşlem Geçmişi (Koordinatlı)
@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # DİKKAT: Her satırın sonunda virgül olduğuna emin ol!
    sql = """
    SELECT
        t.*,
        u.full_name as user_name,
        w_source.name as source_name,
        w_source.latitude as source_lat,
        w_source.longitude as source_lng,
        w_target.name as target_name,
        w_target.latitude as target_lat,
        w_target.longitude as target_lng
    FROM transactions t
    LEFT JOIN users u ON t.performed_by = u.id
    LEFT JOIN warehouses w_source ON t.source_warehouse_id = w_source.id
    LEFT JOIN warehouses w_target ON t.target_warehouse_id = w_target.id
    ORDER BY t.created_at DESC
    """
    cursor.execute(sql)
    data = cursor.fetchall()

    for row in data:
        if row['type'] == 'TRANSFER':
            vehicle, weight = calculate_vehicle(row['item_name'], row['quantity'])
            row['vehicle_type'] = vehicle
            row['total_weight'] = weight

    conn.close()
    return jsonify(data)

# 4. Staff: Stok Ekleme (Fiziksel Bağış Girişi)
@app.route('/api/stock-in', methods=['POST'])
def stock_in():
    data = request.json
    user_id = data.get('user_id')
    warehouse_id = data.get('warehouse_id')
    item_name = data.get('item_name')
    quantity = int(data.get('quantity'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Stoğu Artır
        sql_update = """
        INSERT INTO inventory (warehouse_id, item_name, quantity)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
        """
        cursor.execute(sql_update, (warehouse_id, item_name, quantity))

        # Log Kaydı At
        sql_log = "INSERT INTO transactions (type, source_warehouse_id, target_warehouse_id, item_name, quantity, performed_by) VALUES ('STOCK_IN', %s, %s, %s, %s, %s)"
        cursor.execute(sql_log, (warehouse_id, warehouse_id, item_name, quantity, user_id))

        conn.commit()
        return jsonify({"msg": "Stok Girişi Başarılı"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# --- YENİ TRANSFER FONKSİYONLARI ---

# 5. Transfer Başlat (Kaynaktan düş, Transfer kaydı aç)
@app.route('/api/transfer/start', methods=['POST'])
def start_transfer():
    data = request.json
    source_id = data.get('source_id')
    target_id = data.get('target_id')
    user_id = data.get('user_id')
    items = data.get('items')
      
    if not items or len(items) == 0:
        return jsonify({"error": "Sepet boş!"}), 400

    if source_id == target_id:
        return jsonify({"error": "Aynı depoya transfer yapılamaz!"}), 400
    group_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Önce kaynak depoda yeterli stok var mı kontrol et?

# Stok Kontrolü
        for item in items:
            cursor.execute("SELECT quantity FROM inventory WHERE warehouse_id = %s AND item_name = %s", (source_id, item['item_name']))
            stock = cursor.fetchone()
            if not stock or stock['quantity'] < int(item['quantity']):
                raise Exception(f"Yetersiz Stok: {item['item_name']}")

        # İşleme Başla
        for item in items:
            qty = int(item['quantity'])
            name = item['item_name']

            # Stoktan Düş
            cursor.execute("UPDATE inventory SET quantity = quantity - %s WHERE warehouse_id = %s AND item_name = %s", (qty, source_id, name))

            # YENİ: transfer_group_id ile kaydet
            sql_log = """
                INSERT INTO transactions 
                (type, source_warehouse_id, target_warehouse_id, item_name, quantity, performed_by, status, transfer_group_id) 
                VALUES ('TRANSFER', %s, %s, %s, %s, %s, 'PENDING', %s)
            """
            cursor.execute(sql_log, (source_id, target_id, name, qty, user_id, group_id))




        conn.commit()
        return jsonify({"message": f"Sevkiyat birleştirildi ve yola çıktı. (ID: {group_id[:8]})"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# 6. Gelen Transferleri Listele (Sadece PENDING olanlar)
@app.route('/api/transfer/incoming/<int:warehouse_id>', methods=['GET'])
def get_incoming_transfers(warehouse_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Hedefi benim depom olan ve durumu PENDING olan işlemleri getir
    sql = """
        SELECT t.id, t.item_name, t.quantity, w.name as source_name, t.created_at
        FROM transactions t
        JOIN warehouses w ON t.source_warehouse_id = w.id
        WHERE t.target_warehouse_id = %s AND t.status = 'PENDING'
        ORDER BY t.created_at DESC
    """
    cursor.execute(sql, (warehouse_id,))
    transfers = cursor.fetchall()
    conn.close()
    return jsonify(transfers)

# 7. Transferi Kabul Et (Onayla ve Stoğa Ekle)
@app.route('/api/transfer/complete', methods=['POST'])
def complete_transfer():
    data = request.json
    transfer_id = data.get('transfer_id')
    warehouse_id = data.get('warehouse_id') # Alan depo ID

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Transfer detaylarını çek
        cursor.execute("SELECT * FROM transactions WHERE id = %s AND status = 'PENDING'", (transfer_id,))
        transfer = cursor.fetchone()

        if not transfer:
            return jsonify({"error": "Transfer bulunamadı veya zaten onaylanmış."}), 404

        # 2. Hedef depoya stoğu ekle
        sql_stock = """
            INSERT INTO inventory (warehouse_id, item_name, quantity)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
        """
        cursor.execute(sql_stock, (warehouse_id, transfer['item_name'], transfer['quantity']))

        # 3. İşlem durumunu 'COMPLETED' yap
        cursor.execute("UPDATE transactions SET status = 'COMPLETED' WHERE id = %s", (transfer_id,))

        conn.commit()
        return jsonify({"message": "Ürünler teslim alındı ve stoğa işlendi."}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# --- İPTAL VE REDDETME İŞLEMLERİ ---

# 8. Giden (Bekleyen) Transferleri Listele (Koordinatlı)
@app.route('/api/transfer/outgoing/<int:warehouse_id>', methods=['GET'])
def get_outgoing_transfers(warehouse_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT
            t.id, t.item_name, t.quantity, t.created_at,
            w.name as target_name,
            w.latitude as target_lat,
            w.longitude as target_lng,
            ws.latitude as source_lat,
            ws.longitude as source_lng
        FROM transactions t
        JOIN warehouses w ON t.target_warehouse_id = w.id
        JOIN warehouses ws ON t.source_warehouse_id = ws.id
        WHERE t.source_warehouse_id = %s AND t.status = 'PENDING'
        ORDER BY t.created_at DESC
    """
    cursor.execute(sql, (warehouse_id,))
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

# 9. Transfer İptal / Reddet (Ortak Fonksiyon)
@app.route('/api/transfer/cancel', methods=['POST'])
def cancel_transfer():
    data = request.json
    transfer_id = data.get('transfer_id')
    reason = data.get('reason', 'İptal Edildi') # "İptal" veya "Reddedildi"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Transfer bilgisini çek
        cursor.execute("SELECT * FROM transactions WHERE id = %s AND status = 'PENDING'", (transfer_id,))
        transfer = cursor.fetchone()

        if not transfer:
            return jsonify({"error": "Transfer bulunamadı veya zaten işlem görmüş."}), 404

        # 2. Stoğu KAYNAK (Source) depoya geri yükle
        sql_restore = """
            UPDATE inventory
            SET quantity = quantity + %s
            WHERE warehouse_id = %s AND item_name = %s
        """
        cursor.execute(sql_restore, (transfer['quantity'], transfer['source_warehouse_id'], transfer['item_name']))

        # 3. Transfer durumunu 'CANCELLED' yap
        cursor.execute("UPDATE transactions SET status = 'CANCELLED' WHERE id = %s", (transfer_id,))

        conn.commit()
        return jsonify({"message": f"İşlem başarıyla {reason}."}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/inventory/<int:warehouse_id>', methods=['GET'])
def get_warehouse_inventory(warehouse_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Sadece o depoya ait ve adedi 0'dan büyük ürünleri getir
    sql = "SELECT item_name, quantity FROM inventory WHERE warehouse_id = %s AND quantity > 0"
    cursor.execute(sql, (warehouse_id,))
    data = cursor.fetchall()

    conn.close()
    return jsonify(data)

# 11. Harita İçin Aktif Sevkiyatları Grupla (KONSOLİDASYON)
@app.route('/api/map/active-shipments', methods=['GET'])
def get_active_shipments():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Sadece PENDING olan transferleri çek (Koordinatlarla)
    sql = """
    SELECT 
        t.*, 
        w_source.latitude as source_lat, 
        w_source.longitude as source_lng,
        w_target.name as target_name,
        w_target.latitude as target_lat,
        w_target.longitude as target_lng
    FROM transactions t
    JOIN warehouses w_source ON t.source_warehouse_id = w_source.id
    JOIN warehouses w_target ON t.target_warehouse_id = w_target.id
    WHERE t.type = 'TRANSFER' AND t.status = 'PENDING'
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    
    # --- GRUPLAMA MANTIĞI ---
    shipments = {}
    
    for row in rows:
        # Eski kayıtların group_id'si NULL olabilir, onlara kendi ID'sini verelim
        gid = row['transfer_group_id'] if row['transfer_group_id'] else str(row['id'])
        
        if gid not in shipments:
            shipments[gid] = {
                'id': gid,
                'source_lat': row['source_lat'], 'source_lng': row['source_lng'],
                'target_lat': row['target_lat'], 'target_lng': row['target_lng'],
                'target_name': row['target_name'],
                'created_at': row['created_at'],
                'total_weight': 0,
                'items': [] # İçindeki ürünleri listeye atacağız
            }
        
        # Ağırlık Hesapla
        _, weight = calculate_vehicle(row['item_name'], row['quantity'])
        
        shipments[gid]['total_weight'] += weight
        shipments[gid]['items'].append(f"{row['quantity']} {row['item_name']}")

    # Şimdi her grubun toplam ağırlığına göre Araç Tipini belirle
    result_list = []
    for gid, data in shipments.items():
        if data['total_weight'] < 5000:
            data['vehicle_type'] = 'VAN'
        elif data['total_weight'] < 10000:
            data['vehicle_type'] = 'TRUCK'
        else:
            data['vehicle_type'] = 'TRAILER'
            
        # Ürün özet metni (Örn: "10 Su, 5 Çadır")
        data['summary'] = ", ".join(data['items'])
        result_list.append(data)

    conn.close()
    return jsonify(result_list)

# --- OTONOM AFET MÜDAHALE SİSTEMİ (AI) ---

import math

def calculate_distance(lat1, lon1, lat2, lon2):
    # İki koordinat arası kuş uçuşu mesafe (Haversine Formülü basitleştirilmiş)
    # Gerçek km hesabı için daha karmaşık formül gerekir ama bu kıyaslama için yeterli
    return math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2)

@app.route('/api/ai/trigger-emergency', methods=['POST'])
def trigger_emergency_ai():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    logs = []

    try:
        # 1. Tüm depoları ve stoklarını çek
        cursor.execute("SELECT * FROM warehouses")
        warehouses = cursor.fetchall()
        
        for w in warehouses:
            # Deponun toplam stoğunu hesapla
            cursor.execute("SELECT SUM(quantity) as total FROM inventory WHERE warehouse_id = %s", (w['id'],))
            res = cursor.fetchone()
            w['total_stock'] = int(res['total'] if res['total'] else 0)

        # 2. Yardıma Muhtaç (Kırmızı) ve Yardım Edebilecek (Yeşil) Depoları Ayır
        victims = [w for w in warehouses if w['total_stock'] < 1000]
        donors = [w for w in warehouses if w['total_stock'] > 5000]

        # 3. AI Mantığı: Her kurban için en uygun donörü bul
        for victim in victims:
            # Bu depoya halihazırda yola çıkmış bir yardım var mı? (Spam yapma)
            cursor.execute("""
                SELECT id FROM transactions 
                WHERE target_warehouse_id = %s AND status = 'PENDING' AND performed_by = (SELECT id FROM users WHERE username = 'system_ai')
            """, (victim['id'],))
            is_already_helped = cursor.fetchone()

            if is_already_helped:
                continue # Zaten yardım gidiyor, pas geç

            best_donor = None
            min_distance = 999999

            for donor in donors:
                # Mesafe hesabı
                dist = calculate_distance(float(victim['latitude']), float(victim['longitude']), 
                                          float(donor['latitude']), float(donor['longitude']))
                
                # Kural: En yakın olanı seç
                if dist < min_distance:
                    # Kural: Kendini yakmasın (3000 emniyet sübabı)
                    if (donor['total_stock'] - 500) > 3000:
                        min_distance = dist
                        best_donor = donor

            if best_donor:
                # 4. OPERASYON BAŞLAT: Otomatik Transfer
                # AI Kullanıcısının ID'sini bul
                cursor.execute("SELECT id FROM users WHERE username = 'system_ai'")
                ai_user = cursor.fetchone()
                
                # Eğer AI kullanıcısı yoksa oluştur
                if not ai_user:
                    cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES ('system_ai', '1234', '🤖 Otonom Afet Müdahale Sistemi', 'admin')")
                    conn.commit()
                    ai_user_id = cursor.lastrowid
                else:
                    ai_user_id = ai_user['id']

                # Yardım Paketi (Acil İhtiyaçlar)
                # Donörün elinde ne varsa ondan gönderelim (Basit mantık: Su ve Battaniye)
                relief_items = [
                    {'name': 'Su (Koli)', 'qty': 200},
                    {'name': 'Battaniye', 'qty': 100},
                    {'name': 'Çadır', 'qty': 20}
                ]
                
                group_id = str(uuid.uuid4())
                
                for item in relief_items:
                    # Donörde bu ürün var mı kontrol et
                    cursor.execute("SELECT quantity FROM inventory WHERE warehouse_id = %s AND item_name = %s", (best_donor['id'], item['name']))
                    stock_check = cursor.fetchone()
                    
                    if stock_check and stock_check['quantity'] > item['qty']:
                        # Stoktan düş
                        cursor.execute("UPDATE inventory SET quantity = quantity - %s WHERE warehouse_id = %s AND item_name = %s", 
                                       (item['qty'], best_donor['id'], item['name']))
                        
                        # Transfer Kaydı (AI)
                        sql_log = """
                            INSERT INTO transactions 
                            (type, source_warehouse_id, target_warehouse_id, item_name, quantity, performed_by, status, transfer_group_id) 
                            VALUES ('TRANSFER', %s, %s, %s, %s, %s, 'PENDING', %s)
                        """
                        cursor.execute(sql_log, (best_donor['id'], victim['id'], item['name'], item['qty'], ai_user_id, group_id))
                
                conn.commit()
                logs.append(f"🚨 ACİL DURUM: {victim['name']} stoğu kritik! {best_donor['name']} deposundan otomatik yardım yola çıktı.")

    except Exception as e:
        print("AI Hatası:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

    return jsonify({"logs": logs})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
