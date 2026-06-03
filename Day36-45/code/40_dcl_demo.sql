-- ============================================================================
-- DCL (Data Control Language) 演示脚本
-- 数据控制语言用于管理数据库用户权限，确保数据安全
-- 适用数据库: MySQL 8.0+
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 第一部分: 用户管理 (User Management)
-- ----------------------------------------------------------------------------

-- 1. 创建用户 - 允许从任意主机访问
CREATE USER 'wangdachui'@'%' IDENTIFIED BY 'Wang.618';

-- 2. 删除已有用户后重建 - 限制只能从指定网段访问
DROP USER IF EXISTS 'wangdachui'@'%';
CREATE USER 'wangdachui'@'192.168.0.%' IDENTIFIED BY 'Wang.618';

-- 3. 修改用户密码
ALTER USER 'wangdachui'@'192.168.0.%' IDENTIFIED BY 'Wang.618New';

-- 4. 锁定/解锁用户账户 (MySQL 8.0+)
ALTER USER 'wangdachui'@'192.168.0.%' ACCOUNT LOCK;
ALTER USER 'wangdachui'@'192.168.0.%' ACCOUNT UNLOCK;

-- 5. 删除用户
DROP USER IF EXISTS 'wangdachui'@'192.168.0.%';

-- ----------------------------------------------------------------------------
-- 第二部分: 权限授予 (GRANT)
-- ----------------------------------------------------------------------------

-- 1. 授予单表查询权限
GRANT SELECT ON `school`.`tb_college` TO 'wangdachui'@'192.168.0.%';

-- 2. 授予整个数据库的查询权限
GRANT SELECT ON `school`.* TO 'wangdachui'@'192.168.0.%';

-- 3. 授予多种 DML 权限 (增删改查)
GRANT INSERT, DELETE, UPDATE ON `school`.* TO 'wangdachui'@'192.168.0.%';

-- 4. 授予 DDL 权限 (创建、删除、修改表结构)
GRANT CREATE, DROP, ALTER ON `school`.* TO 'wangdachui'@'192.168.0.%';

-- 5. 授予所有权限 (慎用，生产环境不推荐)
GRANT ALL PRIVILEGES ON *.* TO 'wangdachui'@'192.168.0.%';

-- ----------------------------------------------------------------------------
-- 第三部分: 权限召回 (REVOKE)
-- ----------------------------------------------------------------------------

-- 1. 召回特定权限
REVOKE INSERT, DELETE, UPDATE ON `school`.* FROM 'wangdachui'@'192.168.0.%';

-- 2. 召回所有权限
REVOKE ALL PRIVILEGES ON *.* FROM 'wangdachui'@'192.168.0.%';

-- 3. 刷新权限缓存，使权限变更立即生效
FLUSH PRIVILEGES;

-- ----------------------------------------------------------------------------
-- 第四部分: 角色管理 (Roles) - MySQL 8.0+
-- 角色是命名的权限集合，简化多用户权限管理
-- ----------------------------------------------------------------------------

-- 1. 创建角色
CREATE ROLE 'app_readonly', 'app_developer', 'app_admin';

-- 2. 为角色授予权限

-- 只读角色: 仅允许查询操作
GRANT SELECT ON `school`.* TO 'app_readonly';

-- 开发者角色: 允许 DML 操作 (增删改查) + 创建临时表
GRANT SELECT, INSERT, UPDATE, DELETE ON `school`.* TO 'app_developer';
GRANT CREATE TEMPORARY TABLES ON `school`.* TO 'app_developer';

-- 管理员角色: 允许所有操作
GRANT ALL PRIVILEGES ON `school`.* TO 'app_admin';

-- 3. 将角色分配给用户
GRANT 'app_readonly' TO 'wangdachui'@'192.168.0.%';

-- 4. 设置默认角色 (登录时自动激活)
SET DEFAULT ROLE 'app_readonly' TO 'wangdachui'@'192.168.0.%';

-- 5. 激活当前会话的所有角色
SET GLOBAL activate_all_roles_on_login = ON;

-- ----------------------------------------------------------------------------
-- 第五部分: 企业级用户配置示例
-- 模拟真实企业环境中不同角色的用户配置
-- ----------------------------------------------------------------------------

-- ========================
-- 场景: 公司数据库服务器，运行着 school 管理系统
-- 需要配置三类用户: 管理员、开发者、只读用户
-- ========================

-- 清理已有用户 (便于重复执行)
DROP USER IF EXISTS 'admin_zhangsan'@'10.0.1.%';
DROP USER IF EXISTS 'dev_lisi'@'10.0.2.%';
DROP USER IF EXISTS 'dev_wangwu'@'10.0.2.%';
DROP USER IF EXISTS 'readonly_report'@'10.0.3.%';

-- ---------------------
-- A. 管理员用户配置
-- 负责数据库的日常维护、备份、用户管理
-- ---------------------
CREATE USER 'admin_zhangsan'@'10.0.1.%'
    IDENTIFIED BY 'Admin@2024!Secure'
    PASSWORD EXPIRE INTERVAL 90 DAY        -- 密码90天过期
    FAILED_LOGIN_ATTEMPTS 5                -- 5次登录失败后锁定
    PASSWORD_LOCK_TIME 1;                  -- 锁定1天

-- 授予管理员角色
GRANT 'app_admin' TO 'admin_zhangsan'@'10.0.1.%';
SET DEFAULT ROLE 'app_admin' TO 'admin_zhangsan'@'10.0.1.%';

-- 额外授予用户管理权限
GRANT CREATE USER ON *.* TO 'admin_zhangsan'@'10.0.1.%';
GRANT GRANT OPTION ON `school`.* TO 'admin_zhangsan'@'10.0.1.%';

-- ---------------------
-- B. 开发者用户配置
-- 负责应用开发、调试、数据修复
-- ---------------------
CREATE USER 'dev_lisi'@'10.0.2.%'
    IDENTIFIED BY 'Dev@2024!Pass'
    PASSWORD EXPIRE INTERVAL 180 DAY;

CREATE USER 'dev_wangwu'@'10.0.2.%'
    IDENTIFIED BY 'Dev@2024!Pass2'
    PASSWORD EXPIRE INTERVAL 180 DAY;

-- 授予开发者角色
GRANT 'app_developer' TO 'dev_lisi'@'10.0.2.%';
GRANT 'app_developer' TO 'dev_wangwu'@'10.0.2.%';
SET DEFAULT ROLE 'app_developer' TO 'dev_lisi'@'10.0.2.%';
SET DEFAULT ROLE 'app_developer' TO 'dev_wangwu'@'10.0.2.%';

-- 开发者额外权限: 查看执行计划、创建视图
GRANT SHOW VIEW ON `school`.* TO 'dev_lisi'@'10.0.2.%';
GRANT SHOW VIEW ON `school`.* TO 'dev_wangwu'@'10.0.2.%';

-- ---------------------
-- C. 只读用户配置
-- 用于报表系统、数据分析、BI工具等
-- ---------------------
CREATE USER 'readonly_report'@'10.0.3.%'
    IDENTIFIED BY 'Read@2024!Only'
    PASSWORD EXPIRE INTERVAL 365 DAY;      -- 只读账户密码有效期较长

-- 授予只读角色
GRANT 'app_readonly' TO 'readonly_report'@'10.0.3.%';
SET DEFAULT ROLE 'app_readonly' TO 'readonly_report'@'10.0.3.%';

-- 刷新权限使所有配置生效
FLUSH PRIVILEGES;

-- ----------------------------------------------------------------------------
-- 第六部分: 权限查询与审计
-- ----------------------------------------------------------------------------

-- 1. 查看当前用户的权限
SHOW GRANTS;

-- 2. 查看指定用户的权限
SHOW GRANTS FOR 'admin_zhangsan'@'10.0.1.%';
SHOW GRANTS FOR 'dev_lisi'@'10.0.2.%';
SHOW GRANTS FOR 'readonly_report'@'10.0.3.%';

-- 3. 查看指定用户的角色权限
SHOW GRANTS FOR 'admin_zhangsan'@'10.0.1.%' USING 'app_admin';

-- 4. 列出所有用户
SELECT user, host, account_locked, password_expired
FROM mysql.user
ORDER BY user;

-- 5. 列出所有角色
SELECT * FROM mysql.user WHERE is_role = 'Y';

-- ----------------------------------------------------------------------------
-- 第七部分: 权限回收与清理示例
-- ----------------------------------------------------------------------------

-- 1. 召回开发者的 DELETE 权限 (发现误操作风险)
REVOKE DELETE ON `school`.* FROM 'dev_lisi'@'10.0.2.%';

-- 2. 从角色中回收权限 (影响所有拥有该角色的用户)
REVOKE DELETE ON `school`.* FROM 'app_developer';

-- 3. 回收用户的角色
REVOKE 'app_developer' FROM 'dev_wangwu'@'10.0.2.%';

-- 4. 删除角色
DROP ROLE IF EXISTS 'app_temp';

-- 5. 删除离职员工账户
DROP USER IF EXISTS 'dev_wangwu'@'10.0.2.%';

-- 刷新权限
FLUSH PRIVILEGES;

-- ----------------------------------------------------------------------------
-- 第八部分: 最佳实践总结
-- ----------------------------------------------------------------------------
--
-- 1. 最小权限原则: 只授予用户完成工作所需的最小权限
-- 2. 使用角色管理: 通过角色批量管理权限，而非逐个用户授权
-- 3. 限制主机来源: 避免使用 '%' 通配符，指定具体的 IP 或网段
-- 4. 密码策略: 设置密码过期时间、失败尝试次数、锁定策略
-- 5. 定期审计: 定期检查用户权限，及时回收不必要的权限
-- 6. 避免 GRANT OPTION 滥用: 仅授予管理员 GRANT OPTION
-- 7. 生产环境禁止 ALL PRIVILEGES: 除非绝对必要
-- 8. 及时清理: 员工离职或项目结束后，及时删除相关账户
-- 9. FLUSH PRIVILEGES: 权限变更后务必刷新缓存
-- 10. 记录变更: 所有权限变更应有文档记录和审批流程
-- ============================================================================
