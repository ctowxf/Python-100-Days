-- ============================================================
-- Day 36: 关系型数据库和 MySQL 概述 - 示例 SQL
-- ============================================================
-- 本文件演示：
--   1. 数据库基本概念（DDL / DML / DCL / TCL）
--   2. 创建数据库与数据表
--   3. 企业级公司（Company）数据库模式设计
-- ============================================================

-- ************************************************************
-- 第一部分：数据库基本操作（DDL - 数据定义语言）
-- ************************************************************

-- 查看当前服务器上所有数据库
SHOW DATABASES;

-- 查看支持的字符集（utf8mb4 支持完整的 Unicode，包括 emoji）
SHOW CHARACTER SET;

-- 查看支持的存储引擎（InnoDB 是默认引擎，支持事务和外键）
SHOW ENGINES;

-- 创建一个新的数据库，指定字符集和排序规则
-- IF NOT EXISTS 可防止重复创建时报错
DROP DATABASE IF EXISTS company_demo;
CREATE DATABASE company_demo
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_general_ci;

-- 切换到新创建的数据库
USE company_demo;


-- ************************************************************
-- 第二部分：企业级 Company 数据库模式设计
-- ************************************************************
-- ER 模型思路：
--   - 部门（Department） 1:N 员工（Employee）
--   - 员工（Employee） N:1 职位（Job）
--   - 员工（Employee） M:N 项目（Project） 通过中间表关联
-- ************************************************************

-- ------------------------------------------------------------
-- 2.1 部门表（Department）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_dept (
    dept_id     INT UNSIGNED  AUTO_INCREMENT  COMMENT '部门编号（主键）',
    dept_name   VARCHAR(50)   NOT NULL        COMMENT '部门名称',
    location    VARCHAR(100)  DEFAULT NULL    COMMENT '部门所在地',
    create_time DATETIME      DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                                COMMENT '最后更新时间',
    PRIMARY KEY (dept_id),
    UNIQUE KEY uk_dept_name (dept_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='部门表';

-- ------------------------------------------------------------
-- 2.2 职位表（Job）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_job (
    job_id      INT UNSIGNED  AUTO_INCREMENT  COMMENT '职位编号（主键）',
    job_title   VARCHAR(80)   NOT NULL        COMMENT '职位名称',
    min_salary  DECIMAL(10,2) DEFAULT NULL    COMMENT '该职位最低薪资',
    max_salary  DECIMAL(10,2) DEFAULT NULL    COMMENT '该职位最高薪资',
    PRIMARY KEY (job_id),
    UNIQUE KEY uk_job_title (job_title)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='职位表';

-- ------------------------------------------------------------
-- 2.3 员工表（Employee）
--   - 外键 dept_id 关联 tb_dept
--   - 外键 job_id  关联 tb_job
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_emp (
    emp_id      INT UNSIGNED   AUTO_INCREMENT COMMENT '员工编号（主键）',
    emp_name    VARCHAR(50)    NOT NULL       COMMENT '员工姓名',
    gender      ENUM('M','F')  DEFAULT 'M'    COMMENT '性别：M-男 F-女',
    birthday    DATE           DEFAULT NULL   COMMENT '出生日期',
    email       VARCHAR(100)   DEFAULT NULL   COMMENT '电子邮箱',
    phone       VARCHAR(20)    DEFAULT NULL   COMMENT '手机号码',
    salary      DECIMAL(10,2)  DEFAULT 0.00   COMMENT '月薪',
    dept_id     INT UNSIGNED   DEFAULT NULL   COMMENT '所属部门编号',
    job_id      INT UNSIGNED   DEFAULT NULL   COMMENT '职位编号',
    manager_id  INT UNSIGNED   DEFAULT NULL   COMMENT '直属上级员工编号',
    hire_date   DATE           NOT NULL       COMMENT '入职日期',
    create_time DATETIME       DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME       DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                               COMMENT '最后更新时间',
    PRIMARY KEY (emp_id),
    UNIQUE KEY uk_emp_email (email),
    KEY idx_emp_dept (dept_id),
    KEY idx_emp_job  (job_id),
    CONSTRAINT fk_emp_dept
        FOREIGN KEY (dept_id) REFERENCES tb_dept(dept_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_emp_job
        FOREIGN KEY (job_id)  REFERENCES tb_job(job_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_emp_manager
        FOREIGN KEY (manager_id) REFERENCES tb_emp(emp_id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='员工表';

-- ------------------------------------------------------------
-- 2.4 项目表（Project）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_project (
    proj_id     INT UNSIGNED   AUTO_INCREMENT COMMENT '项目编号（主键）',
    proj_name   VARCHAR(100)   NOT NULL       COMMENT '项目名称',
    start_date  DATE           DEFAULT NULL   COMMENT '项目开始日期',
    end_date    DATE           DEFAULT NULL   COMMENT '项目结束日期',
    budget      DECIMAL(12,2)  DEFAULT 0.00   COMMENT '项目预算',
    create_time DATETIME       DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (proj_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目表';

-- ------------------------------------------------------------
-- 2.5 员工-项目关联表（多对多关系 M:N）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_emp_project (
    emp_id      INT UNSIGNED  NOT NULL COMMENT '员工编号',
    proj_id     INT UNSIGNED  NOT NULL COMMENT '项目编号',
    role        VARCHAR(50)   DEFAULT NULL COMMENT '在该项目中担任的角色',
    join_date   DATE          DEFAULT NULL COMMENT '加入项目日期',
    PRIMARY KEY (emp_id, proj_id),
    CONSTRAINT fk_ep_emp
        FOREIGN KEY (emp_id)  REFERENCES tb_emp(emp_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ep_proj
        FOREIGN KEY (proj_id) REFERENCES tb_project(proj_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='员工与项目的多对多关联表';


-- ************************************************************
-- 第三部分：DML - 数据操作语言（插入、查询、更新、删除）
-- ************************************************************

-- ------------------------------------------------------------
-- 3.1 向部门表插入示例数据
-- ------------------------------------------------------------
INSERT INTO tb_dept (dept_name, location) VALUES
    ('总裁办',   '北京'),
    ('研发部',   '上海'),
    ('市场部',   '广州'),
    ('人力资源', '北京'),
    ('财务部',   '上海');

-- ------------------------------------------------------------
-- 3.2 向职位表插入示例数据
-- ------------------------------------------------------------
INSERT INTO tb_job (job_title, min_salary, max_salary) VALUES
    ('总经理',   30000.00, 80000.00),
    ('技术总监', 25000.00, 60000.00),
    ('高级工程师', 15000.00, 35000.00),
    ('初级工程师',  6000.00, 15000.00),
    ('市场经理',  12000.00, 30000.00),
    ('HR专员',    5000.00, 12000.00),
    ('会计',      6000.00, 15000.00);

-- ------------------------------------------------------------
-- 3.3 向员工表插入示例数据
-- ------------------------------------------------------------
INSERT INTO tb_emp
    (emp_name, gender, birthday, email, phone, salary, dept_id, job_id, manager_id, hire_date)
VALUES
    ('张三', 'M', '1975-03-15', 'zhangsan@company.com',  '13800001111', 50000.00, 1, 1, NULL, '2005-06-01'),
    ('李四', 'M', '1980-07-22', 'lisi@company.com',      '13800002222', 35000.00, 2, 2, 1,   '2010-03-15'),
    ('王芳', 'F', '1990-11-05', 'wangfang@company.com',  '13800003333', 18000.00, 2, 3, 2,   '2018-07-01'),
    ('赵磊', 'M', '1995-01-20', 'zhaolei@company.com',   '13800004444', 10000.00, 2, 4, 2,   '2022-09-01'),
    ('刘梅', 'F', '1988-05-30', 'liumei@company.com',    '13800005555', 20000.00, 3, 5, 1,   '2016-04-10'),
    ('陈伟', 'M', '1992-09-18', 'chenwei@company.com',   '13800006666',  8000.00, 4, 6, 1,   '2020-01-15'),
    ('孙丽', 'F', '1993-12-01', 'sunli@company.com',     '13800007777',  9500.00, 5, 7, 1,   '2019-06-20');

-- ------------------------------------------------------------
-- 3.4 向项目表插入示例数据
-- ------------------------------------------------------------
INSERT INTO tb_project (proj_name, start_date, end_date, budget) VALUES
    ('企业官网改版',     '2025-01-01', '2025-06-30', 500000.00),
    ('移动端 App 开发',  '2025-03-15', '2025-12-31', 1200000.00),
    ('数据中台建设',     '2025-06-01', '2026-06-01', 2000000.00);

-- ------------------------------------------------------------
-- 3.5 向员工-项目关联表插入数据
-- ------------------------------------------------------------
INSERT INTO tb_emp_project (emp_id, proj_id, role, join_date) VALUES
    (2, 1, '项目负责人', '2025-01-01'),
    (3, 1, '前端开发',   '2025-01-15'),
    (4, 1, '后端开发',   '2025-01-15'),
    (2, 2, '技术顾问',   '2025-03-15'),
    (3, 2, '移动端开发', '2025-03-15'),
    (5, 3, '项目经理',   '2025-06-01'),
    (3, 3, '数据工程师', '2025-06-15');


-- ************************************************************
-- 第四部分：DQL - 数据查询语言（SELECT）
-- ************************************************************

-- 4.1 查询所有员工信息
SELECT * FROM tb_emp;

-- 4.2 查询员工姓名、月薪，并按月薪降序排列
SELECT emp_name, salary
FROM tb_emp
ORDER BY salary DESC;

-- 4.3 连接查询：员工及其所属部门和职位
SELECT
    e.emp_id,
    e.emp_name    AS '姓名',
    d.dept_name   AS '部门',
    j.job_title   AS '职位',
    e.salary      AS '月薪',
    e.hire_date   AS '入职日期'
FROM tb_emp e
LEFT JOIN tb_dept d ON e.dept_id = d.dept_id
LEFT JOIN tb_job  j ON e.job_id  = j.job_id
ORDER BY d.dept_id, e.salary DESC;

-- 4.4 统计每个部门的员工人数和平均薪资
SELECT
    d.dept_name           AS '部门',
    COUNT(e.emp_id)       AS '员工人数',
    ROUND(AVG(e.salary), 2) AS '平均薪资'
FROM tb_dept d
LEFT JOIN tb_emp e ON d.dept_id = e.dept_id
GROUP BY d.dept_id, d.dept_name
ORDER BY 平均薪资 DESC;

-- 4.5 查询参与项目数量 >= 2 的员工
SELECT
    e.emp_name   AS '姓名',
    COUNT(ep.proj_id) AS '参与项目数'
FROM tb_emp e
JOIN tb_emp_project ep ON e.emp_id = ep.emp_id
GROUP BY e.emp_id, e.emp_name
HAVING COUNT(ep.proj_id) >= 2;

-- 4.6 子查询：查找薪资高于公司平均薪资的员工
SELECT emp_name, salary
FROM tb_emp
WHERE salary > (SELECT AVG(salary) FROM tb_emp);


-- ************************************************************
-- 第五部分：DML - 更新与删除
-- ************************************************************

-- 5.1 将赵磊的薪资调整为 12000（晋升调薪）
UPDATE tb_emp
SET salary = 12000.00
WHERE emp_name = '赵磊';

-- 5.2 删除某条项目关联记录
DELETE FROM tb_emp_project
WHERE emp_id = 4 AND proj_id = 1;


-- ************************************************************
-- 第六部分：DCL - 数据控制语言（用户与权限管理）
-- ************************************************************

-- 6.1 创建一个只读用户，仅允许查询 company_demo 库
CREATE USER IF NOT EXISTS 'reader'@'localhost'
    IDENTIFIED BY 'Read@2025';

GRANT SELECT ON company_demo.*
    TO 'reader'@'localhost';

-- 6.2 创建一个应用账号，允许增删改查，但不允许修改表结构
CREATE USER IF NOT EXISTS 'app_user'@'localhost'
    IDENTIFIED BY 'App@2025';

GRANT SELECT, INSERT, UPDATE, DELETE ON company_demo.*
    TO 'app_user'@'localhost';

-- 6.3 刷新权限，使授权立即生效
FLUSH PRIVILEGES;


-- ************************************************************
-- 第七部分：TCL - 事务控制语言
-- ************************************************************

-- 事务示例：批量调整研发部员工薪资（全部成功或全部回滚）
START TRANSACTION;

    UPDATE tb_emp
    SET salary = salary * 1.10
    WHERE dept_id = (SELECT dept_id FROM tb_dept WHERE dept_name = '研发部');

    -- 验证更新结果
    SELECT emp_name, salary FROM tb_emp
    WHERE dept_id = (SELECT dept_id FROM tb_dept WHERE dept_name = '研发部');

    -- 如果结果正确则提交
    COMMIT;
    -- 如果需要回滚，使用：ROLLBACK;


-- ************************************************************
-- 第八部分：清理（可选，按需执行）
-- ************************************************************

-- 取消注释以下语句可删除整个演示数据库：
-- DROP DATABASE IF EXISTS company_demo;
