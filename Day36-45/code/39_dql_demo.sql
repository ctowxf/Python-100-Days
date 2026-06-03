-- =============================================================================
-- DQL (Data Query Language) Comprehensive Demo
-- Day 39: SQL Query Deep Dive - SELECT, WHERE, JOIN, GROUP BY, HAVING, etc.
-- =============================================================================
-- This script demonstrates all major DQL constructs with enterprise-grade
-- examples. Each section includes C++ STL algorithm comparisons to help
-- programmers from a systems background map SQL concepts to familiar ideas.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 0. Setup: Create sample enterprise tables and seed data
-- ---------------------------------------------------------------------------

DROP DATABASE IF EXISTS enterprise_demo;
CREATE DATABASE enterprise_demo DEFAULT CHARSET=utf8mb4;
USE enterprise_demo;

-- Departments
CREATE TABLE departments (
    dept_id     INT PRIMARY KEY AUTO_INCREMENT,
    dept_name   VARCHAR(50) NOT NULL,
    location    VARCHAR(100)
);

-- Employees
CREATE TABLE employees (
    emp_id      INT PRIMARY KEY AUTO_INCREMENT,
    emp_name    VARCHAR(50) NOT NULL,
    gender      TINYINT DEFAULT 1 COMMENT '1=male, 0=female',
    hire_date   DATE NOT NULL,
    salary      DECIMAL(10,2) NOT NULL,
    dept_id     INT,
    manager_id  INT DEFAULT NULL,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

-- Products
CREATE TABLE products (
    prod_id     INT PRIMARY KEY AUTO_INCREMENT,
    prod_name   VARCHAR(100) NOT NULL,
    category    VARCHAR(50) NOT NULL,
    unit_price  DECIMAL(10,2) NOT NULL,
    stock_qty   INT DEFAULT 0
);

-- Orders
CREATE TABLE orders (
    order_id    INT PRIMARY KEY AUTO_INCREMENT,
    emp_id      INT,
    order_date  DATE NOT NULL,
    customer    VARCHAR(100),
    status      VARCHAR(20) DEFAULT 'completed',
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
);

-- Order items (line items)
CREATE TABLE order_items (
    item_id     INT PRIMARY KEY AUTO_INCREMENT,
    order_id    INT NOT NULL,
    prod_id     INT NOT NULL,
    quantity    INT NOT NULL,
    unit_price  DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (prod_id)   REFERENCES products(prod_id)
);

-- Seed departments
INSERT INTO departments (dept_name, location) VALUES
    ('Sales',       'Beijing'),
    ('Engineering', 'Shanghai'),
    ('Marketing',   'Guangzhou'),
    ('Finance',     'Beijing'),
    ('HR',          'Shanghai');

-- Seed employees
INSERT INTO employees (emp_name, gender, hire_date, salary, dept_id, manager_id) VALUES
    ('Alice Wang',    0, '2018-03-15', 28000.00, 1, NULL),
    ('Bob Li',        1, '2019-07-01', 22000.00, 1, 1),
    ('Charlie Zhang', 1, '2017-01-10', 35000.00, 2, NULL),
    ('Diana Chen',    0, '2020-05-20', 18000.00, 2, 3),
    ('Edward Liu',    1, '2016-11-30', 40000.00, 2, 3),
    ('Fiona Zhao',    0, '2021-02-14', 15000.00, 3, NULL),
    ('George Wu',     1, '2019-09-09', 20000.00, 3, 6),
    ('Helen Xu',      0, '2015-06-01', 45000.00, 4, NULL),
    ('Ivan Yang',     1, '2022-01-10', 12000.00, 4, 8),
    ('Julia Sun',     0, '2018-08-08', 26000.00, 5, NULL),
    ('Kevin Huang',   1, '2023-03-01', 10000.00, 1, 1),
    ('Linda Zhou',    0, '2021-11-11', 16000.00, 2, 3);

-- Seed products
INSERT INTO products (prod_name, category, unit_price, stock_qty) VALUES
    ('Laptop Pro 15',       'Electronics',  8999.00, 120),
    ('Wireless Mouse',      'Electronics',   199.00, 500),
    ('Mechanical Keyboard', 'Electronics',   599.00, 300),
    ('USB-C Hub',           'Electronics',   299.00, 200),
    ('Monitor 27"',         'Electronics',  2499.00, 80),
    ('Office Chair',        'Furniture',    1299.00, 150),
    ('Standing Desk',       'Furniture',    3499.00, 60),
    ('Webcam HD',           'Electronics',   399.00, 250),
    ('Noise-Cancel Headset','Electronics',   999.00, 180),
    ('Desk Lamp',           'Furniture',     249.00, 400);

-- Seed orders
INSERT INTO orders (emp_id, order_date, customer, status) VALUES
    (1,  '2024-01-15', 'Acme Corp',     'completed'),
    (2,  '2024-01-20', 'Beta Inc',      'completed'),
    (1,  '2024-02-05', 'Gamma LLC',     'completed'),
    (3,  '2024-02-10', 'Delta Ltd',     'completed'),
    (2,  '2024-03-01', 'Acme Corp',     'completed'),
    (4,  '2024-03-15', 'Epsilon Co',    'completed'),
    (1,  '2024-04-01', 'Zeta Group',    'completed'),
    (5,  '2024-04-10', 'Beta Inc',      'completed'),
    (2,  '2024-05-01', 'Gamma LLC',     'cancelled'),
    (6,  '2024-05-15', 'Eta Partners',  'completed'),
    (1,  '2024-06-01', 'Acme Corp',     'completed'),
    (3,  '2024-06-15', 'Theta Ltd',     'completed'),
    (7,  '2024-07-01', 'Iota Inc',      'completed'),
    (2,  '2024-07-20', 'Delta Ltd',     'completed'),
    (4,  '2024-08-01', 'Kappa Corp',    'completed');

-- Seed order items
INSERT INTO order_items (order_id, prod_id, quantity, unit_price) VALUES
    (1,  1,  2, 8999.00),   -- 2x Laptop
    (1,  2,  5,  199.00),   -- 5x Mouse
    (2,  3, 10,  599.00),   -- 10x Keyboard
    (2,  5,  3, 2499.00),   -- 3x Monitor
    (3,  1,  1, 8999.00),   -- 1x Laptop
    (3,  9,  2,  999.00),   -- 2x Headset
    (4,  6, 20, 1299.00),   -- 20x Chair
    (4,  7, 10, 3499.00),   -- 10x Desk
    (5,  2, 50,  199.00),   -- 50x Mouse
    (5,  4, 30,  299.00),   -- 30x USB-C Hub
    (6,  8,  5,  399.00),   -- 5x Webcam
    (7,  1,  3, 8999.00),   -- 3x Laptop
    (7,  5,  2, 2499.00),   -- 2x Monitor
    (8, 10, 15,  249.00),   -- 15x Lamp
    (9,  3, 10,  599.00),   -- 10x Keyboard (cancelled)
    (10, 1,  1, 8999.00),   -- 1x Laptop
    (10, 9,  3,  999.00),   -- 3x Headset
    (11, 2,100,  199.00),   -- 100x Mouse
    (11, 3, 20,  599.00),   -- 20x Keyboard
    (11, 4, 50,  299.00),   -- 50x USB-C Hub
    (12, 6, 30, 1299.00),   -- 30x Chair
    (13, 1,  5, 8999.00),   -- 5x Laptop
    (13, 5,  4, 2499.00),   -- 4x Monitor
    (13, 9, 10,  999.00),   -- 10x Headset
    (14, 2, 80,  199.00),   -- 80x Mouse
    (14, 8, 20,  399.00),   -- 20x Webcam
    (15, 7,  5, 3499.00);   -- 5x Desk


-- ===========================================================================
-- 1. SELECT - Projection (choosing columns)
-- ===========================================================================
-- C++ analogy: SELECT is like std::transform -- it maps each row to a
-- new shape, keeping only the fields you care about.
--   std::transform(begin, end, out, [](const Row& r) {
--       return Result{r.name, r.salary};
--   });
-- ===========================================================================

-- Select all columns (equivalent to printing every field of every struct)
SELECT * FROM employees;

-- Project specific columns with aliases
SELECT emp_id   AS employee_id,
       emp_name AS name,
       salary   AS monthly_salary
  FROM employees;

-- Computed columns: calculate annual salary
-- C++ analogy: like applying a lambda in std::transform
--   [](const Row& r) { return Result{r.name, r.salary * 12}; }
SELECT emp_name,
       salary,
       salary * 12 AS annual_salary,
       ROUND(salary * 12 * 0.85, 2) AS after_tax_estimate
  FROM employees;

-- CASE expression: conditional logic in SELECT
-- C++ analogy: like a ternary inside transform
--   r.gender == 1 ? "Male" : "Female"
SELECT emp_name,
       CASE gender WHEN 1 THEN 'Male' ELSE 'Female' END AS gender_text,
       salary
  FROM employees;

-- Using IF() as a shorter alternative to CASE for binary choices
SELECT emp_name,
       IF(gender, 'Male', 'Female') AS gender_text
  FROM employees;


-- ===========================================================================
-- 2. WHERE - Filtering rows
-- ===========================================================================
-- C++ analogy: WHERE is like std::copy_if / std::remove_if -- it selects
-- only the rows that satisfy a predicate.
--   std::copy_if(begin, end, out, [](const Row& r) {
--       return r.salary > 20000;
--   });
-- ===========================================================================

-- Comparison operators: =, <>, <, <=, >, >=
SELECT emp_name, salary
  FROM employees
 WHERE salary >= 25000;

-- Logical operators: AND, OR, NOT
SELECT emp_name, salary, hire_date
  FROM employees
 WHERE salary >= 20000
   AND hire_date <= '2020-01-01';

-- BETWEEN: range filtering (inclusive on both ends)
-- C++ analogy:  r.salary >= 15000 && r.salary <= 30000
SELECT emp_name, salary
  FROM employees
 WHERE salary BETWEEN 15000 AND 30000;

-- IN: membership test (set inclusion)
-- C++ analogy:  std::set<int> ids{1,2,3}; ids.count(r.dept_id)
SELECT emp_name, dept_id
  FROM employees
 WHERE dept_id IN (1, 2);

-- NOT IN: exclusion
SELECT emp_name, dept_id
  FROM employees
 WHERE dept_id NOT IN (4, 5);

-- LIKE: pattern matching with wildcards
--   % matches zero or more characters
--   _ matches exactly one character
SELECT emp_name
  FROM employees
 WHERE emp_name LIKE 'A%';          -- starts with 'A'

SELECT emp_name
  FROM employees
 WHERE emp_name LIKE '%ang';        -- ends with 'ang'

SELECT emp_name
  FROM employees
 WHERE emp_name LIKE '%li%';        -- contains 'li'

-- NULL handling
-- C++ analogy: checking for std::optional::has_value()
-- IS NULL / IS NOT NULL, never use = NULL
SELECT emp_name, manager_id
  FROM employees
 WHERE manager_id IS NULL;          -- top-level employees (no manager)

SELECT emp_name, manager_id
  FROM employees
 WHERE manager_id IS NOT NULL;      -- employees who have a manager

-- Combining conditions: complex predicates
SELECT emp_name, salary, dept_id
  FROM employees
 WHERE (dept_id = 1 OR dept_id = 2)
   AND salary > 15000
   AND hire_date >= '2019-01-01';


-- ===========================================================================
-- 3. JOIN - Combining tables
-- ===========================================================================
-- C++ analogy: JOIN is like a nested loop that pairs elements from two
-- containers based on a predicate.  Inner join is like
--   for (auto& a : tableA)
--       for (auto& b : tableB)
--           if (a.key == b.key)  out.push_back(merge(a, b));
-- ===========================================================================

-- INNER JOIN: only matching rows from both sides
-- C++ analogy: inner_product-like merge on matching keys
SELECT e.emp_name,
       d.dept_name,
       d.location
  FROM employees e
 INNER JOIN departments d ON e.dept_id = d.dept_id;

-- LEFT JOIN: all rows from left, matched rows from right (NULL if no match)
-- C++ analogy: like a left-biased merge; unmatched left elements get a
--              default-constructed right side (i.e., NULLs)
SELECT e.emp_name,
       COALESCE(d.dept_name, 'Unassigned') AS department
  FROM employees e
  LEFT JOIN departments d ON e.dept_id = d.dept_id;

-- RIGHT JOIN: all rows from right, matched rows from left
SELECT e.emp_name,
       d.dept_name
  FROM employees e
 RIGHT JOIN departments d ON e.dept_id = d.dept_id;

-- CROSS JOIN: Cartesian product (every row x every row)
-- C++ analogy: nested for-loop with no filter
--   for (auto& e : employees) for (auto& d : departments) out.push_back(...)
-- Use with caution -- row count = |employees| * |departments|
SELECT e.emp_name, d.dept_name
  FROM employees e
 CROSS JOIN departments d
 LIMIT 10;  -- show only first 10 to avoid flooding output

-- Self JOIN: joining a table to itself
-- Find each employee and their manager's name
SELECT e.emp_name  AS employee,
       m.emp_name  AS manager
  FROM employees e
  LEFT JOIN employees m ON e.manager_id = m.emp_id;

-- Multi-table JOIN: orders -> employees -> departments
-- "Which department generated which orders?"
SELECT d.dept_name,
       o.order_id,
       o.order_date,
       o.customer
  FROM orders o
 INNER JOIN employees e   ON o.emp_id  = e.emp_id
 INNER JOIN departments d ON e.dept_id = d.dept_id
 ORDER BY d.dept_name, o.order_date;

-- Full detail JOIN: order -> order_items -> products -> employees
-- "Complete sales line-item report"
SELECT o.order_id,
       o.order_date,
       e.emp_name       AS salesperson,
       p.prod_name      AS product,
       oi.quantity,
       oi.unit_price,
       oi.quantity * oi.unit_price AS line_total
  FROM orders o
 INNER JOIN employees e   ON o.emp_id  = e.emp_id
 INNER JOIN order_items oi ON o.order_id = oi.order_id
 INNER JOIN products p    ON oi.prod_id = p.prod_id
 WHERE o.status = 'completed'
 ORDER BY o.order_id;


-- ===========================================================================
-- 4. GROUP BY + Aggregate Functions
-- ===========================================================================
-- C++ analogy: GROUP BY is like std::accumulate / std::reduce applied per
-- group.  SQL's SUM, COUNT, AVG, MIN, MAX map directly to fold operations.
--   auto groups = partition(rows, by_key);
--   for (auto& [key, group] : groups)
--       result[key] = { count(group), sum(group, &Row::amount) };
-- ===========================================================================

-- COUNT: number of employees per department
SELECT d.dept_name,
       COUNT(*) AS headcount
  FROM employees e
 INNER JOIN departments d ON e.dept_id = d.dept_id
 GROUP BY d.dept_name;

-- SUM: total salary expense per department
SELECT d.dept_name,
       COUNT(*)        AS headcount,
       SUM(e.salary)   AS total_salary,
       AVG(e.salary)   AS avg_salary
  FROM employees e
 INNER JOIN departments d ON e.dept_id = d.dept_id
 GROUP BY d.dept_name;

-- MIN / MAX: salary range per department
SELECT d.dept_name,
       MIN(e.salary) AS min_salary,
       MAX(e.salary) AS max_salary,
       MAX(e.salary) - MIN(e.salary) AS salary_spread
  FROM employees e
 INNER JOIN departments d ON e.dept_id = d.dept_id
 GROUP BY d.dept_name;

-- GROUP BY with multiple columns
-- "How many male and female employees in each department?"
SELECT d.dept_name,
       IF(e.gender, 'Male', 'Female') AS gender,
       COUNT(*) AS headcount
  FROM employees e
 INNER JOIN departments d ON e.dept_id = d.dept_id
 GROUP BY d.dept_name, e.gender
 ORDER BY d.dept_name, gender;

-- Aggregate on joined data: revenue per salesperson
-- C++ analogy: fold over a filtered, joined dataset
SELECT e.emp_name                                AS salesperson,
       COUNT(DISTINCT o.order_id)                AS num_orders,
       SUM(oi.quantity * oi.unit_price)           AS total_revenue,
       ROUND(AVG(oi.quantity * oi.unit_price), 2) AS avg_order_line_value
  FROM orders o
 INNER JOIN employees e    ON o.emp_id   = e.emp_id
 INNER JOIN order_items oi ON o.order_id = oi.order_id
 WHERE o.status = 'completed'
 GROUP BY e.emp_name
 ORDER BY total_revenue DESC;


-- ===========================================================================
-- 5. HAVING - Filtering after aggregation
-- ===========================================================================
-- C++ analogy: HAVING is like a second pass of std::copy_if applied to the
-- aggregated results -- you cannot use WHERE on aggregates, so HAVING acts
-- as a post-reduce filter.
--   auto groups = group_by(rows, key);
--   auto result = filter(groups, [](auto& g) { return g.sum > 1000; });
-- ===========================================================================

-- Departments with more than 2 employees
SELECT d.dept_name,
       COUNT(*) AS headcount
  FROM employees e
 INNER JOIN departments d ON e.dept_id = d.dept_id
 GROUP BY d.dept_name
HAVING headcount > 2;

-- Salespersons with total revenue over 50,000
SELECT e.emp_name,
       SUM(oi.quantity * oi.unit_price) AS total_revenue
  FROM orders o
 INNER JOIN employees e    ON o.emp_id   = e.emp_id
 INNER JOIN order_items oi ON o.order_id = oi.order_id
 WHERE o.status = 'completed'
 GROUP BY e.emp_name
HAVING total_revenue > 50000
 ORDER BY total_revenue DESC;

-- WHERE vs HAVING: WHERE filters rows BEFORE grouping;
--                  HAVING filters groups AFTER grouping.
-- "Find departments where the average salary exceeds 20000,
--  considering only employees hired after 2018."
SELECT d.dept_name,
       COUNT(*)        AS headcount,
       AVG(e.salary)   AS avg_salary
  FROM employees e
 INNER JOIN departments d ON e.dept_id = d.dept_id
 WHERE e.hire_date >= '2018-01-01'      -- pre-group filter
 GROUP BY d.dept_name
HAVING avg_salary > 20000               -- post-group filter
 ORDER BY avg_salary DESC;


-- ===========================================================================
-- 6. ORDER BY - Sorting results
-- ===========================================================================
-- C++ analogy: ORDER BY is std::sort on the result set.
--   std::sort(rows.begin(), rows.end(), [](auto& a, auto& b) {
--       return a.salary > b.salary;   -- DESC
--   });
-- ===========================================================================

-- Single column sort: employees by salary descending
SELECT emp_name, salary
  FROM employees
 ORDER BY salary DESC;

-- Multi-column sort: department ascending, then salary descending
SELECT emp_name, dept_id, salary
  FROM employees
 ORDER BY dept_id ASC, salary DESC;

-- Sort by expression: employees by annual salary
SELECT emp_name,
       salary * 12 AS annual_salary
  FROM employees
 ORDER BY annual_salary DESC;

-- Sort by column alias defined in SELECT
SELECT d.dept_name,
       COUNT(*) AS headcount
  FROM employees e
 INNER JOIN departments d ON e.dept_id = d.dept_id
 GROUP BY d.dept_name
 ORDER BY headcount DESC;


-- ===========================================================================
-- 7. LIMIT / OFFSET - Pagination
-- ===========================================================================
-- C++ analogy: LIMIT is like taking the first N elements after sort;
-- LIMIT + OFFSET is like std::advance(begin, offset) then taking N.
--   auto start = result.begin() + offset;
--   auto end   = start + limit;
--   return Slice(start, end);
-- ===========================================================================

-- Top 5 highest-paid employees
SELECT emp_name, salary
  FROM employees
 ORDER BY salary DESC
 LIMIT 5;

-- Page 2 (rows 6-10): skip first 5, take next 5
SELECT emp_name, salary
  FROM employees
 ORDER BY salary DESC
 LIMIT 5 OFFSET 5;

-- Alternative syntax: LIMIT count OFFSET skip
-- MySQL also supports: LIMIT skip, count
SELECT emp_name, salary
  FROM employees
 ORDER BY salary DESC
 LIMIT 10, 5;   -- skip 10, take 5 (page 3 if page size = 5)

-- Practical pagination: "top products by revenue, page 1"
SELECT p.prod_name,
       SUM(oi.quantity * oi.unit_price) AS total_revenue
  FROM order_items oi
 INNER JOIN products p ON oi.prod_id = p.prod_id
 GROUP BY p.prod_name
 ORDER BY total_revenue DESC
 LIMIT 5;


-- ===========================================================================
-- 8. Subqueries
-- ===========================================================================
-- C++ analogy: subqueries are like composing algorithms:
--   auto ids    = filter_map(rows, pred, &Row::id);   -- inner query
--   auto result = filter(rows, [&](auto& r) {          -- outer query
--       return ids.count(r.id);
--   });
-- ===========================================================================

-- Scalar subquery: employees earning above the company average
-- C++: auto avg = accumulate(...) / count(...);  then copy_if(... > avg)
SELECT emp_name, salary
  FROM employees
 WHERE salary > (SELECT AVG(salary) FROM employees);

-- Subquery with IN: employees in the top-2 departments by headcount
SELECT emp_name, dept_id
  FROM employees
 WHERE dept_id IN (
       SELECT dept_id
         FROM employees
        GROUP BY dept_id
        ORDER BY COUNT(*) DESC
        LIMIT 2
 );

-- Correlated subquery: employees who earn more than their department average
-- C++: for each employee, recompute the department average -- like a
--      nested accumulate inside copy_if
SELECT e.emp_name,
       e.salary,
       d.dept_name
  FROM employees e
 INNER JOIN departments d ON e.dept_id = d.dept_id
 WHERE e.salary > (
       SELECT AVG(e2.salary)
         FROM employees e2
        WHERE e2.dept_id = e.dept_id
 );

-- Subquery in FROM (derived table): department salary statistics
-- C++: group into a temp structure, then query that structure
SELECT dept_stats.dept_name,
       dept_stats.headcount,
       dept_stats.avg_salary
  FROM (
       SELECT d.dept_name,
              COUNT(*)      AS headcount,
              ROUND(AVG(e.salary), 2) AS avg_salary
         FROM employees e
        INNER JOIN departments d ON e.dept_id = d.dept_id
        GROUP BY d.dept_name
  ) AS dept_stats
 WHERE dept_stats.headcount >= 2;

-- EXISTS subquery: departments that have at least one employee
-- C++: std::any_of -- "does any element satisfy the predicate?"
SELECT d.dept_name
  FROM departments d
 WHERE EXISTS (
       SELECT 1
         FROM employees e
        WHERE e.dept_id = d.dept_id
 );

-- NOT EXISTS: departments with no employees
SELECT d.dept_name
  FROM departments d
 WHERE NOT EXISTS (
       SELECT 1
         FROM employees e
        WHERE e.dept_id = d.dept_id
 );


-- ===========================================================================
-- 9. Enterprise Scenario: Monthly Sales Report
-- ===========================================================================
-- "Generate a monthly revenue report for 2024, showing order count,
--  total revenue, and average order value per month."
--
-- C++ analogy: partition orders by month, then fold each partition.
--   auto by_month = group_by(orders, [](auto& o){ return o.date.month(); });
--   for (auto& [month, group] : by_month)
--       report[month] = { count(group), sum(...), avg(...) };
-- ===========================================================================

SELECT DATE_FORMAT(o.order_date, '%Y-%m')  AS month,
       COUNT(DISTINCT o.order_id)          AS order_count,
       SUM(oi.quantity * oi.unit_price)    AS total_revenue,
       ROUND(SUM(oi.quantity * oi.unit_price) / COUNT(DISTINCT o.order_id), 2)
                                           AS avg_order_value
  FROM orders o
 INNER JOIN order_items oi ON o.order_id = oi.order_id
 WHERE o.status = 'completed'
   AND o.order_date BETWEEN '2024-01-01' AND '2024-12-31'
 GROUP BY DATE_FORMAT(o.order_date, '%Y-%m')
 ORDER BY month;


-- ===========================================================================
-- 10. Enterprise Scenario: User/Employee Analytics
-- ===========================================================================
-- "Profile each salesperson: total orders, first/last order date, total
--  revenue, and a performance tier based on revenue thresholds."
--
-- C++: map-reduce pattern -- map each order to its salesperson, reduce
--      to aggregated stats, then classify with a transform.
-- ===========================================================================

SELECT e.emp_name,
       COUNT(DISTINCT o.order_id)       AS total_orders,
       MIN(o.order_date)                AS first_order,
       MAX(o.order_date)                AS last_order,
       SUM(oi.quantity * oi.unit_price) AS total_revenue,
       CASE
           WHEN SUM(oi.quantity * oi.unit_price) >= 100000 THEN 'Platinum'
           WHEN SUM(oi.quantity * oi.unit_price) >=  50000 THEN 'Gold'
           WHEN SUM(oi.quantity * oi.unit_price) >=  20000 THEN 'Silver'
           ELSE 'Bronze'
       END AS performance_tier
  FROM employees e
  LEFT JOIN orders o      ON e.emp_id   = o.emp_id
                          AND o.status   = 'completed'
  LEFT JOIN order_items oi ON o.order_id = oi.order_id
 GROUP BY e.emp_id, e.emp_name
 ORDER BY total_revenue DESC;


-- ===========================================================================
-- 11. Enterprise Scenario: Product Ranking
-- ===========================================================================
-- "Rank products by total revenue within their category, showing top 3
--  per category."
--
-- C++: partition by category, sort each partition by revenue descending,
--      then take the first 3 from each.
--   for (auto& [cat, prods] : group_by(products, &Product::category)) {
--       std::sort(prods.begin(), prods.end(), by_revenue_desc);
--       result.append(prods.begin(), prods.begin() + min(3, prods.size()));
--   }
-- ===========================================================================

SELECT category,
       prod_name,
       total_revenue,
       revenue_rank
  FROM (
       SELECT p.category,
              p.prod_name,
              SUM(oi.quantity * oi.unit_price) AS total_revenue,
              ROW_NUMBER() OVER (
                  PARTITION BY p.category
                  ORDER BY SUM(oi.quantity * oi.unit_price) DESC
              ) AS revenue_rank
         FROM products p
         LEFT JOIN order_items oi ON p.prod_id = oi.prod_id
        GROUP BY p.category, p.prod_name
  ) ranked
 WHERE revenue_rank <= 3
 ORDER BY category, revenue_rank;


-- ===========================================================================
-- 12. Enterprise Scenario: Revenue Analysis (YoY / cumulative)
-- ===========================================================================
-- "Show cumulative revenue over time in 2024 and each month's contribution
--  as a percentage of the annual total."
--
-- C++: like a partial_sum (running total) combined with a final transform
--      that divides each element by the grand total.
--   auto running = std::partial_sum(monthly.begin(), monthly.end(), ...);
--   auto pct = transform(running, [&](auto& v) { return v / grand_total; });
-- ===========================================================================

SELECT month,
       monthly_revenue,
       SUM(monthly_revenue) OVER (ORDER BY month) AS cumulative_revenue,
       ROUND(
           monthly_revenue * 100.0 / SUM(monthly_revenue) OVER (), 2
       ) AS pct_of_annual
  FROM (
       SELECT DATE_FORMAT(o.order_date, '%Y-%m')  AS month,
              SUM(oi.quantity * oi.unit_price)     AS monthly_revenue
         FROM orders o
        INNER JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.status = 'completed'
          AND YEAR(o.order_date) = 2024
        GROUP BY DATE_FORMAT(o.order_date, '%Y-%m')
  ) monthly
 ORDER BY month;


-- ===========================================================================
-- 13. Enterprise Scenario: Customer Purchase Behavior
-- ===========================================================================
-- "For each customer, show how many orders they placed, their total spend,
--  and average items per order.  Identify VIP customers (spend > 30000)."
--
-- C++: group_by customer, fold each group, then filter by threshold.
-- ===========================================================================

SELECT o.customer,
       COUNT(DISTINCT o.order_id)          AS order_count,
       SUM(oi.quantity)                     AS total_items,
       ROUND(SUM(oi.quantity) * 1.0 / COUNT(DISTINCT o.order_id), 1)
                                            AS avg_items_per_order,
       SUM(oi.quantity * oi.unit_price)     AS total_spend,
       IF(SUM(oi.quantity * oi.unit_price) > 30000, 'VIP', 'Regular')
                                            AS customer_tier
  FROM orders o
 INNER JOIN order_items oi ON o.order_id = oi.order_id
 WHERE o.status = 'completed'
 GROUP BY o.customer
 ORDER BY total_spend DESC;


-- ===========================================================================
-- 14. Enterprise Scenario: Department Performance Dashboard
-- ===========================================================================
-- "Compare departments: headcount, avg salary, total sales revenue,
--  and revenue per employee."
--
-- C++: two separate group_by folds (one on employees, one on sales),
--      then a merge/join on department key.
-- ===========================================================================

SELECT d.dept_name,
       emp_stats.headcount,
       emp_stats.avg_salary,
       COALESCE(sales_stats.total_revenue, 0) AS total_revenue,
       ROUND(COALESCE(sales_stats.total_revenue, 0) / emp_stats.headcount, 2)
                                               AS revenue_per_employee
  FROM departments d
 INNER JOIN (
       SELECT dept_id,
              COUNT(*)            AS headcount,
              ROUND(AVG(salary), 2) AS avg_salary
         FROM employees
        GROUP BY dept_id
 ) emp_stats ON d.dept_id = emp_stats.dept_id
 LEFT JOIN (
       SELECT e.dept_id,
              SUM(oi.quantity * oi.unit_price) AS total_revenue
         FROM orders o
        INNER JOIN employees e    ON o.emp_id   = e.emp_id
        INNER JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.status = 'completed'
        GROUP BY e.dept_id
 ) sales_stats ON d.dept_id = sales_stats.dept_id
 ORDER BY total_revenue DESC;


-- ===========================================================================
-- 15. Set Operations: UNION, INTERSECT emulation, EXCEPT emulation
-- ===========================================================================
-- C++ analogy: UNION is std::set_union (with duplicates removed by default),
-- INTERSECT is std::set_intersection, EXCEPT is std::set_difference.
-- MySQL does not natively support INTERSECT or EXCEPT in older versions,
-- so we emulate them with IN / NOT IN subqueries.
-- ===========================================================================

-- UNION: combine two result sets (removes duplicates by default)
-- "Employees in Sales or Engineering"
SELECT emp_name FROM employees WHERE dept_id = 1
UNION
SELECT emp_name FROM employees WHERE dept_id = 2;

-- UNION ALL: keeps duplicates (like concatenating two vectors)
SELECT emp_name FROM employees WHERE dept_id = 1
UNION ALL
SELECT emp_name FROM employees WHERE dept_id = 2;

-- INTERSECT emulation: "Employees who are in both dept 1 and have salary > 20000"
-- (trivial here, but demonstrates the pattern)
SELECT emp_name FROM employees
 WHERE dept_id = 1
   AND emp_id IN (SELECT emp_id FROM employees WHERE salary > 20000);


-- ===========================================================================
-- 16. Advanced: Window Functions (bonus, extends GROUP BY concept)
-- ===========================================================================
-- C++ analogy: window functions are like a "sliding fold" -- they compute
-- aggregates without collapsing rows, similar to std::partial_sum or a
-- running accumulate that keeps every element.
-- ===========================================================================

-- Rank employees by salary within their department
SELECT e.emp_name,
       d.dept_name,
       e.salary,
       RANK() OVER (PARTITION BY e.dept_id ORDER BY e.salary DESC) AS salary_rank,
       e.salary - LAG(e.salary) OVER (PARTITION BY e.dept_id ORDER BY e.salary DESC)
           AS diff_from_next_highest
  FROM employees e
 INNER JOIN departments d ON e.dept_id = d.dept_id
 ORDER BY d.dept_name, salary_rank;

-- Running total of revenue per salesperson over time
SELECT e.emp_name,
       o.order_date,
       SUM(oi.quantity * oi.unit_price) AS order_revenue,
       SUM(SUM(oi.quantity * oi.unit_price)) OVER (
           PARTITION BY e.emp_id ORDER BY o.order_date
       ) AS running_total
  FROM orders o
 INNER JOIN employees e    ON o.emp_id   = e.emp_id
 INNER JOIN order_items oi ON o.order_id = oi.order_id
 WHERE o.status = 'completed'
 GROUP BY e.emp_id, e.emp_name, o.order_date
 ORDER BY e.emp_name, o.order_date;


-- ===========================================================================
-- Cleanup (comment out to keep the demo data)
-- ===========================================================================
-- DROP DATABASE IF EXISTS enterprise_demo;
