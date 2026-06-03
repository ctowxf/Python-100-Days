-- =====================================================
-- MySQL 8.0+ 新特性演示
-- 包括：窗口函数、CTE、JSON支持、不可见索引
-- 企业级示例：累计求和、排名、同比分析
-- =====================================================

-- 创建演示数据库
CREATE DATABASE IF NOT EXISTS `demo_mysql8`
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_unicode_ci;

USE `demo_mysql8`;

-- =====================================================
-- 一、JSON 类型支持
-- =====================================================

-- 1.1 创建包含JSON列的表
-- JSON类型从MySQL 5.7开始支持，8.0解决了日志性能瓶颈问题
-- 打破了关系型数据库和非关系型数据库的界限

CREATE TABLE `tb_users` (
    `user_id`    BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `username`   VARCHAR(50) NOT NULL,
    -- 使用JSON类型存储多种登录方式，灵活应对业务变化
    `login_info` JSON,
    -- 使用JSON类型存储用户画像标签
    `user_tags`  JSON,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 1.2 插入JSON数据
INSERT INTO `tb_users` (`username`, `login_info`, `user_tags`) VALUES
('张三', '{"tel": "13122335566", "QQ": "654321", "wechat": "zhangsan"}', '[1, 5, 8, 10]'),
('李四', '{"tel": "13599876543", "weibo": "lisi123", "wechat": "lisi_wx"}', '[2, 6, 9, 11]'),
('王五', '{"tel": "13800138000", "QQ": "123456"}', '[2, 7, 10, 12]'),
('赵六', '{"wechat": "zhaoliu_wx", "weibo": "zhaoliu_wb"}', '[3, 5, 8, 9]');

-- 1.3 查询JSON字段
-- 使用 ->> 操作符提取JSON值（MySQL 8.0简写语法）
SELECT `user_id`,
       `username`,
       `login_info` ->> '$.tel' AS `手机号`,
       `login_info` ->> '$.wechat' AS `微信`,
       `login_info` ->> '$.QQ' AS `QQ号`
FROM `tb_users`;

-- 使用JSON_EXTRACT和JSON_UNQUOTE函数提取（等效写法）
SELECT `user_id`,
       `username`,
       JSON_UNQUOTE(JSON_EXTRACT(`login_info`, '$.tel')) AS `手机号`,
       JSON_UNQUOTE(JSON_EXTRACT(`login_info`, '$.wechat')) AS `微信`
FROM `tb_users`;

-- 1.4 JSON查询函数
-- MEMBER OF: 检查元素是否在JSON数组中
-- 查询爱看电影（标签ID为10）的用户
SELECT `user_id`, `username`
FROM `tb_users`
WHERE 10 MEMBER OF (`user_tags`->'$');

-- JSON_CONTAINS: 检查JSON数组是否包含所有指定元素
-- 查询既是80后（标签2）又爱看电影（标签10）的用户
SELECT `user_id`, `username`
FROM `tb_users`
WHERE JSON_CONTAINS(`user_tags`->'$', '[2, 10]');

-- JSON_OVERLAPS: 检查JSON数组是否有重叠
-- 查询80后、90后或爱看电影的用户
SELECT `user_id`, `username`
FROM `tb_users`
WHERE JSON_OVERLAPS(`user_tags`->'$', '[2, 3, 10]');

-- =====================================================
-- 二、窗口函数 (Window Functions)
-- 从MySQL 8.0开始支持，用于OLAP统计分析
-- =====================================================

-- 创建销售数据表
CREATE TABLE `tb_sales` (
    `sale_id`      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `emp_name`     VARCHAR(50) NOT NULL COMMENT '员工姓名',
    `dept_name`    VARCHAR(50) NOT NULL COMMENT '部门名称',
    `sale_year`    INT NOT NULL COMMENT '销售年份',
    `sale_month`   INT NOT NULL COMMENT '销售月份',
    `sale_amount`  DECIMAL(12, 2) NOT NULL COMMENT '销售金额'
);

-- 插入演示数据
INSERT INTO `tb_sales` (`emp_name`, `dept_name`, `sale_year`, `sale_month`, `sale_amount`) VALUES
('张三', '华东区', 2024, 1, 15000.00),
('张三', '华东区', 2024, 2, 18000.00),
('张三', '华东区', 2024, 3, 22000.00),
('张三', '华东区', 2025, 1, 16000.00),
('张三', '华东区', 2025, 2, 20000.00),
('张三', '华东区', 2025, 3, 25000.00),
('李四', '华东区', 2024, 1, 12000.00),
('李四', '华东区', 2024, 2, 15000.00),
('李四', '华东区', 2024, 3, 19000.00),
('李四', '华东区', 2025, 1, 14000.00),
('李四', '华东区', 2025, 2, 17000.00),
('李四', '华东区', 2025, 3, 21000.00),
('王五', '华南区', 2024, 1, 20000.00),
('王五', '华南区', 2024, 2, 23000.00),
('王五', '华南区', 2024, 3, 28000.00),
('王五', '华南区', 2025, 1, 22000.00),
('王五', '华南区', 2025, 2, 26000.00),
('王五', '华南区', 2025, 3, 30000.00),
('赵六', '华南区', 2024, 1, 18000.00),
('赵六', '华南区', 2024, 2, 21000.00),
('赵六', '华南区', 2024, 3, 25000.00),
('赵六', '华南区', 2025, 1, 19000.00),
('赵六', '华南区', 2025, 2, 24000.00),
('赵六', '华南区', 2025, 3, 28000.00);

-- 2.1 ROW_NUMBER(): 行号排名（不重复）
-- 查询2025年Q1销售额排名前3的员工
SELECT `emp_name`, `dept_name`, `sale_amount`,
       ROW_NUMBER() OVER (ORDER BY `sale_amount` DESC) AS `排名`
FROM `tb_sales`
WHERE `sale_year` = 2025 AND `sale_month` = 1;

-- 2.2 RANK(): 排名（有并列会跳号）
-- 查询每个部门2025年销售额排名
SELECT `emp_name`, `dept_name`, `sale_year`, `sale_amount`,
       RANK() OVER (PARTITION BY `dept_name`, `sale_year` ORDER BY `sale_amount` DESC) AS `部门年度排名`
FROM `tb_sales`
WHERE `sale_year` = 2025;

-- 2.3 DENSE_RANK(): 排名（有并列不跳号）
-- 与RANK()的区别：RANK有并列会跳号(1,1,3)，DENSE_RANK不跳号(1,1,2)
SELECT `emp_name`, `dept_name`, `sale_amount`,
       RANK() OVER (ORDER BY `sale_amount` DESC) AS `rank排名`,
       DENSE_RANK() OVER (ORDER BY `sale_amount` DESC) AS `dense_rank排名`
FROM `tb_sales`
WHERE `sale_year` = 2025 AND `sale_month` = 1;

-- 2.4 累计求和 (Running Total)
-- 计算每个员工的月度销售累计金额
SELECT `emp_name`, `sale_year`, `sale_month`, `sale_amount`,
       SUM(`sale_amount`) OVER (
           PARTITION BY `emp_name`, `sale_year`
           ORDER BY `sale_month`
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS `累计销售额`
FROM `tb_sales`
ORDER BY `emp_name`, `sale_year`, `sale_month`;

-- 2.5 移动平均 (Moving Average)
-- 计算每个员工近3个月的移动平均销售额
SELECT `emp_name`, `sale_year`, `sale_month`, `sale_amount`,
       AVG(`sale_amount`) OVER (
           PARTITION BY `emp_name`, `sale_year`
           ORDER BY `sale_month`
           ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
       ) AS `近3月移动平均`
FROM `tb_sales`
ORDER BY `emp_name`, `sale_year`, `sale_month`;

-- 2.6 LAG() 和 LEAD(): 前后行数据访问
-- 计算每个月与上月的销售差异
SELECT `emp_name`, `sale_year`, `sale_month`, `sale_amount`,
       LAG(`sale_amount`, 1, 0) OVER (
           PARTITION BY `emp_name`, `sale_year` ORDER BY `sale_month`
       ) AS `上月销售额`,
       `sale_amount` - LAG(`sale_amount`, 1, 0) OVER (
           PARTITION BY `emp_name`, `sale_year` ORDER BY `sale_month`
       ) AS `环比增长`
FROM `tb_sales`
ORDER BY `emp_name`, `sale_year`, `sale_month`;

-- 2.7 FIRST_VALUE() 和 LAST_VALUE()
-- 查询每个部门销售额最高和最低的记录
SELECT `emp_name`, `dept_name`, `sale_year`, `sale_month`, `sale_amount`,
       FIRST_VALUE(`emp_name`) OVER (
           PARTITION BY `dept_name`, `sale_year`
           ORDER BY `sale_amount` DESC
       ) AS `销冠`,
       LAST_VALUE(`emp_name`) OVER (
           PARTITION BY `dept_name`, `sale_year`
           ORDER BY `sale_amount` DESC
           ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
       ) AS `末位`
FROM `tb_sales`
WHERE `sale_year` = 2025;

-- 2.8 NTILE(): 分桶
-- 将员工按销售额分为4个等级
SELECT `emp_name`, `sale_year`, `sale_amount`,
       NTILE(4) OVER (PARTITION BY `sale_year` ORDER BY `sale_amount` DESC) AS `业绩等级`
FROM `tb_sales`
WHERE `sale_month` = 1;

-- =====================================================
-- 三、CTE (Common Table Expressions) 公共表表达式
-- MySQL 8.0开始支持，提高SQL可读性和可维护性
-- =====================================================

-- 3.1 基本CTE
-- 查询2025年销售额超过平均值的员工
WITH `avg_sales` AS (
    SELECT AVG(`sale_amount`) AS `avg_amount`
    FROM `tb_sales`
    WHERE `sale_year` = 2025
)
SELECT `emp_name`, `dept_name`, `sale_amount`
FROM `tb_sales`
WHERE `sale_year` = 2025
  AND `sale_amount` > (SELECT `avg_amount` FROM `avg_sales`);

-- 3.2 多个CTE
-- 查询每个部门的销冠及其销售详情
WITH `dept_rank` AS (
    SELECT `emp_name`, `dept_name`, `sale_year`, `sale_amount`,
           ROW_NUMBER() OVER (PARTITION BY `dept_name`, `sale_year` ORDER BY `sale_amount` DESC) AS `rn`
    FROM `tb_sales`
),
`dept_top` AS (
    SELECT `emp_name`, `dept_name`, `sale_year`, `sale_amount`
    FROM `dept_rank`
    WHERE `rn` = 1
)
SELECT * FROM `dept_top` WHERE `sale_year` = 2025;

-- 3.3 递归CTE (Recursive CTE)
-- 生成1到10的数字序列
WITH RECURSIVE `numbers` AS (
    SELECT 1 AS `n`
    UNION ALL
    SELECT `n` + 1 FROM `numbers` WHERE `n` < 10
)
SELECT * FROM `numbers`;

-- =====================================================
-- 四、企业级分析示例
-- =====================================================

-- 4.1 同比分析 (Year-over-Year Comparison)
-- 比较2025年与2024年同期销售额
WITH `yearly_sales` AS (
    SELECT `emp_name`, `sale_year`, `sale_month`, `sale_amount`
    FROM `tb_sales`
    WHERE `sale_year` IN (2024, 2025)
)
SELECT
    a.`emp_name`,
    a.`sale_month`,
    a.`sale_amount` AS `2025年销售额`,
    b.`sale_amount` AS `2024年销售额`,
    ROUND((a.`sale_amount` - b.`sale_amount`) / b.`sale_amount` * 100, 2) AS `同比增长率(%)`
FROM
    (SELECT * FROM `yearly_sales` WHERE `sale_year` = 2025) a
JOIN
    (SELECT * FROM `yearly_sales` WHERE `sale_year` = 2024) b
ON a.`emp_name` = b.`emp_name` AND a.`sale_month` = b.`sale_month`
ORDER BY a.`emp_name`, a.`sale_month`;

-- 4.2 环比分析 (Month-over-Month)
-- 使用LAG窗口函数计算月度环比
SELECT `emp_name`, `sale_year`, `sale_month`, `sale_amount`,
       LAG(`sale_amount`, 1) OVER (
           PARTITION BY `emp_name` ORDER BY `sale_year`, `sale_month`
       ) AS `上月销售额`,
       ROUND(
           (`sale_amount` - LAG(`sale_amount`, 1) OVER (
               PARTITION BY `emp_name` ORDER BY `sale_year`, `sale_month`
           )) / LAG(`sale_amount`, 1) OVER (
               PARTITION BY `emp_name` ORDER BY `sale_year`, `sale_month`
           ) * 100, 2
       ) AS `环比增长率(%)`
FROM `tb_sales`
ORDER BY `emp_name`, `sale_year`, `sale_month`;

-- 4.3 销售占比分析
-- 计算每个员工销售额占其部门总额的百分比
SELECT `emp_name`, `dept_name`, `sale_year`, `sale_amount`,
       SUM(`sale_amount`) OVER (PARTITION BY `dept_name`, `sale_year`) AS `部门年度总额`,
       ROUND(`sale_amount` / SUM(`sale_amount`) OVER (PARTITION BY `dept_name`, `sale_year`) * 100, 2) AS `占比(%)`
FROM `tb_sales`
WHERE `sale_year` = 2025
ORDER BY `dept_name`, `sale_amount` DESC;

-- 4.4 综合报表：使用CTE + 窗口函数
-- 生成完整的销售业绩分析报表
WITH `emp_summary` AS (
    SELECT
        `emp_name`,
        `dept_name`,
        `sale_year`,
        SUM(`sale_amount`) AS `年度总额`,
        AVG(`sale_amount`) AS `月均销售额`,
        MAX(`sale_amount`) AS `最高月销售额`,
        MIN(`sale_amount`) AS `最低月销售额`
    FROM `tb_sales`
    GROUP BY `emp_name`, `dept_name`, `sale_year`
),
`ranked` AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY `dept_name`, `sale_year` ORDER BY `年度总额` DESC) AS `部门排名`,
           ROW_NUMBER() OVER (PARTITION BY `sale_year` ORDER BY `年度总额` DESC) AS `公司排名`
    FROM `emp_summary`
)
SELECT
    `emp_name` AS `员工`,
    `dept_name` AS `部门`,
    `sale_year` AS `年度`,
    `年度总额`,
    ROUND(`月均销售额`, 2) AS `月均销售额`,
    `部门排名`,
    `公司排名`
FROM `ranked`
ORDER BY `sale_year`, `公司排名`;

-- =====================================================
-- 五、不可见索引 (Invisible Indexes)
-- MySQL 8.0开始支持，用于安全地测试索引删除的影响
-- =====================================================

-- 5.1 创建不可见索引
-- 不可见索引不会被优化器使用，但仍会被维护
CREATE INDEX `idx_sale_year` ON `tb_sales`(`sale_year`) INVISIBLE;

-- 5.2 将索引设为不可见（测试删除索引的影响）
ALTER TABLE `tb_sales` ALTER INDEX `idx_sale_year` INVISIBLE;

-- 5.3 将索引设为可见（恢复索引）
ALTER TABLE `tb_sales` ALTER INDEX `idx_sale_year` VISIBLE;

-- 5.4 创建表时指定不可见索引
CREATE TABLE `tb_test_invisible` (
    `id` INT PRIMARY KEY,
    `name` VARCHAR(50),
    `status` INT,
    INDEX `idx_status` (`status`) INVISIBLE
);

-- 5.5 查看索引可见性
SHOW INDEX FROM `tb_sales`;

-- =====================================================
-- 六、清理演示数据
-- =====================================================

-- DROP DATABASE IF EXISTS `demo_mysql8`;
