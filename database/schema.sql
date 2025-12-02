-- VERİTABANINI SIFIRLA VE KUR
DROP DATABASE IF EXISTS rescuechain_db;
CREATE DATABASE rescuechain_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE rescuechain_db;

-- 1. DEPOLAR
CREATE TABLE warehouses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    city VARCHAR(50),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. KULLANICILAR
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) DEFAULT '1234',
    full_name VARCHAR(100),
    role ENUM('admin', 'staff') NOT NULL,
    warehouse_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE SET NULL
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

-- 4. İŞLEM GEÇMİŞİ (LOGLAR)
CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type ENUM('STOCK_IN', 'TRANSFER') NOT NULL,
    source_warehouse_id INT, 
    target_warehouse_id INT, 
    item_name VARCHAR(100),
    quantity INT,
    performed_by INT,
    status ENUM('PENDING', 'COMPLETED', 'CANCELLED') DEFAULT 'COMPLETED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (performed_by) REFERENCES users(id),
    FOREIGN KEY (source_warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (target_warehouse_id) REFERENCES warehouses(id)
);

-- --- VERİ GİRİŞLERİ ---

-- A. DEPOLAR (8 Merkez)
INSERT INTO warehouses (name, city, latitude, longitude) VALUES 
('Marmara Ana Lojistik', 'Istanbul', 41.0082, 28.9784),
('İç Anadolu Bölge Depo', 'Ankara', 39.9334, 32.8597),
('Ege Dağıtım Merkezi', 'Izmir', 38.4237, 27.1428),
('Doğu Anadolu Yardım Üssü', 'Van', 38.5012, 43.3729),
('Güney Lojistik Üssü', 'Adana', 37.0000, 35.3213),
('Karadeniz Afet Merkezi', 'Trabzon', 41.0027, 39.7168),
('Güneydoğu Destek Deposu', 'Diyarbakir', 37.9144, 40.2306),
('Akdeniz Tahliye & Lojistik', 'Antalya', 36.8969, 30.7133);

-- B. KULLANICILAR (Kullanıcı adları şehir ismiyle, Ünvanlar tam haliyle)
INSERT INTO users (username, password, full_name, role, warehouse_id) VALUES 
('admin', '1234', 'Genel Komutan (AFAD)', 'admin', NULL),
('staff_istanbul', '1234', 'Mehmet (İstanbul Sorumlusu)', 'staff', 1),
('staff_ankara', '1234', 'Ayşe (Ankara Sorumlusu)', 'staff', 2),
('staff_izmir', '1234', 'Can (İzmir Sorumlusu)', 'staff', 3),
('staff_van', '1234', 'Ali (Van Sorumlusu)', 'staff', 4),
('staff_adana', '1234', 'Zeynep (Adana Sorumlusu)', 'staff', 5),
('staff_trabzon', '1234', 'Hakan (Trabzon Sorumlusu)', 'staff', 6),
('staff_diyarbakir', '1234', 'Baran (Diyarbakır Sorumlusu)', 'staff', 7),
('staff_antalya', '1234', 'Selin (Antalya Sorumlusu)', 'staff', 8);

-- C. STOKLAR (Senin 10 Ürünlük Listen)
INSERT INTO inventory (warehouse_id, item_name, quantity) VALUES 
-- İstanbul (Ana Depo - Geniş Stok)
(1, 'Su (Koli)', 5000), (1, 'Konserve Gıda (Koli)', 3000), (1, 'Çadır', 500), (1, 'Jeneratör', 50), (1, 'Tıbbi Malzeme (İlaç vb.)', 2000),
-- Ankara (Barınma ve Isınma Odaklı)
(2, 'Isıtıcı', 400), (2, 'Battaniye', 1000), (2, 'Uyku Tulumu', 500),
-- İzmir (Gıda ve İlk Yardım)
(3, 'İlk Yardım Çantası', 1500), (3, 'Su (Koli)', 2000), (3, 'Kıyafet', 800),
-- Van (Kış Şartları)
(4, 'Isıtıcı', 600), (4, 'Battaniye', 1200), (4, 'Uyku Tulumu', 800), (4, 'Jeneratör', 20),
-- Adana (Gıda Lojistiği)
(5, 'Konserve Gıda (Koli)', 2500), (5, 'Su (Koli)', 5000),
-- Trabzon (Giyim ve Barınma)
(6, 'Kıyafet', 1000), (6, 'Battaniye', 400), (6, 'Çadır', 100),
-- Diyarbakır (Medikal ve Barınma)
(7, 'Tıbbi Malzeme (İlaç vb.)', 1000), (7, 'İlk Yardım Çantası', 800), (7, 'Çadır', 300),
-- Antalya (Acil Durum)
(8, 'Su (Koli)', 1000), (8, 'İlk Yardım Çantası', 500), (8, 'Kıyafet', 300);

-- D. GEÇMİŞ İŞLEMLER (Loglar)
INSERT INTO transactions (type, source_warehouse_id, target_warehouse_id, item_name, quantity, performed_by, status, created_at) VALUES
-- 5 Gün Önce
('STOCK_IN', 1, 1, 'Su (Koli)', 5000, 2, 'COMPLETED', NOW() - INTERVAL 5 DAY),
('STOCK_IN', 5, 5, 'Konserve Gıda (Koli)', 2500, 6, 'COMPLETED', NOW() - INTERVAL 5 DAY),

-- 3 Gün Önce
('TRANSFER', 1, 4, 'Battaniye', 200, 2, 'COMPLETED', NOW() - INTERVAL 3 DAY),
('TRANSFER', 1, 6, 'Jeneratör', 5, 2, 'COMPLETED', NOW() - INTERVAL 3 DAY),
('TRANSFER', 3, 5, 'İlk Yardım Çantası', 200, 4, 'COMPLETED', NOW() - INTERVAL 3 DAY),

-- Dün
('STOCK_IN', 7, 7, 'Tıbbi Malzeme (İlaç vb.)', 1000, 8, 'COMPLETED', NOW() - INTERVAL 1 DAY),
('TRANSFER', 2, 4, 'Isıtıcı', 50, 3, 'COMPLETED', NOW() - INTERVAL 1 DAY),
('STOCK_IN', 8, 8, 'Kıyafet', 300, 9, 'COMPLETED', NOW() - INTERVAL 1 DAY),

-- BUGÜN (Yolda Olanlar - Heyecanlı Kısım)
('TRANSFER', 1, 8, 'Çadır', 50, 2, 'PENDING', NOW() - INTERVAL 1 HOUR),
('TRANSFER', 5, 7, 'Konserve Gıda (Koli)', 100, 6, 'PENDING', NOW() - INTERVAL 30 MINUTE),
('TRANSFER', 3, 2, 'Uyku Tulumu', 150, 4, 'PENDING', NOW() - INTERVAL 10 MINUTE);
