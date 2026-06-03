-- ============================================================
-- Day 43: MySQL 索引 (Index) 与 EXPLAIN 性能分析
-- 主题: B+树索引原理、索引类型、EXPLAIN 执行计划解读
-- 场景: 企业级性能优化实践
-- ============================================================

-- ----------------------------------------------------------
-- 1. 准备测试环境
-- ----------------------------------------------------------

-- 创建演示数据库
DROP DATABASE IF EXISTS demo_index;
CREATE DATABASE demo_index DEFAULT CHARSET utf8mb4;
USE demo_index;

-- 员工表: 模拟企业人事系统
CREATE TABLE tb_employee (
    emp_id      INT         NOT NULL AUTO_INCREMENT COMMENT '员工ID(主键, 聚集索引)',
    emp_name    VARCHAR(50) NOT NULL COMMENT '员工姓名',
    dept_id     INT         NOT NULL COMMENT '部门ID',
    salary      DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '薪资',
    hire_date   DATE        NOT NULL COMMENT '入职日期',
    phone       VARCHAR(20) DEFAULT NULL COMMENT '手机号码',
    email       VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
    status      TINYINT     NOT NULL DEFAULT 1 COMMENT '状态: 1-在职, 0-离职',
    remark      VARCHAR(200) DEFAULT NULL COMMENT '备注',
    PRIMARY KEY (emp_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='员工表';

-- 批量插入测试数据 (使用存储过程)
DELIMITER $$
CREATE PROCEDURE sp_insert_employees(IN cnt INT)
BEGIN
    DECLARE i INT DEFAULT 1;
    DECLARE surnames VARCHAR(200) DEFAULT '王李张刘陈杨黄赵周吴徐孙马胡朱郭何罗高林梁郑谢韩唐冯于董萧程曹袁邓许傅沈曾彭吕苏卢蒋蔡贾丁魏薛叶阎余潘杜戴夏钟汪田任姜范方石姚谭廖邹熊金陆郝孔白崔康毛邱秦江史顾侯邵孟龙万段漕钱汤尹黎易常武乔贺赖龚文';
    DECLARE names VARCHAR(200) DEFAULT '伟芳娜秀英敏静丽强磊洋艳勇军杰娟涛明超秀华刚桂英平燕红玉梅飞雪春华建华建国建军志强秀兰';
    WHILE i <= cnt DO
        INSERT INTO tb_employee (emp_name, dept_id, salary, hire_date, phone, email, status)
        VALUES (
            CONCAT(
                SUBSTRING(surnames, FLOOR(1 + RAND() * 50), 1),
                SUBSTRING(names, FLOOR(1 + RAND() * 30), 1),
                IF(RAND() > 0.5, SUBSTRING(names, FLOOR(1 + RAND() * 30), 1), '')
            ),
            FLOOR(1 + RAND() * 8),                  -- 8 个部门
            ROUND(5000 + RAND() * 45000, 2),         -- 5000~50000
            DATE_ADD('2015-01-01', INTERVAL FLOOR(RAND() * 3650) DAY),
            CONCAT('138', LPAD(FLOOR(RAND() * 100000000), 8, '0')),
            CONCAT('emp', i, '@company.com'),
            IF(RAND() > 0.1, 1, 0)
        );
        SET i = i + 1;
    END WHILE;
END$$
DELIMITER ;

-- 插入 10000 条测试数据
CALL sp_insert_employees(10000);

-- ----------------------------------------------------------
-- 2. EXPLAIN 基础: 查看全表扫描 (type = ALL)
-- 未创建任何索引时的查询性能分析
-- ----------------------------------------------------------

-- 场景: 根据姓名查找员工 (无索引)
EXPLAIN SELECT * FROM tb_employee WHERE emp_name = '张伟';

-- 预期结果关注点:
--   type:       ALL          -> 全表扫描, 性能最差
--   possible_keys: NULL      -> 没有可用索引
--   key:        NULL         -> 未使用索引
--   rows:       ~10000       -> 需要扫描全部行
--   Extra:      Using where  -> 索引未覆盖, 需回表

-- ----------------------------------------------------------
-- 3. 创建单列索引, 用 EXPLAIN 验证效果
-- ----------------------------------------------------------

-- 3.1 为 emp_name 创建普通索引
CREATE INDEX idx_emp_name ON tb_employee(emp_name);

-- 再次分析: 姓名查询
EXPLAIN SELECT * FROM tb_employee WHERE emp_name = '张伟';

-- 预期结果关注点:
--   type:       ref          -> 非唯一索引扫描, 显著优于 ALL
--   possible_keys: idx_emp_name
--   key:        idx_emp_name -> 使用了索引
--   key_len:    202          -> 索引长度 (utf8mb4: 50*4+2)
--   rows:       ~2           -> 扫描行数大幅减少
--   Extra:      NULL         -> 查询列未被索引完全覆盖

-- 3.2 为 dept_id 创建索引 (WHERE 子句常用列)
CREATE INDEX idx_emp_dept ON tb_employee(dept_id);

-- 按部门查询
EXPLAIN SELECT * FROM tb_employee WHERE dept_id = 3;

-- 3.3 为 salary 创建索引 (范围查询场景)
CREATE INDEX idx_emp_salary ON tb_employee(salary);

-- 等值查询
EXPLAIN SELECT * FROM tb_employee WHERE salary = 15000.00;

-- 范围查询 (B+树索引对 >, <, BETWEEN 等范围条件仍然生效)
EXPLAIN SELECT * FROM tb_employee WHERE salary BETWEEN 10000 AND 20000;

-- ----------------------------------------------------------
-- 4. 前缀索引: 节省空间, 权衡精度
-- ----------------------------------------------------------

-- 为 phone 创建前缀索引 (仅索引前 7 位)
CREATE INDEX idx_emp_phone_prefix ON tb_employee(phone(7));

-- 查询
EXPLAIN SELECT * FROM tb_employee WHERE phone = '13812345678';

-- 注意: 前缀索引会导致 rows 增大, 因为前 7 位相同的号码不止一条
-- 这体现了 "时间与空间的矛盾"

-- 删除前缀索引, 创建完整索引做对比
DROP INDEX idx_emp_phone_prefix ON tb_employee;
CREATE INDEX idx_emp_phone ON tb_employee(phone);

EXPLAIN SELECT * FROM tb_employee WHERE phone = '13812345678';
-- 完整索引: rows=1, 扫描更精准

-- ----------------------------------------------------------
-- 5. 复合索引 (联合索引) 与最左前缀原则
-- ----------------------------------------------------------

-- 5.1 创建复合索引: (dept_id, salary)
CREATE INDEX idx_dept_salary ON tb_employee(dept_id, salary);

-- 符合最左前缀 -> 索引生效
EXPLAIN SELECT * FROM tb_employee WHERE dept_id = 3 AND salary > 15000;
-- type: range, key: idx_dept_salary

-- 仅使用最左列 -> 索引生效
EXPLAIN SELECT * FROM tb_employee WHERE dept_id = 5;
-- type: ref, key: idx_dept_salary

-- 跳过最左列, 仅用 salary -> 索引不生效 (违反最左前缀)
EXPLAIN SELECT * FROM tb_employee WHERE salary > 20000;
-- type: ALL, key: NULL

-- 5.2 创建三列复合索引: (dept_id, status, hire_date)
CREATE INDEX idx_dept_status_date ON tb_employee(dept_id, status, hire_date);

-- 完全匹配最左前缀 -> 索引生效
EXPLAIN SELECT * FROM tb_employee
WHERE dept_id = 2 AND status = 1 AND hire_date > '2020-01-01';

-- 范围查询后的列不再使用索引 (MySQL 8.0 Index Skip Scan 除外)
EXPLAIN SELECT * FROM tb_employee
WHERE dept_id = 2 AND hire_date > '2020-01-01';
-- status 是范围条件时, hire_date 不走索引
-- 但如果 status 是等值条件, hire_date 是范围, 则两者都走索引

-- ----------------------------------------------------------
-- 6. 索引覆盖 (Covering Index): 避免回表, 性能最优
-- ----------------------------------------------------------

-- 覆盖索引: 查询的列全部在索引中, 无需回表读取数据行
-- Extra 显示 "Using index" 表示索引覆盖

-- 场景: 只查询部门ID和薪资 (这两列已在 idx_dept_salary 中)
EXPLAIN SELECT dept_id, salary FROM tb_employee WHERE dept_id = 3;
-- Extra: Using index  -> 索引覆盖, 性能最佳

-- 对比: 查询所有列 (需要回表)
EXPLAIN SELECT * FROM tb_employee WHERE dept_id = 3;
-- Extra: NULL  -> 需要回表查询完整行

-- ----------------------------------------------------------
-- 7. EXPLAIN 各字段详解 (企业性能调优必备)
-- ----------------------------------------------------------

-- 7.1 select_type 查询类型
--   SIMPLE:    简单查询, 无子查询/UNION
--   PRIMARY:   最外层查询 (含子查询时)
--   SUBQUERY:  子查询中的第一个 SELECT
--   DERIVED:   FROM 子句中的子查询 (派生表)
--   UNION:     UNION 中第二个及之后的 SELECT

-- 示例: 子查询
EXPLAIN
SELECT * FROM tb_employee
WHERE dept_id IN (
    SELECT dept_id FROM tb_employee WHERE salary > 30000
);

-- 7.2 type 访问类型 (性能从差到好)
--   ALL        全表扫描 (最差)
--   index      索引全扫描
--   range      索引范围扫描
--   ref        非唯一索引扫描
--   eq_ref     唯一索引扫描 (JOIN 主键/唯一索引)
--   const      常量查询 (主键/唯一索引等值)
--   system     系统表 (最好)

-- const 示例: 主键等值查询
EXPLAIN SELECT * FROM tb_employee WHERE emp_id = 100;
-- type: const, 最优

-- range 示例: 索引范围扫描
EXPLAIN SELECT * FROM tb_employee WHERE emp_id BETWEEN 100 AND 200;
-- type: range

-- 7.3 key_len 计算规则
--   INT:       4 字节 + 1 (NULL标志) = 5
--   VARCHAR(N): N * 字符集字节数 + 2 (长度前缀) + 1 (NULL标志)
--   utf8mb4: 每字符 4 字节
--   例: VARCHAR(50) NOT NULL -> 50*4 + 2 = 202

-- 7.4 Extra 常见值
--   Using index       索引覆盖 (最佳)
--   Using where       需回表过滤
--   Using filesort    额外排序 (应优化)
--   Using temporary   使用临时表 (应优化)
--   Using index condition  索引条件下推 (ICP)

-- Using filesort 示例: ORDER BY 无索引列
EXPLAIN SELECT * FROM tb_employee WHERE dept_id = 1 ORDER BY salary;
-- 如果 (dept_id, salary) 复合索引存在, 则不会 filesort

-- ----------------------------------------------------------
-- 8. 索引失效的常见场景 (企业踩坑指南)
-- ----------------------------------------------------------

-- 8.1 对索引列使用函数 -> 索引失效
EXPLAIN SELECT * FROM tb_employee WHERE YEAR(hire_date) = 2022;
-- type: ALL, 索引失效

-- 正确写法: 将函数应用到值上, 保持列"干净"
EXPLAIN SELECT * FROM tb_employee
WHERE hire_date >= '2022-01-01' AND hire_date < '2023-01-01';
-- type: range, 索引生效

-- 8.2 隐式类型转换 -> 索引失效
-- phone 是 VARCHAR, 传入 INT 会导致隐式转换
EXPLAIN SELECT * FROM tb_employee WHERE phone = 13812345678;
-- type: ALL, 索引失效 (数字与字符串比较)

-- 正确写法: 传入字符串
EXPLAIN SELECT * FROM tb_employee WHERE phone = '13812345678';
-- type: ref, 索引生效

-- 8.3 LIKE 以通配符开头 -> 索引失效
EXPLAIN SELECT * FROM tb_employee WHERE emp_name LIKE '%伟';
-- type: ALL, 索引失效

-- 不以通配符开头 -> 索引生效
EXPLAIN SELECT * FROM tb_employee WHERE emp_name LIKE '张%';
-- type: range, 索引生效

-- 8.4 OR 连接非索引列 -> 索引失效
EXPLAIN SELECT * FROM tb_employee WHERE emp_name = '张伟' OR remark = 'test';
-- remark 无索引, 可能导致全表扫描

-- 8.5 使用 NOT / <> / != -> 可能导致索引失效
EXPLAIN SELECT * FROM tb_employee WHERE salary <> 15000;
-- 优化器可能放弃索引, 选择全表扫描

-- 8.6 IS NULL / IS NOT NULL -> 视数据分布而定
EXPLAIN SELECT * FROM tb_employee WHERE phone IS NOT NULL;
-- 若大部分行非 NULL, 优化器可能选择全表扫描

-- ----------------------------------------------------------
-- 9. 函数索引 (MySQL 8.0+)
-- ----------------------------------------------------------

-- MySQL 8.0 支持函数索引, 对表达式建立索引
CREATE INDEX idx_emp_name_lower ON tb_employee((LOWER(emp_name)));

-- 即使使用函数, 索引也能生效
EXPLAIN SELECT * FROM tb_employee WHERE LOWER(emp_name) = '张伟';
-- type: ref, key: idx_emp_name_lower

-- ----------------------------------------------------------
-- 10. 索引管理操作汇总
-- ----------------------------------------------------------

-- 查看表上所有索引
SHOW INDEX FROM tb_employee;

-- 删除索引的两种方式
-- 方式一: ALTER TABLE
-- ALTER TABLE tb_employee DROP INDEX idx_emp_phone;

-- 方式二: DROP INDEX
-- DROP INDEX idx_emp_phone ON tb_employee;

-- 创建唯一索引 (列值不允许重复)
-- CREATE UNIQUE INDEX uk_emp_email ON tb_employee(email);

-- ----------------------------------------------------------
-- 11. 企业级优化建议 (总结)
-- ----------------------------------------------------------

-- [原则1] WHERE 子句和 JOIN 条件中的列最适合建索引
-- [原则2] 基数大 (区分度高) 的列索引效果更好
--         例: phone (几乎唯一) > status (仅 0/1)
-- [原则3] 前缀索引可节省空间, 但会降低精度
-- [原则4] 索引不是越多越好: 加速读, 拖慢写
-- [原则5] 主键尽量用短类型 (INT 优于 BIGINT), InnoDB
--         二级索引叶子节点存储主键值, 主键越短索引越小
-- [原则6] 利用复合索引实现索引覆盖, 减少回表
-- [原则7] 保持索引列"干净": 不加函数, 不做隐式转换

-- 清理 (可选)
-- DROP DATABASE IF EXISTS demo_index;
