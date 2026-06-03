-- ============================================================
-- Day 42: Views, Functions, Procedures, Triggers, and Events
-- ============================================================
-- This script demonstrates MySQL database objects including:
--   1. CREATE VIEW - virtual tables for data abstraction
--   2. Stored Functions - reusable logic returning a value
--   3. Stored Procedures - multi-step operations with transactions
--   4. Triggers - automatic actions on INSERT/UPDATE/DELETE
--   5. Events - scheduled tasks (like cron jobs in the DB)
-- ============================================================

-- ------------------------------------------------------------
-- Setup: Create and use the sample database
-- ------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS `enterprise_db`
    DEFAULT CHARSET utf8mb4;

USE `enterprise_db`;

-- ------------------------------------------------------------
-- Table: Customers
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `order_audit_log`;
DROP TABLE IF EXISTS `order_items`;
DROP TABLE IF EXISTS `orders`;
DROP TABLE IF EXISTS `products`;
DROP TABLE IF EXISTS `customers`;

CREATE TABLE `customers` (
    `customer_id`   INT AUTO_INCREMENT PRIMARY KEY,
    `customer_name` VARCHAR(100) NOT NULL COMMENT 'Customer name',
    `email`         VARCHAR(150) NOT NULL COMMENT 'Email address',
    `phone`         VARCHAR(20)  DEFAULT NULL COMMENT 'Phone number',
    `city`          VARCHAR(50)  DEFAULT NULL COMMENT 'City',
    `created_at`    DATETIME     DEFAULT CURRENT_TIMESTAMP
) COMMENT 'Customer master table';

-- ------------------------------------------------------------
-- Table: Products
-- ------------------------------------------------------------
CREATE TABLE `products` (
    `product_id`    INT AUTO_INCREMENT PRIMARY KEY,
    `product_name`  VARCHAR(200)   NOT NULL COMMENT 'Product name',
    `category`      VARCHAR(50)    NOT NULL COMMENT 'Product category',
    `unit_price`    DECIMAL(10,2)  NOT NULL COMMENT 'Unit price',
    `stock_qty`     INT            NOT NULL DEFAULT 0 COMMENT 'Available stock',
    `is_active`     TINYINT(1)     NOT NULL DEFAULT 1 COMMENT 'Active flag'
) COMMENT 'Product catalog';

-- ------------------------------------------------------------
-- Table: Orders
-- ------------------------------------------------------------
CREATE TABLE `orders` (
    `order_id`      INT AUTO_INCREMENT PRIMARY KEY,
    `customer_id`   INT            NOT NULL,
    `order_date`    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `status`        VARCHAR(20)    NOT NULL DEFAULT 'pending'
                        COMMENT 'pending/confirmed/shipped/cancelled',
    `total_amount`  DECIMAL(12,2)  NOT NULL DEFAULT 0.00,
    FOREIGN KEY (`customer_id`) REFERENCES `customers`(`customer_id`)
) COMMENT 'Sales orders header';

-- ------------------------------------------------------------
-- Table: Order Items (line items)
-- ------------------------------------------------------------
CREATE TABLE `order_items` (
    `item_id`       INT AUTO_INCREMENT PRIMARY KEY,
    `order_id`      INT            NOT NULL,
    `product_id`    INT            NOT NULL,
    `quantity`      INT            NOT NULL,
    `unit_price`    DECIMAL(10,2)  NOT NULL,
    `line_total`    DECIMAL(12,2)  NOT NULL,
    FOREIGN KEY (`order_id`)   REFERENCES `orders`(`order_id`),
    FOREIGN KEY (`product_id`) REFERENCES `products`(`product_id`)
) COMMENT 'Sales order line items';

-- ------------------------------------------------------------
-- Table: Order Audit Log (used by triggers)
-- ------------------------------------------------------------
CREATE TABLE `order_audit_log` (
    `audit_id`      INT AUTO_INCREMENT PRIMARY KEY,
    `order_id`      INT          NOT NULL,
    `action_type`   VARCHAR(10)  NOT NULL COMMENT 'INSERT/UPDATE/DELETE',
    `old_status`    VARCHAR(20)  DEFAULT NULL,
    `new_status`    VARCHAR(20)  DEFAULT NULL,
    `changed_by`    VARCHAR(100) DEFAULT NULL,
    `changed_at`    DATETIME     DEFAULT CURRENT_TIMESTAMP
) COMMENT 'Audit trail for order changes';

-- ------------------------------------------------------------
-- Sample Data
-- ------------------------------------------------------------
INSERT INTO `customers` (`customer_name`, `email`, `phone`, `city`) VALUES
    ('Alice Johnson',   'alice@example.com',   '555-0101', 'New York'),
    ('Bob Smith',       'bob@example.com',     '555-0102', 'Chicago'),
    ('Charlie Davis',   'charlie@example.com', '555-0103', 'Houston'),
    ('Diana Martinez',  'diana@example.com',   '555-0104', 'Phoenix'),
    ('Edward Wilson',   'edward@example.com',  '555-0105', 'Seattle');

INSERT INTO `products` (`product_name`, `category`, `unit_price`, `stock_qty`) VALUES
    ('Wireless Mouse',       'Electronics', 29.99,  150),
    ('Mechanical Keyboard',  'Electronics', 89.99,  75),
    ('USB-C Hub',            'Electronics', 49.99,  200),
    ('Monitor Stand',        'Accessories', 39.99,  100),
    ('Laptop Bag',           'Accessories', 59.99,  120),
    ('Webcam HD',            'Electronics', 69.99,  50),
    ('Desk Lamp',            'Office',      24.99,  300),
    ('Ergonomic Chair',      'Office',      299.99, 30);

INSERT INTO `orders` (`customer_id`, `order_date`, `status`, `total_amount`) VALUES
    (1, '2025-01-15 10:30:00', 'confirmed', 119.98),
    (2, '2025-01-16 14:00:00', 'shipped',    89.99),
    (3, '2025-01-17 09:15:00', 'pending',    49.99),
    (1, '2025-01-20 11:00:00', 'confirmed', 369.98),
    (4, '2025-01-21 16:45:00', 'cancelled',  59.99),
    (5, '2025-02-01 08:00:00', 'shipped',   324.98);

INSERT INTO `order_items` (`order_id`, `product_id`, `quantity`, `unit_price`, `line_total`) VALUES
    (1, 1, 2, 29.99,  59.98),
    (1, 3, 1, 49.99,  49.99),
    (2, 2, 1, 89.99,  89.99),
    (3, 3, 1, 49.99,  49.99),
    (4, 8, 1, 299.99, 299.99),
    (4, 5, 1, 59.99,  59.99),
    (5, 5, 1, 59.99,  59.99),
    (6, 2, 1, 89.99,  89.99),
    (6, 8, 1, 299.99, 299.99);


-- ============================================================
-- PART 1: VIEWS
-- ============================================================
-- A view is a virtual table defined by a SELECT query.
-- Benefits:
--   - Security: hide sensitive columns from users
--   - Simplicity: encapsulate complex joins/aggregations
--   - Consistency: single definition reused everywhere
-- ============================================================

-- ------------------------------------------------------------
-- View 1: vw_sales_summary
-- Enterprise use: Sales dashboard / reporting
-- Aggregates order data by customer for quick insights.
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW `vw_sales_summary` AS
SELECT
    c.customer_id,
    c.customer_name,
    c.city,
    COUNT(DISTINCT o.order_id)       AS total_orders,
    SUM(o.total_amount)              AS lifetime_revenue,
    ROUND(AVG(o.total_amount), 2)    AS avg_order_value,
    MIN(o.order_date)                AS first_order_date,
    MAX(o.order_date)                AS last_order_date
FROM `customers` c
LEFT JOIN `orders` o
    ON c.customer_id = o.customer_id
    AND o.status <> 'cancelled'
GROUP BY c.customer_id, c.customer_name, c.city;

-- Usage: SELECT * FROM vw_sales_summary;

-- ------------------------------------------------------------
-- View 2: vw_product_performance
-- Enterprise use: Inventory / product performance report
-- Shows how well each product is selling vs. available stock.
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW `vw_product_performance` AS
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.unit_price,
    p.stock_qty,
    COALESCE(SUM(oi.quantity), 0)     AS total_units_sold,
    COALESCE(SUM(oi.line_total), 0)   AS total_revenue,
    p.stock_qty - COALESCE(SUM(oi.quantity), 0) AS remaining_stock
FROM `products` p
LEFT JOIN `order_items` oi
    ON p.product_id = oi.product_id
LEFT JOIN `orders` o
    ON oi.order_id = o.order_id
    AND o.status NOT IN ('cancelled')
GROUP BY p.product_id, p.product_name, p.category,
         p.unit_price, p.stock_qty;

-- Usage: SELECT * FROM vw_product_performance WHERE category = 'Electronics';

-- ------------------------------------------------------------
-- View 3: vw_order_details
-- Enterprise use: Order detail view for support staff.
-- Joins orders with items, products, and customer info.
-- Hides internal IDs and exposes only what support needs.
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW `vw_order_details` AS
SELECT
    o.order_id,
    o.order_date,
    o.status           AS order_status,
    c.customer_name,
    c.email,
    p.product_name,
    oi.quantity,
    oi.unit_price,
    oi.line_total,
    o.total_amount     AS order_total
FROM `orders` o
JOIN `customers` c   ON o.customer_id = c.customer_id
JOIN `order_items` oi ON o.order_id = oi.order_id
JOIN `products` p     ON oi.product_id = p.product_id;

-- Usage: SELECT * FROM vw_order_details WHERE order_id = 1;


-- ============================================================
-- PART 2: STORED FUNCTIONS
-- ============================================================
-- A stored function encapsulates logic and returns a single
-- value. Functions can be used inside SELECT statements,
-- WHERE clauses, and other expressions.
-- ============================================================

-- ------------------------------------------------------------
-- Function 1: fn_calculate_discount
-- Enterprise use: Tiered pricing / loyalty discount
-- Returns a discount percentage based on total spend.
--   - Spend >= 1000 => 15%
--   - Spend >=  500 => 10%
--   - Spend >=  200 =>  5%
--   - Otherwise     =>  0%
-- ------------------------------------------------------------
DELIMITER $$

CREATE FUNCTION fn_calculate_discount(
    p_customer_id INT
)
RETURNS DECIMAL(5,2)
READS SQL DATA
BEGIN
    DECLARE v_total_spend DECIMAL(12,2);
    DECLARE v_discount    DECIMAL(5,2);

    -- Calculate lifetime spend (excluding cancelled orders)
    SELECT IFNULL(SUM(o.total_amount), 0)
      INTO v_total_spend
      FROM `orders` o
     WHERE o.customer_id = p_customer_id
       AND o.status <> 'cancelled';

    -- Determine discount tier
    IF v_total_spend >= 1000 THEN
        SET v_discount = 15.00;
    ELSEIF v_total_spend >= 500 THEN
        SET v_discount = 10.00;
    ELSEIF v_total_spend >= 200 THEN
        SET v_discount = 5.00;
    ELSE
        SET v_discount = 0.00;
    END IF;

    RETURN v_discount;
END $$

DELIMITER ;

-- Usage:
-- SELECT customer_name, fn_calculate_discount(customer_id) AS discount_pct
--   FROM customers;

-- ------------------------------------------------------------
-- Function 2: fn_product_profit_margin
-- Enterprise use: Margin analysis
-- Calculates a simplified profit margin assuming a known
-- cost ratio (for demo, cost = 60% of unit_price).
-- ------------------------------------------------------------
DELIMITER $$

CREATE FUNCTION fn_product_profit_margin(
    p_product_id INT,
    p_cost_ratio DECIMAL(3,2)   -- e.g. 0.60 means cost is 60% of price
)
RETURNS DECIMAL(5,2)
READS SQL DATA
BEGIN
    DECLARE v_price DECIMAL(10,2);
    DECLARE v_cost  DECIMAL(10,2);
    DECLARE v_margin DECIMAL(5,2);

    SELECT unit_price
      INTO v_price
      FROM `products`
     WHERE product_id = p_product_id;

    IF v_price IS NULL OR v_price = 0 THEN
        RETURN 0.00;
    END IF;

    SET v_cost   = v_price * p_cost_ratio;
    SET v_margin = ((v_price - v_cost) / v_price) * 100;

    RETURN ROUND(v_margin, 2);
END $$

DELIMITER ;

-- Usage:
-- SELECT product_name,
--        unit_price,
--        fn_product_profit_margin(product_id, 0.60) AS margin_pct
--   FROM products;

-- ------------------------------------------------------------
-- Function 3: fn_format_currency
-- Enterprise use: Display formatting in reports
-- Returns a formatted currency string, e.g. "$1,234.56"
-- ------------------------------------------------------------
DELIMITER $$

CREATE FUNCTION fn_format_currency(
    p_amount DECIMAL(12,2)
)
RETURNS VARCHAR(20)
NO SQL
BEGIN
    RETURN CONCAT('$', FORMAT(p_amount, 2));
END $$

DELIMITER ;

-- Usage:
-- SELECT fn_format_currency(1234.5) AS formatted;  -- "$1,234.50"


-- ============================================================
-- PART 3: STORED PROCEDURES
-- ============================================================
-- A stored procedure is a precompiled collection of SQL
-- statements. Procedures can use transactions, control flow,
-- cursors, and error handling.
-- ============================================================

-- ------------------------------------------------------------
-- Procedure 1: sp_place_order
-- Enterprise use: Order placement workflow
-- Steps:
--   1. Validate stock availability
--   2. Create the order header
--   3. Insert order items and calculate line totals
--   4. Deduct stock
--   5. Update the order total
--   6. Commit or rollback on error
-- ------------------------------------------------------------
DELIMITER $$

CREATE PROCEDURE sp_place_order(
    IN  p_customer_id INT,
    IN  p_product_id  INT,
    IN  p_quantity     INT,
    OUT p_order_id     INT,
    OUT p_result_msg   VARCHAR(200)
)
BEGIN
    DECLARE v_stock       INT;
    DECLARE v_unit_price  DECIMAL(10,2);
    DECLARE v_line_total  DECIMAL(12,2);
    DECLARE v_error_flag  BOOLEAN DEFAULT FALSE;

    -- Rollback if any SQL exception occurs
    DECLARE CONTINUE HANDLER FOR SQLEXCEPTION
        SET v_error_flag = TRUE;

    -- Validate stock
    SELECT stock_qty, unit_price
      INTO v_stock, v_unit_price
      FROM `products`
     WHERE product_id = p_product_id
       AND is_active = 1
     FOR UPDATE;  -- lock the row to prevent overselling

    IF v_stock IS NULL THEN
        SET p_result_msg = 'Product not found or inactive.';
        SET p_order_id   = NULL;
        -- No transaction started, so just return
    ELSEIF v_stock < p_quantity THEN
        SET p_result_msg = CONCAT('Insufficient stock. Available: ', v_stock);
        SET p_order_id   = NULL;
    ELSE
        START TRANSACTION;

        -- Create order header
        INSERT INTO `orders` (`customer_id`, `status`, `total_amount`)
        VALUES (p_customer_id, 'pending', 0.00);

        SET p_order_id = LAST_INSERT_ID();

        -- Calculate line total
        SET v_line_total = v_unit_price * p_quantity;

        -- Insert order item
        INSERT INTO `order_items`
            (`order_id`, `product_id`, `quantity`, `unit_price`, `line_total`)
        VALUES
            (p_order_id, p_product_id, p_quantity, v_unit_price, v_line_total);

        -- Deduct stock
        UPDATE `products`
           SET stock_qty = stock_qty - p_quantity
         WHERE product_id = p_product_id;

        -- Update order total
        UPDATE `orders`
           SET total_amount = v_line_total
         WHERE order_id = p_order_id;

        -- Commit or rollback
        IF v_error_flag THEN
            ROLLBACK;
            SET p_result_msg = 'Order failed due to a system error. Rolled back.';
            SET p_order_id   = NULL;
        ELSE
            COMMIT;
            SET p_result_msg = CONCAT('Order #', p_order_id, ' placed successfully.');
        END IF;
    END IF;
END $$

DELIMITER ;

-- Usage:
-- CALL sp_place_order(1, 2, 3, @oid, @msg);
-- SELECT @oid AS order_id, @msg AS result_message;

-- ------------------------------------------------------------
-- Procedure 2: sp_update_order_status
-- Enterprise use: Order lifecycle management
-- Updates the status of an existing order with validation.
-- ------------------------------------------------------------
DELIMITER $$

CREATE PROCEDURE sp_update_order_status(
    IN p_order_id   INT,
    IN p_new_status VARCHAR(20)
)
BEGIN
    DECLARE v_current_status VARCHAR(20);

    -- Fetch current status
    SELECT status
      INTO v_current_status
      FROM `orders`
     WHERE order_id = p_order_id;

    IF v_current_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Order not found.';
    END IF;

    -- Validate status transition
    IF v_current_status = 'cancelled' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot update a cancelled order.';
    END IF;

    IF v_current_status = 'shipped' AND p_new_status = 'pending' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot revert a shipped order to pending.';
    END IF;

    -- Perform update (the AFTER UPDATE trigger fires automatically)
    UPDATE `orders`
       SET status = p_new_status
     WHERE order_id = p_order_id;
END $$

DELIMITER ;

-- Usage:
-- CALL sp_update_order_status(1, 'shipped');

-- ------------------------------------------------------------
-- Procedure 3: sp_monthly_sales_report
-- Enterprise use: Generate a summary for a given month
-- Returns a result set of sales by category.
-- ------------------------------------------------------------
DELIMITER $$

CREATE PROCEDURE sp_monthly_sales_report(
    IN p_year  INT,
    IN p_month INT
)
BEGIN
    SELECT
        p.category,
        COUNT(DISTINCT o.order_id)   AS num_orders,
        SUM(oi.quantity)             AS units_sold,
        fn_format_currency(SUM(oi.line_total)) AS revenue
    FROM `orders` o
    JOIN `order_items` oi ON o.order_id = oi.order_id
    JOIN `products` p     ON oi.product_id = p.product_id
    WHERE YEAR(o.order_date)  = p_year
      AND MONTH(o.order_date) = p_month
      AND o.status <> 'cancelled'
    GROUP BY p.category
    ORDER BY SUM(oi.line_total) DESC;
END $$

DELIMITER ;

-- Usage:
-- CALL sp_monthly_sales_report(2025, 1);


-- ============================================================
-- PART 4: TRIGGERS
-- ============================================================
-- A trigger automatically fires in response to INSERT, UPDATE,
-- or DELETE events on a table. Triggers are useful for:
--   - Audit logging
--   - Data validation
--   - Maintaining derived data
-- ============================================================

-- ------------------------------------------------------------
-- Trigger 1: trg_orders_after_insert
-- Enterprise use: Audit trail
-- Logs every new order into the audit table.
-- ------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER trg_orders_after_insert
AFTER INSERT ON `orders`
FOR EACH ROW
BEGIN
    INSERT INTO `order_audit_log`
        (`order_id`, `action_type`, `old_status`, `new_status`, `changed_by`)
    VALUES
        (NEW.order_id, 'INSERT', NULL, NEW.status, CURRENT_USER());
END $$

DELIMITER ;

-- ------------------------------------------------------------
-- Trigger 2: trg_orders_after_update
-- Enterprise use: Audit trail
-- Logs status changes on orders.
-- ------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER trg_orders_after_update
AFTER UPDATE ON `orders`
FOR EACH ROW
BEGIN
    -- Only log if the status actually changed
    IF OLD.status <> NEW.status THEN
        INSERT INTO `order_audit_log`
            (`order_id`, `action_type`, `old_status`, `new_status`, `changed_by`)
        VALUES
            (NEW.order_id, 'UPDATE', OLD.status, NEW.status, CURRENT_USER());
    END IF;
END $$

DELIMITER ;

-- ------------------------------------------------------------
-- Trigger 3: trg_order_items_before_insert
-- Enterprise use: Data validation
-- Automatically calculates line_total before inserting an
-- order item, ensuring consistency.
-- ------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER trg_order_items_before_insert
BEFORE INSERT ON `order_items`
FOR EACH ROW
BEGIN
    -- Auto-calculate line_total from quantity * unit_price
    SET NEW.line_total = NEW.quantity * NEW.unit_price;
END $$

DELIMITER ;

-- ------------------------------------------------------------
-- Trigger 4: trg_order_items_after_insert
-- Enterprise use: Derived data maintenance
-- Updates the parent order's total_amount after a new
-- line item is added.
-- ------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER trg_order_items_after_insert
AFTER INSERT ON `order_items`
FOR EACH ROW
BEGIN
    UPDATE `orders`
       SET total_amount = (
           SELECT IFNULL(SUM(line_total), 0)
             FROM `order_items`
            WHERE order_id = NEW.order_id
       )
     WHERE order_id = NEW.order_id;
END $$

DELIMITER ;


-- ============================================================
-- PART 5: EVENTS (Scheduled Tasks)
-- ============================================================
-- Events are MySQL's built-in scheduler, similar to cron jobs.
-- They execute SQL statements on a defined schedule.
-- REQUIREMENT: The event scheduler must be enabled.
-- ============================================================

-- Enable the event scheduler (requires SUPER privilege)
-- SET GLOBAL event_scheduler = ON;

-- ------------------------------------------------------------
-- Event 1: evt_expire_old_pending_orders
-- Enterprise use: Auto-cancel stale orders
-- Runs daily at 2:00 AM; cancels orders that have been in
-- 'pending' status for more than 7 days.
-- ------------------------------------------------------------
DELIMITER $$

CREATE EVENT IF NOT EXISTS evt_expire_old_pending_orders
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_DATE + INTERVAL 1 DAY + INTERVAL 2 HOUR
COMMENT 'Auto-cancel pending orders older than 7 days'
DO
BEGIN
    UPDATE `orders`
       SET status = 'cancelled'
     WHERE status = 'pending'
       AND order_date < NOW() - INTERVAL 7 DAY;
END $$

DELIMITER ;

-- ------------------------------------------------------------
-- Event 2: evt_cleanup_old_audit_logs
-- Enterprise use: Housekeeping / compliance retention
-- Runs on the 1st of every month at 3:00 AM; deletes audit
-- log entries older than 90 days.
-- ------------------------------------------------------------
DELIMITER $$

CREATE EVENT IF NOT EXISTS evt_cleanup_old_audit_logs
ON SCHEDULE EVERY 1 MONTH
STARTS CURRENT_DATE + INTERVAL 1 DAY + INTERVAL 3 HOUR
COMMENT 'Delete audit logs older than 90 days'
DO
BEGIN
    DELETE FROM `order_audit_log`
     WHERE changed_at < NOW() - INTERVAL 90 DAY;
END $$

DELIMITER ;

-- ------------------------------------------------------------
-- Event 3: evt_reorder_low_stock
-- Enterprise use: Inventory replenishment alert
-- Runs every Monday at 6:00 AM; flags products with stock
-- below 20 units by setting is_active = 0.
-- ------------------------------------------------------------
DELIMITER $$

CREATE EVENT IF NOT EXISTS evt_reorder_low_stock
ON SCHEDULE EVERY 1 WEEK
STARTS CURRENT_DATE + INTERVAL 1 DAY + INTERVAL 6 HOUR
COMMENT 'Deactivate products with critically low stock'
DO
BEGIN
    UPDATE `products`
       SET is_active = 0
     WHERE stock_qty < 20
       AND is_active = 1;
END $$

DELIMITER ;


-- ============================================================
-- PART 6: DEMONSTRATION QUERIES
-- ============================================================

-- ------------------------------------------------------------
-- Query the sales summary view
-- ------------------------------------------------------------
SELECT * FROM `vw_sales_summary` ORDER BY lifetime_revenue DESC;

-- ------------------------------------------------------------
-- Query the product performance view
-- ------------------------------------------------------------
SELECT * FROM `vw_product_performance` ORDER BY total_revenue DESC;

-- ------------------------------------------------------------
-- Use the discount function in a query
-- ------------------------------------------------------------
SELECT
    c.customer_name,
    fn_calculate_discount(c.customer_id) AS discount_pct
FROM `customers` c
ORDER BY discount_pct DESC;

-- ------------------------------------------------------------
-- Use the profit margin function
-- ------------------------------------------------------------
SELECT
    product_name,
    fn_format_currency(unit_price) AS price,
    fn_product_profit_margin(product_id, 0.60) AS margin_pct
FROM `products`;

-- ------------------------------------------------------------
-- Place a new order via the stored procedure
-- ------------------------------------------------------------
CALL sp_place_order(2, 4, 2, @new_order_id, @result_message);
SELECT @new_order_id AS order_id, @result_message AS result;

-- ------------------------------------------------------------
-- Update an order's status (triggers fire automatically)
-- ------------------------------------------------------------
CALL sp_update_order_status(1, 'shipped');

-- ------------------------------------------------------------
-- View the audit log (populated by triggers)
-- ------------------------------------------------------------
SELECT * FROM `order_audit_log` ORDER BY `changed_at` DESC;

-- ------------------------------------------------------------
-- Generate a monthly report
-- ------------------------------------------------------------
CALL sp_monthly_sales_report(2025, 1);


-- ============================================================
-- CLEANUP (uncomment to drop all objects)
-- ============================================================
-- DROP EVENT IF EXISTS evt_expire_old_pending_orders;
-- DROP EVENT IF EXISTS evt_cleanup_old_audit_logs;
-- DROP EVENT IF EXISTS evt_reorder_low_stock;
-- DROP TRIGGER IF EXISTS trg_orders_after_insert;
-- DROP TRIGGER IF EXISTS trg_orders_after_update;
-- DROP TRIGGER IF EXISTS trg_order_items_before_insert;
-- DROP TRIGGER IF EXISTS trg_order_items_after_insert;
-- DROP PROCEDURE IF EXISTS sp_place_order;
-- DROP PROCEDURE IF EXISTS sp_update_order_status;
-- DROP PROCEDURE IF EXISTS sp_monthly_sales_report;
-- DROP FUNCTION IF EXISTS fn_calculate_discount;
-- DROP FUNCTION IF EXISTS fn_product_profit_margin;
-- DROP FUNCTION IF EXISTS fn_format_currency;
-- DROP VIEW IF EXISTS vw_sales_summary;
-- DROP VIEW IF EXISTS vw_product_performance;
-- DROP VIEW IF EXISTS vw_order_details;
-- DROP TABLE IF EXISTS order_audit_log;
-- DROP TABLE IF EXISTS order_items;
-- DROP TABLE IF EXISTS orders;
-- DROP TABLE IF EXISTS products;
-- DROP TABLE IF EXISTS customers;
-- DROP DATABASE IF EXISTS enterprise_db;
