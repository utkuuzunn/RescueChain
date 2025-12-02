# nano app.py
from flask import Flask, jsonify, request
from db import get_db_connection
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({"message": "RescueChain API 2.0 (Admin/Staff) Calisiyor! 🚀"})

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
    item_name = data.get('item_name')
    quantity = int(data.get('quantity'))
    user_id = data.get('user_id')

    if source_id == target_id:
        return jsonify({"error": "Aynı depoya transfer yapılamaz!"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Önce kaynak depoda yeterli stok var mı kontrol et?
        cursor.execute("SELECT quantity FROM inventory WHERE warehouse_id = %s AND item_name = %s", (source_id, item_name))
        stock = cursor.fetchone()

        if not stock or stock['quantity'] < quantity:
            return jsonify({"error": "Yetersiz Stok! Gönderim yapılamaz."}), 400

        # 2. Kaynak depodan stoğu düş
        cursor.execute("UPDATE inventory SET quantity = quantity - %s WHERE warehouse_id = %s AND item_name = %s", (quantity, source_id, item_name))

        # 3. Transfer kaydını 'PENDING' (Yolda) olarak oluştur
        sql_log = """
            INSERT INTO transactions 
            (type, source_warehouse_id, target_warehouse_id, item_name, quantity, performed_by, status) 
            VALUES ('TRANSFER', %s, %s, %s, %s, %s, 'PENDING')
        """
        cursor.execute(sql_log, (source_id, target_id, item_name, quantity, user_id))

        conn.commit()
        return jsonify({"message": "Transfer başlatıldı. Ürünler yola çıktı."}), 200

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
