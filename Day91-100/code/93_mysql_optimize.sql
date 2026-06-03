-- ============================================================================
-- 93_mysql_optimize.sql
-- MySQL 性能优化实战指南
-- 基于 Day91-100/93.MySQL性能优化.md 文档编写
-- 覆盖: 建库建表规范、索引优化、EXPLAIN 分析、慢查询日志、分区、SQL 优化
-- ============================================================================


-- ============================================================================
-- 第一部分: 建库建表规范
-- MySQL 只用于数据存储，不进行复杂计算，确保存储和计算分离
-- ============================================================================

-- 创建示例数据库，指定 UTF8mb4 字符集
DROP DATABASE IF EXISTS db_enterprise;
CREATE DATABASE db_enterprise
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_general_ci;

USE db_enterprise;

-- ---------------------------------------------------------------------------
-- 1.1 员工表 (符合建表规范)
-- 规范要点:
--   - 主键使用 unsigned int + auto_increment
--   - 必备三字段: xxx_id, xxx_create, xxx_modified
--   - 所有字段指定 NOT NULL 并设置默认值 (NULL 值导致复合索引失效)
--   - 每列都有 COMMENT 注释
--   - 显式指定 ENGINE=InnoDB
--   - 禁用 enum/set 类型
--   - 大文件不使用 blob 而是保存路径
--   - IP 地址使用 int unsigned 而非 char(15)
--   - 货币使用 decimal 而非 float
-- ---------------------------------------------------------------------------
CREATE TABLE tb_employee (
    emp_id          INT UNSIGNED    NOT NULL AUTO_INCREMENT COMMENT '员工主键ID',
    emp_name        VARCHAR(50)     NOT NULL DEFAULT '' COMMENT '员工姓名',
    emp_email       VARCHAR(100)    NOT NULL DEFAULT '' COMMENT '电子邮箱',
    emp_phone       VARCHAR(20)     NOT NULL DEFAULT '' COMMENT '手机号码',
    emp_ip          INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '最近登录IP(使用inet_aton转换)',
    dept_id         INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '部门ID',
    salary          DECIMAL(10,2)   NOT NULL DEFAULT 0.00 COMMENT '月薪(使用decimal保证精度)',
    hire_date       DATE            NOT NULL DEFAULT '1970-01-01' COMMENT '入职日期',
    avatar_path     VARCHAR(255)    NOT NULL DEFAULT '' COMMENT '头像文件路径(不使用blob存储)',
    status          TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '状态: 1-在职 2-离职 3-试用期',
    emp_create      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    emp_modified    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录修改时间',
    PRIMARY KEY (emp_id),
    UNIQUE KEY uk_email (emp_email),
    KEY idx_dept_id (dept_id),
    KEY idx_hire_date (hire_date),
    KEY idx_name_phone (emp_name, emp_phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='员工信息表';

-- ---------------------------------------------------------------------------
-- 1.2 部门表
-- ---------------------------------------------------------------------------
CREATE TABLE tb_department (
    dept_id         INT UNSIGNED    NOT NULL AUTO_INCREMENT COMMENT '部门主键ID',
    dept_name       VARCHAR(100)    NOT NULL DEFAULT '' COMMENT '部门名称',
    parent_id       INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '上级部门ID',
    manager_id      INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '部门经理员工ID',
    dept_create     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    dept_modified   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录修改时间',
    PRIMARY KEY (dept_id),
    KEY idx_parent_id (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='部门信息表';

-- ---------------------------------------------------------------------------
-- 1.3 订单表 (大批量数据场景)
-- ---------------------------------------------------------------------------
CREATE TABLE tb_order (
    order_id        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '订单主键ID',
    order_no        VARCHAR(32)     NOT NULL DEFAULT '' COMMENT '订单编号',
    cust_id         INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '客户ID',
    emp_id          INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '负责员工ID',
    order_amount    DECIMAL(12,2)   NOT NULL DEFAULT 0.00 COMMENT '订单金额',
    order_status    TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '订单状态: 0-待付款 1-已付款 2-已发货 3-已完成 4-已取消',
    order_date      DATE            NOT NULL DEFAULT '1970-01-01' COMMENT '下单日期',
    remark          VARCHAR(500)    NOT NULL DEFAULT '' COMMENT '备注信息',
    order_create    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    order_modified  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录修改时间',
    PRIMARY KEY (order_id),
    UNIQUE KEY uk_order_no (order_no),
    KEY idx_cust_id (cust_id),
    KEY idx_emp_id (emp_id),
    KEY idx_order_date (order_date),
    KEY idx_status_date (order_status, order_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单信息表';

-- ---------------------------------------------------------------------------
-- 1.4 IP 地址存储示例
-- 不用 char(15) 存储 IP，而是用 int unsigned + inet_aton/inet_ntoa
-- ---------------------------------------------------------------------------
-- 插入示例: 将 IP '192.168.1.100' 转为整数
INSERT INTO tb_employee (emp_name, emp_email, emp_ip, dept_id, salary, hire_date)
VALUES ('张三', 'zhangsan@example.com', INET_ATON('192.168.1.100'), 1, 15000.00, '2020-03-15');

-- 查询时将整数转回 IP 地址
SELECT emp_name, INET_NTOA(emp_ip) AS login_ip FROM tb_employee WHERE emp_id = 1;


-- ============================================================================
-- 第二部分: 索引优化
-- 索引是提升查询性能最重要的手段之一
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 2.1 索引设计原则演示
-- ---------------------------------------------------------------------------

-- 原则1: 索引应创建在 WHERE 子句和 JOIN 条件中频繁出现的列上
-- tb_order 表中 cust_id 和 order_status 在查询中经常出现在 WHERE 子句
-- 已在建表时创建: KEY idx_cust_id (cust_id), KEY idx_status_date (order_status, order_date)

-- 原则2: 选择性高的列适合创建索引 (唯一值多)
-- emp_email 具有唯一性，适合创建唯一索引 -> 已创建 UNIQUE KEY uk_email

-- 原则3: 对字符串创建前缀索引，减少磁盘 I/O
-- 假设订单编号很长，可以只索引前 N 个字符
ALTER TABLE tb_order ADD KEY idx_order_no_prefix (order_no(8));

-- 原则4: 复合索引遵循最左前缀原则
-- 创建复合索引 (order_status, order_date) 后:
--   SELECT * FROM tb_order WHERE order_status = 1;                    -- 使用索引 (命中最左前缀)
--   SELECT * FROM tb_order WHERE order_status = 1 AND order_date = '2024-01-01'; -- 使用索引
--   SELECT * FROM tb_order WHERE order_date = '2024-01-01';           -- 不使用索引 (跳过最左列)

-- 原则5: 不要过度索引，每个索引都会占用存储空间并影响写入性能
-- 写操作 (INSERT/UPDATE/DELETE) 时索引需要同步更新

-- 原则6: 注意索引失效的场景
-- 以下情况会导致索引失效:
--   a) 模糊查询使用前置通配符: WHERE emp_name LIKE '%张'    -- 索引失效
--   b) 使用负向条件: WHERE dept_id != 1 / NOT IN / NOT EXISTS
--   c) 对索引列使用函数: WHERE YEAR(hire_date) = 2024       -- 索引失效
--   d) 隐式类型转换: WHERE emp_id = '100' (emp_id 是 INT)   -- 可能失效

-- ---------------------------------------------------------------------------
-- 2.2 使用 SQL 提示控制索引选择
-- ---------------------------------------------------------------------------

-- USE INDEX: 建议 MySQL 使用指定索引 (不强制)
SELECT * FROM tb_order USE INDEX (idx_cust_id) WHERE cust_id = 1001;

-- IGNORE INDEX: 建议 MySQL 忽略指定索引
SELECT * FROM tb_order IGNORE INDEX (idx_order_date) WHERE order_date = '2024-06-01';

-- FORCE INDEX: 强制 MySQL 使用指定索引
SELECT * FROM tb_order FORCE INDEX (idx_status_date)
WHERE order_status = 1 AND order_date >= '2024-01-01';


-- ============================================================================
-- 第三部分: EXPLAIN 执行计划分析
-- EXPLAIN 是分析 SQL 性能最重要的工具
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 3.1 EXPLAIN 基本用法
-- 关键字段说明:
--   select_type  : 查询类型 (SIMPLE/PRIMARY/UNION/SUBQUERY/DERIVED)
--   type         : 访问类型，从好到差: system > const > eq_ref > ref > range > index > ALL
--   possible_keys: 可能使用的索引
--   key          : 实际使用的索引
--   key_len      : 索引使用的字节长度
--   rows         : 预估扫描行数 (越少越好)
--   Extra        : 额外信息 (Using index/Using filesort/Using temporary 等)
-- ---------------------------------------------------------------------------

-- 示例 1: 全表扫描 (type=ALL, 性能最差)
EXPLAIN SELECT * FROM tb_employee WHERE emp_name LIKE '%张%';
-- 分析: 前置通配符导致索引失效，type=ALL 表示全表扫描

-- 示例 2: 使用索引的等值查询 (type=ref)
EXPLAIN SELECT emp_name, emp_email FROM tb_employee WHERE dept_id = 20;
-- 分析: dept_id 上有索引 idx_dept_id，type=ref 表示使用了非唯一索引

-- 示例 3: 使用唯一索引 (type=const)
EXPLAIN SELECT * FROM tb_employee WHERE emp_email = 'zhangsan@example.com';
-- 分析: emp_email 上有唯一索引 uk_email，type=const 表示最多返回一行

-- 示例 4: 范围查询 (type=range)
EXPLAIN SELECT * FROM tb_order WHERE order_date BETWEEN '2024-01-01' AND '2024-06-30';
-- 分析: order_date 上有索引，BETWEEN 属于范围查询，type=range

-- 示例 5: 复合索引的最左前缀验证
EXPLAIN SELECT * FROM tb_order WHERE order_status = 1 AND order_date = '2024-06-01';
-- 分析: 使用复合索引 idx_status_date(order_status, order_date)，两个条件都命中

EXPLAIN SELECT * FROM tb_order WHERE order_date = '2024-06-01';
-- 分析: 跳过了复合索引的最左列 order_status，索引无法使用

-- ---------------------------------------------------------------------------
-- 3.2 EXPLAIN 中 Extra 字段的常见值解读
-- ---------------------------------------------------------------------------

-- "Using index": 覆盖索引，查询的列都在索引中，无需回表 (性能好)
EXPLAIN SELECT order_status, order_date FROM tb_order WHERE order_status = 1;

-- "Using filesort": 需要额外排序操作 (性能差，应优化)
EXPLAIN SELECT * FROM tb_order ORDER BY cust_id;

-- "Using temporary": 使用了临时表 (性能差，常见于 GROUP BY/ORDER BY 不同列)
EXPLAIN SELECT order_status, COUNT(*) FROM tb_order GROUP BY order_status;

-- "Using where": 在存储引擎层过滤后还需要在服务层过滤
EXPLAIN SELECT * FROM tb_order WHERE remark LIKE '%加急%';


-- ============================================================================
-- 第四部分: SHOW PROFILES 性能剖析
-- 用于分析单条 SQL 的执行耗时细节
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 4.1 开启剖面系统
-- ---------------------------------------------------------------------------
-- 检查是否支持 profiling
SELECT @@have_profiling;

-- 检查 profiling 是否开启
SELECT @@profiling;

-- 开启 profiling
SET profiling = 1;

-- ---------------------------------------------------------------------------
-- 4.2 使用剖面系统分析 SQL
-- ---------------------------------------------------------------------------

-- 执行待分析的查询
SELECT COUNT(*) FROM tb_order;
SELECT * FROM tb_employee WHERE dept_id = 1 ORDER BY emp_name;

-- 查看所有已记录的查询及其耗时
SHOW PROFILES;

-- 查看指定查询的详细执行阶段耗时
-- Query_ID 根据 SHOW PROFILES 的结果替换
SHOW PROFILE FOR QUERY 1;

-- 查看指定查询的 CPU 使用情况
SHOW PROFILE CPU FOR QUERY 1;

-- 查看指定查询的特定阶段信息 (如查看 IO 等待)
SHOW PROFILE BLOCK IO FOR QUERY 1;


-- ============================================================================
-- 第五部分: 慢查询日志
-- 用于定位执行时间超过阈值的低效 SQL
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 5.1 查看慢查询日志配置
-- ---------------------------------------------------------------------------
SHOW VARIABLES LIKE 'slow_query%';
SHOW VARIABLES LIKE 'long_query_time';

-- ---------------------------------------------------------------------------
-- 5.2 通过 SQL 命令启用慢查询日志 (临时生效，重启后失效)
-- ---------------------------------------------------------------------------
-- 设置慢查询日志文件路径
SET GLOBAL slow_query_log_file = '/var/log/mysql/mysqld-slow.log';

-- 开启慢查询日志
SET GLOBAL slow_query_log = 'ON';

-- 设置慢查询阈值为 1 秒 (默认 10 秒)
SET GLOBAL long_query_time = 1;

-- 记录没有使用索引的查询
SET GLOBAL log_queries_not_using_indexes = 'ON';

-- ---------------------------------------------------------------------------
-- 5.3 通过配置文件启用 (永久生效)
-- 在 my.cnf 或 my.ini 的 [mysqld] 段添加以下配置:
-- ---------------------------------------------------------------------------
/*
[mysqld]
slow_query_log = ON
slow_query_log_file = /var/log/mysql/mysqld-slow.log
long_query_time = 1
log_queries_not_using_indexes = ON
*/

-- ---------------------------------------------------------------------------
-- 5.4 分析慢查询日志 (使用 mysqldumpslow 工具)
-- ---------------------------------------------------------------------------
/*
-- 查看最慢的 10 条 SQL
mysqldumpslow -s t -t 10 /var/log/mysql/mysqld-slow.log

-- 查看访问次数最多的 10 条 SQL
mysqldumpslow -s c -t 10 /var/log/mysql/mysqld-slow.log

-- 查看返回记录数最多的 10 条 SQL
mysqldumpslow -s r -t 10 /var/log/mysql/mysqld-slow.log

参数说明:
  -s: 排序方式 (t=时间, c=次数, l=锁时间, r=返回记录数)
  -t: 返回前 N 条
  -g: 正则过滤
*/

-- ---------------------------------------------------------------------------
-- 5.5 查看服务器运行状态指标
-- ---------------------------------------------------------------------------
SHOW STATUS LIKE 'slow_queries';       -- 慢查询总数
SHOW STATUS LIKE 'com_%';              -- 各类命令执行次数
SHOW STATUS LIKE 'innodb_%';           -- InnoDB 引擎状态
SHOW STATUS LIKE 'connections';        -- 连接数


-- ============================================================================
-- 第六部分: SQL 优化 (CRUD 操作)
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 6.1 INSERT 优化
-- ---------------------------------------------------------------------------

-- 优化1: 批量插入代替逐条插入 (减少网络往返和事务开销)
-- 差的写法:
--   INSERT INTO tb_employee (emp_name, emp_email, dept_id) VALUES ('张三', 'a@x.com', 1);
--   INSERT INTO tb_employee (emp_name, emp_email, dept_id) VALUES ('李四', 'b@x.com', 2);
--   INSERT INTO tb_employee (emp_name, emp_email, dept_id) VALUES ('王五', 'c@x.com', 1);

-- 好的写法: 一次插入多组值
INSERT INTO tb_employee (emp_name, emp_email, dept_id, salary, hire_date)
VALUES
    ('张三', 'a@x.com', 1, 12000.00, '2023-01-15'),
    ('李四', 'b@x.com', 2, 15000.00, '2023-02-20'),
    ('王五', 'c@x.com', 1, 18000.00, '2023-03-10');

-- 优化2: 从文件加载大量数据 (比 INSERT 快很多)
-- LOAD DATA INFILE '/tmp/employees.csv'
-- INTO TABLE tb_employee
-- FIELDS TERMINATED BY ','
-- ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 ROWS
-- (emp_name, emp_email, dept_id, salary, hire_date);

-- 优化3: 大批量插入时临时关闭索引更新
ALTER TABLE tb_order DISABLE KEYS;
-- ... 执行大批量插入 ...
ALTER TABLE tb_order ENABLE KEYS;

-- ---------------------------------------------------------------------------
-- 6.2 ORDER BY 优化
-- ---------------------------------------------------------------------------

-- 优化思路: 利用索引完成排序，避免 filesort
-- 如果 WHERE 和 ORDER BY 的列与索引一致，且排序方向相同，可直接用索引排序

-- 好的写法: idx_status_date(order_status, order_date) 可以同时用于过滤和排序
SELECT * FROM tb_order
WHERE order_status = 1
ORDER BY order_date ASC;

-- 差的写法: ORDER BY 的列不在索引中，触发 filesort
SELECT * FROM tb_order ORDER BY cust_id;

-- ---------------------------------------------------------------------------
-- 6.3 GROUP BY 优化
-- ---------------------------------------------------------------------------

-- 优化: 使用 ORDER BY NULL 避免 GROUP BY 后的隐式排序开销
-- MySQL 对 GROUP BY 的结果默认会按分组字段排序，如果不需要排序可以禁用

-- 好的写法: 禁用排序
SELECT order_status, COUNT(*) AS cnt
FROM tb_order
GROUP BY order_status
ORDER BY NULL;

-- ---------------------------------------------------------------------------
-- 6.4 子查询优化 (用 JOIN 替代)
-- ---------------------------------------------------------------------------

-- 差的写法: 使用子查询
SELECT * FROM tb_employee
WHERE dept_id IN (SELECT dept_id FROM tb_department WHERE parent_id = 0);

-- 好的写法: 使用 INNER JOIN 替代子查询 (避免创建临时表)
SELECT e.* FROM tb_employee e
INNER JOIN tb_department d ON e.dept_id = d.dept_id
WHERE d.parent_id = 0;

-- ---------------------------------------------------------------------------
-- 6.5 OR 条件优化
-- ---------------------------------------------------------------------------

-- 注意: OR 条件中只有所有列都有索引时索引才生效
-- 如果部分列无索引，可改写为 UNION ALL

-- 可能不走索引的写法:
SELECT * FROM tb_order WHERE order_status = 1 OR cust_id = 1001;

-- 改写为 UNION ALL (确保每个子查询都能走索引)
SELECT * FROM tb_order WHERE order_status = 1
UNION ALL
SELECT * FROM tb_order WHERE cust_id = 1001 AND order_status != 1;

-- ---------------------------------------------------------------------------
-- 6.6 分页查询优化 (企业级常见场景)
-- ---------------------------------------------------------------------------

-- 问题: LIMIT 偏移量大时性能极差
-- 当 offset=10000, limit=20 时，MySQL 需要扫描前 10020 行，丢弃前 10000 行

-- 差的写法: 大偏移量分页
SELECT * FROM tb_order ORDER BY order_id LIMIT 10000, 20;

-- 好的写法: 在索引上完成分页，再做表连接
SELECT o.* FROM tb_order o
INNER JOIN (
    SELECT order_id FROM tb_order ORDER BY order_id LIMIT 10000, 20
) AS tmp ON o.order_id = tmp.order_id;
-- 子查询只需扫描索引列 (order_id 是主键)，不需要回表取所有列

-- 更好的写法: 使用延迟关联 + 书签方式 (记住上次最后一条的 ID)
-- 假设上一页最后一条 order_id = 10000
SELECT * FROM tb_order
WHERE order_id > 10000
ORDER BY order_id
LIMIT 20;
-- 这种方式完全避免了 offset 扫描，适合 "无限滚动" 或 "加载更多" 场景

-- ---------------------------------------------------------------------------
-- 6.7 COUNT 优化
-- ---------------------------------------------------------------------------

-- COUNT(*) 和 COUNT(1) 在 InnoDB 中性能基本一致，都会统计所有行
-- COUNT(column) 会排除该列为 NULL 的行

-- 如果需要精确计数且表很大，可考虑维护计数器 (中间表/缓存)
SELECT COUNT(*) FROM tb_order;

-- 近似计数 (适用于允许近似值的大表场景)
EXPLAIN SELECT COUNT(*) FROM tb_order;
-- EXPLAIN 输出的 rows 字段是 InnoDB 的估算值，大表时可作为参考


-- ============================================================================
-- 第七部分: 数据分区
-- 通过分区可以优化查询、加快数据删除、提升吞吐量
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 7.1 RANGE 分区: 按年份范围分区
-- 适用于按时间范围查询的历史数据表
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS tb_order_partitioned;
CREATE TABLE tb_order_partitioned (
    order_id        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '订单ID',
    order_no        VARCHAR(32)     NOT NULL DEFAULT '' COMMENT '订单编号',
    cust_id         INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '客户ID',
    order_amount    DECIMAL(12,2)   NOT NULL DEFAULT 0.00 COMMENT '订单金额',
    order_date      DATE            NOT NULL COMMENT '下单日期',
    order_create    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (order_id, order_date),   -- 分区键必须包含在主键中
    KEY idx_cust_id (cust_id),
    KEY idx_order_date (order_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='按年份RANGE分区的订单表'
PARTITION BY RANGE (YEAR(order_date)) (
    PARTITION p2020 VALUES LESS THAN (2021) COMMENT '2020年数据',
    PARTITION p2021 VALUES LESS THAN (2022) COMMENT '2021年数据',
    PARTITION p2022 VALUES LESS THAN (2023) COMMENT '2022年数据',
    PARTITION p2023 VALUES LESS THAN (2024) COMMENT '2023年数据',
    PARTITION p2024 VALUES LESS THAN (2025) COMMENT '2024年数据',
    PARTITION pmax  VALUES LESS THAN MAXVALUE COMMENT '未来数据兜底分区'
);

-- 验证分区信息
SELECT PARTITION_NAME, PARTITION_EXPRESSION, TABLE_ROWS
FROM INFORMATION_SCHEMA.PARTITIONS
WHERE TABLE_SCHEMA = 'db_enterprise' AND TABLE_NAME = 'tb_order_partitioned';

-- 查询时如果 WHERE 条件包含分区键，MySQL 只扫描对应分区 (分区裁剪)
EXPLAIN SELECT * FROM tb_order_partitioned WHERE order_date = '2024-06-01';
-- 只扫描 p2024 分区，而非全表

-- 快速删除过期数据: 直接删除整个分区比 DELETE 快得多
ALTER TABLE tb_order_partitioned DROP PARTITION p2020;

-- 添加新分区
ALTER TABLE tb_order_partitioned REORGANIZE PARTITION pmax INTO (
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION pmax  VALUES LESS THAN MAXVALUE
);

-- ---------------------------------------------------------------------------
-- 7.2 HASH 分区: 按客户 ID 哈希分区
-- 适用于需要均匀分布数据的场景
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS tb_cust_hash;
CREATE TABLE tb_cust_hash (
    cust_id     INT UNSIGNED    NOT NULL AUTO_INCREMENT COMMENT '客户ID',
    cust_name   VARCHAR(100)    NOT NULL DEFAULT '' COMMENT '客户名称',
    cust_create DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (cust_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='按客户ID HASH分区'
PARTITION BY HASH (cust_id)
PARTITIONS 4;

-- ---------------------------------------------------------------------------
-- 7.3 LIST 分区: 按状态值枚举分区
-- 适用于分区键为离散值的场景
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS tb_status_list;
CREATE TABLE tb_status_list (
    record_id       INT UNSIGNED    NOT NULL AUTO_INCREMENT COMMENT '记录ID',
    region_code     INT UNSIGNED    NOT NULL COMMENT '区域编码: 1-华东 2-华南 3-华北 4-其他',
    record_data     VARCHAR(200)    NOT NULL DEFAULT '' COMMENT '记录数据',
    rec_create      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (record_id, region_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='按区域LIST分区'
PARTITION BY LIST (region_code) (
    PARTITION p_east   VALUES IN (1) COMMENT '华东',
    PARTITION p_south  VALUES IN (2) COMMENT '华南',
    PARTITION p_north  VALUES IN (3) COMMENT '华北',
    PARTITION p_other  VALUES IN (4, 5, 6) COMMENT '其他区域'
);


-- ============================================================================
-- 第八部分: 配置优化
-- MySQL 关键参数调优
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 8.1 查看关键配置参数
-- ---------------------------------------------------------------------------
SHOW VARIABLES LIKE 'max_connections';           -- 最大连接数 (默认 151, 建议不超过 1000)
SHOW VARIABLES LIKE 'back_log';                  -- TCP 连接积压队列 (约 max_connections/5, 不超过 900)
SHOW VARIABLES LIKE 'table_open_cache';          -- 表缓存 (应设为 max_connections * N)
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';   -- InnoDB 缓冲池 (可设为物理内存的 80%)
SHOW VARIABLES LIKE 'innodb_lock_wait_timeout';  -- 行锁等待超时 (默认 50ms)
SHOW VARIABLES LIKE 'key_buffer_size';           -- MyISAM 索引缓冲 (仅 MyISAM 使用)

-- ---------------------------------------------------------------------------
-- 8.2 推荐配置 (在 my.cnf 的 [mysqld] 段设置)
-- ---------------------------------------------------------------------------
/*
[mysqld]
# 最大连接数 (根据业务并发量调整)
max_connections = 500

# TCP 积压队列
back_log = 100

# 表缓存 = max_connections * 每连接平均打开表数
table_open_cache = 2000

# InnoDB 缓冲池大小 (假设服务器有 16GB 内存，分配 12GB)
innodb_buffer_pool_size = 12G

# 行锁等待超时 (在线业务建议 3-10 秒，批处理可适当增大)
innodb_lock_wait_timeout = 5
*/


-- ============================================================================
-- 第九部分: 企业级优化实战示例
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 9.1 场景: 电商订单报表查询优化
-- 需求: 查询某客户在 2024 年的已完成订单，按日期倒序
-- ---------------------------------------------------------------------------

-- 优化前: 无索引，全表扫描
-- ALTER TABLE tb_order DROP INDEX idx_cust_id;
-- SELECT * FROM tb_order WHERE cust_id = 1001 AND order_status = 3
--   AND order_date BETWEEN '2024-01-01' AND '2024-12-31'
--   ORDER BY order_date DESC;

-- 优化方案: 创建覆盖查询条件的复合索引
ALTER TABLE tb_order ADD KEY idx_cust_status_date (cust_id, order_status, order_date);

-- 优化后: 使用复合索引，避免排序
SELECT order_id, order_no, order_amount, order_date
FROM tb_order
WHERE cust_id = 1001
  AND order_status = 3
  AND order_date BETWEEN '2024-01-01' AND '2024-12-31'
ORDER BY order_date DESC;

-- 使用 EXPLAIN 验证优化效果
EXPLAIN SELECT order_id, order_no, order_amount, order_date
FROM tb_order
WHERE cust_id = 1001
  AND order_status = 3
  AND order_date BETWEEN '2024-01-01' AND '2024-12-31'
ORDER BY order_date DESC;
-- 预期: type=range, key=idx_cust_status_date, Extra 中无 filesort

-- ---------------------------------------------------------------------------
-- 9.2 场景: 分页查询优化 - 后台管理系统订单列表
-- 需求: 按订单创建时间倒序分页展示，支持大偏移量
-- ---------------------------------------------------------------------------

-- 差的写法: 直接使用大 offset
SELECT * FROM tb_order ORDER BY order_create DESC LIMIT 10000, 20;

-- 好的写法: 覆盖索引 + 延迟关联
SELECT o.* FROM tb_order o
INNER JOIN (
    SELECT order_id FROM tb_order ORDER BY order_create DESC LIMIT 10000, 20
) AS tmp ON o.order_id = tmp.order_id;

-- 最佳写法: 游标分页 (记住上一页最后一条记录的值)
-- 假设上一页最后一条的 order_create = '2024-06-15 10:30:00', order_id = 50020
SELECT * FROM tb_order
WHERE order_create < '2024-06-15 10:30:00'
   OR (order_create = '2024-06-15 10:30:00' AND order_id < 50020)
ORDER BY order_create DESC, order_id DESC
LIMIT 20;

-- ---------------------------------------------------------------------------
-- 9.3 场景: 统计报表优化 - 使用中间表
-- 需求: 按部门统计 2024 年入职人数和平均工资
-- ---------------------------------------------------------------------------

-- 差的写法: 直接对大表做复杂聚合
-- SELECT d.dept_name, COUNT(*) AS emp_count, AVG(e.salary) AS avg_salary
-- FROM tb_employee e
-- INNER JOIN tb_department d ON e.dept_id = d.dept_id
-- WHERE e.hire_date BETWEEN '2024-01-01' AND '2024-12-31'
-- GROUP BY d.dept_name;

-- 好的写法: 先将筛选数据放入中间表，再做聚合
-- Step 1: 创建中间表
CREATE TEMPORARY TABLE tmp_emp_2024 AS
SELECT dept_id, salary
FROM tb_employee
WHERE hire_date BETWEEN '2024-01-01' AND '2024-12-31';

-- Step 2: 对中间表做聚合
SELECT d.dept_name, COUNT(*) AS emp_count, AVG(t.salary) AS avg_salary
FROM tmp_emp_2024 t
INNER JOIN tb_department d ON t.dept_id = d.dept_id
GROUP BY d.dept_name;

-- Step 3: 清理临时表
DROP TEMPORARY TABLE tmp_emp_2024;

-- ---------------------------------------------------------------------------
-- 9.4 场景: 大批量数据维护
-- 需求: 批量更新订单状态
-- ---------------------------------------------------------------------------

-- 差的写法: 逐条更新 (每条一次网络往返 + 事务)
-- UPDATE tb_order SET order_status = 4 WHERE order_id = 1;
-- UPDATE tb_order SET order_status = 4 WHERE order_id = 2;
-- ...

-- 好的写法: 批量更新
UPDATE tb_order SET order_status = 4
WHERE order_id IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10);

-- 更好的写法: 超大批量时分批执行，避免长事务和锁争用
-- 每次更新 1000 条，循环执行直到处理完成
UPDATE tb_order SET order_status = 4
WHERE order_status = 0 AND order_date < '2020-01-01'
LIMIT 1000;

-- ---------------------------------------------------------------------------
-- 9.5 场景: IP 地址查询优化
-- 需求: 查询某 IP 段的登录记录
-- ---------------------------------------------------------------------------

-- 使用 inet_aton 将 IP 段转为整数范围查询 (比字符串比较高效)
SELECT emp_name, INET_NTOA(emp_ip) AS login_ip
FROM tb_employee
WHERE emp_ip BETWEEN INET_ATON('192.168.1.0') AND INET_ATON('192.168.1.255');


-- ============================================================================
-- 第十部分: 逆范式与架构优化示例
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 10.1 逆范式设计: 冗余字段减少连表查询
-- 在订单表中冗余客户名称，避免每次查订单都要 JOIN 客户表
-- ---------------------------------------------------------------------------
ALTER TABLE tb_order ADD COLUMN cust_name VARCHAR(100) NOT NULL DEFAULT '' COMMENT '客户姓名(冗余字段)';

-- 冗余字段需要在业务层维护一致性 (如客户改名时同步更新)
-- UPDATE tb_order SET cust_name = '新名称' WHERE cust_id = 1001;

-- 查询时无需 JOIN 客户表
SELECT order_no, cust_name, order_amount, order_date
FROM tb_order
WHERE cust_id = 1001;

-- ---------------------------------------------------------------------------
-- 10.2 垂直拆分: 将大字段分离到扩展表
-- 如果 tb_employee 有大字段 (如个人简介 TEXT)，应拆分到独立表
-- ---------------------------------------------------------------------------
CREATE TABLE tb_employee_ext (
    emp_id          INT UNSIGNED    NOT NULL COMMENT '员工ID(与主表一致)',
    biography       TEXT            NOT NULL COMMENT '个人简介(大字段)',
    emp_ext_create  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    emp_ext_modified DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
    PRIMARY KEY (emp_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='员工扩展信息表(大字段分离)';


-- ============================================================================
-- 第十一部分: 运维诊断常用查询
-- ============================================================================

-- 查看当前正在执行的进程
SHOW PROCESSLIST;

-- 终止指定连接
-- KILL <process_id>;

-- 查看 InnoDB 引擎状态
SHOW ENGINE INNODB STATUS;

-- 查看表的索引信息
SHOW INDEX FROM tb_order;

-- 查看表的大小
SELECT
    TABLE_NAME,
    TABLE_ROWS,
    ROUND(DATA_LENGTH / 1024 / 1024, 2) AS data_mb,
    ROUND(INDEX_LENGTH / 1024 / 1024, 2) AS index_mb
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'db_enterprise'
ORDER BY DATA_LENGTH DESC;

-- 查看未使用的索引 (MySQL 8.0+ sys schema)
-- SELECT * FROM sys.schema_unused_indexes WHERE object_schema = 'db_enterprise';

-- 查看冗余索引 (MySQL 8.0+ sys schema)
-- SELECT * FROM sys.schema_redundant_indexes WHERE table_schema = 'db_enterprise';


-- ============================================================================
-- 清理测试环境
-- ============================================================================
-- DROP DATABASE IF EXISTS db_enterprise;
