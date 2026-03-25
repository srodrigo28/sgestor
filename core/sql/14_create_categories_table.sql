-- Migration: 14_create_categories_table.sql
-- Description: Extract categories to a separate table and link products to it.

-- 1. Create categories table
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_category (user_id, name),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 2. Populate categories from existing products
INSERT IGNORE INTO categories (user_id, name)
SELECT DISTINCT user_id, category
FROM products
WHERE category IS NOT NULL AND category != '';

-- 3. Add category_id to products
ALTER TABLE products ADD COLUMN IF NOT EXISTS category_id INT;
ALTER TABLE products ADD CONSTRAINT fk_product_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL;

-- 4. Link existing products to new categories
UPDATE products p
JOIN categories c ON p.user_id = c.user_id AND p.category = c.name
SET p.category_id = c.id
WHERE p.category_id IS NULL;

-- 5. (Optional) Rename old column to avoid confusion, or keep for backup.
-- ALTER TABLE products CHANGE COLUMN category category_legacy VARCHAR(100);
