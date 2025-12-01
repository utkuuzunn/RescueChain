# nano app.py
from flask import Flask, jsonify, request
from db import get_db_connection
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({"message": "RescueChain API 2.0 (Admin/Staff) Calisiyor! 🚀"})

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

# 3. Admin: Tüm İşlem Geçmişi
@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # İşlemleri, kimin yaptığını ve depo isimlerini birleştirerek getir
    sql = """
    SELECT t.*, u.full_name as user_name,
           w_source.name as source_name, w_target.name as target_name
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
