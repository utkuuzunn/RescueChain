DROP DATABASE IF EXISTS rescuechain_db;
CREATE DATABASE rescuechain_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE rescuechain_db;

-- 1. KULLANICILAR (Sadece Admin ve Staff kaldı)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(100),
    role ENUM('admin', 'staff') NOT NULL,
    warehouse_id INT NULL, -- Admin ise NULL, Staff ise sorumlu olduğu depo ID'si
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. DEPOLAR (Harita için Koordinatlar Kritik)
CREATE TABLE warehouses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    city VARCHAR(50),
    latitude DECIMAL(10, 8), -- Harita Enlem
    longitude DECIMAL(11, 8), -- Harita Boylam
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. ENVANTER
CREATE TABLE inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    warehouse_id INT NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    quantity INT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE CASCADE,
    UNIQUE KEY unique_item_per_warehouse (warehouse_id, item_name)
);

-- 4. İŞLEM GEÇMİŞİ (Admin burayı izleyecek)
CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type ENUM('STOCK_IN', 'TRANSFER') NOT NULL, -- Stok Girişi mi, Transfer mi?
    source_warehouse_id INT, -- Nereden (Stok girişiyse NULL olabilir veya kendisi)
    target_warehouse_id INT, -- Nereye
    item_name VARCHAR(100),
    quantity INT,
    performed_by INT, -- İşlemi yapan personel ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (performed_by) REFERENCES users(id)
);

-- --- DEMO VERİLERİ ---

-- Depolar (İstanbul, Ankara, İzmir, Van)
INSERT INTO warehouses (name, city, latitude, longitude) VALUES 
('Marmara Ana Lojistik', 'Istanbul', 41.0082, 28.9784),
('İç Anadolu Bölge Depo', 'Ankara', 39.9334, 32.8597),
('Ege Dağıtım Merkezi', 'Izmir', 38.4237, 27.1428),
('Doğu Anadolu Yardım Üssü', 'Van', 38.5012, 43.3729);

-- Kullanıcılar
-- Admin: Tüm sistemi görür
-- Staff: Sadece kendi deposunu görür
INSERT INTO users (username, full_name, role, warehouse_id) VALUES 
('admin', 'Genel Komutan', 'admin', NULL),
('staff_ist', 'Mehmet (İst Sorumlusu)', 'staff', 1),
('staff_ank', 'Ayşe (Ank Sorumlusu)', 'staff', 2),
('staff_van', 'Ali (Van Sorumlusu)', 'staff', 4);

-- Başlangıç Stokları
INSERT INTO inventory (warehouse_id, item_name, quantity) VALUES 
(1, 'Su (Koli)', 1000), (1, 'Çadır', 200),
(2, 'Battaniye', 500),
(4, 'Jeneratör', 20);

-- Örnek Geçmiş İşlemler (Admin paneli boş durmasın)
INSERT INTO transactions (type, source_warehouse_id, target_warehouse_id, item_name, quantity, performed_by) VALUES
('STOCK_IN', 1, 1, 'Su (Koli)', 1000, 2),
('TRANSFER', 1, 4, 'Çadır', 50, 2);
