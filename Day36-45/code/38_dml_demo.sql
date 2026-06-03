-- ============================================================
-- SQL DML (Data Manipulation Language) 完整演示
-- 涵盖：INSERT、UPDATE、DELETE、REPLACE、事务处理
-- 企业级案例：批量数据导入、订单处理事务、库存更新
-- ============================================================

-- 切换到 school 数据库
USE `school`;

-- ============================================================
-- 第一部分：INSERT 操作
-- ============================================================

-- ----------------------------------------------------------
-- 1.1 插入单行数据（完整行）
-- ----------------------------------------------------------
-- 当主键为自增字段时，使用 DEFAULT 占位
INSERT INTO `tb_college`
VALUES
    (DEFAULT, '计算机学院', '学习计算机科学与技术的地方');

-- ----------------------------------------------------------
-- 1.2 插入单行数据（指定列，推荐做法）
-- ----------------------------------------------------------
-- 显式列出列名，不依赖建表时的列顺序，可读性更好
INSERT INTO `tb_college` (`col_name`, `col_intro`)
VALUES
    ('外国语学院', '学习歪果仁的语言的学院');

-- ----------------------------------------------------------
-- 1.3 批量插入多行数据
-- ----------------------------------------------------------
-- VALUES 后跟多个元组，一次插入多条记录，效率更高
INSERT INTO `tb_college`
    (`col_name`, `col_intro`)
VALUES
    ('经济管理学院', '经世济民，治理国家；管理科学，兴国之道'),
    ('体育学院', '发展体育运动，增强人民体质'),
    ('艺术学院', '培养艺术素养与创造力');

-- ----------------------------------------------------------
-- 1.4 通过子查询插入数据（INSERT ... SELECT）
-- ----------------------------------------------------------
-- 从临时表查询数据并插入到目标表
-- 假设存在一张 tb_temp 表，包含 col_name 和 col_intro 两列
-- INSERT INTO `tb_college`
--     (`col_name`, `col_intro`)
-- SELECT `col_name`, `col_intro`
--   FROM `tb_temp`
--  WHERE `col_name` IS NOT NULL;

-- ----------------------------------------------------------
-- 1.5 降低 INSERT 优先级（不影响 SELECT 性能）
-- ----------------------------------------------------------
-- 在业务高峰期，用 LOW_PRIORITY 避免写操作阻塞读操作
-- INSERT LOW_PRIORITY INTO `tb_college` (`col_name`, `col_intro`)
-- VALUES ('医学院', '培养医疗卫生人才');


-- ============================================================
-- 第二部分：UPDATE 操作
-- ============================================================

-- ----------------------------------------------------------
-- 2.1 更新单个字段
-- ----------------------------------------------------------
-- 注意：WHERE 子句用于限定范围，使用主键定位最精确
-- 切勿省略 WHERE，否则会更新全表所有行
UPDATE `tb_student`
   SET `stu_name` = '杨逍'
 WHERE `stu_id` = 1001;

-- ----------------------------------------------------------
-- 2.2 同时更新多个字段
-- ----------------------------------------------------------
-- 在 SET 后用逗号分隔多个字段赋值
UPDATE `tb_student`
   SET `stu_name` = '杨逍'
     , `stu_birth` = '1975-12-29'
     , `stu_addr` = '四川成都'
 WHERE `stu_id` = 1001;

-- ----------------------------------------------------------
-- 2.3 使用表达式更新字段
-- ----------------------------------------------------------
-- 给所有学生的成绩加 5 分（但不超过 100 分）
UPDATE `tb_record`
   SET `score` = LEAST(`score` + 5, 100)
 WHERE `score` IS NOT NULL
   AND `cou_id` = 1111;

-- ----------------------------------------------------------
-- 2.4 使用子查询更新数据
-- ----------------------------------------------------------
-- 将选修了"Python程序设计"课程且成绩为空的学生记录，设置成绩为 0
UPDATE `tb_record`
   SET `score` = 0
 WHERE `cou_id` = 1111
   AND `score` IS NULL;

-- ----------------------------------------------------------
-- 2.5 使用 CASE WHEN 进行条件批量更新
-- ----------------------------------------------------------
-- 根据成绩等级批量更新备注信息（假设表中有 remark 字段）
-- UPDATE `tb_record`
--    SET `remark` = CASE
--        WHEN `score` >= 90 THEN '优秀'
--        WHEN `score` >= 80 THEN '良好'
--        WHEN `score` >= 60 THEN '及格'
--        ELSE '不及格'
--    END
--  WHERE `score` IS NOT NULL;


-- ============================================================
-- 第三部分：DELETE 操作
-- ============================================================

-- ----------------------------------------------------------
-- 3.1 删除指定行
-- ----------------------------------------------------------
-- 必须带 WHERE 子句，精确指定要删除的行
DELETE
  FROM `tb_college`
 WHERE `col_id` = 5;

-- ----------------------------------------------------------
-- 3.2 按条件批量删除
-- ----------------------------------------------------------
-- 删除所有未录入成绩的选课记录
DELETE
  FROM `tb_record`
 WHERE `score` IS NULL;

-- ----------------------------------------------------------
-- 3.3 使用子查询删除数据
-- ----------------------------------------------------------
-- 删除"体育学院"下所有学生的选课记录
DELETE
  FROM `tb_record`
 WHERE `stu_id` IN (
     SELECT `stu_id`
       FROM `tb_student`
      WHERE `col_id` = (
          SELECT `col_id`
            FROM `tb_college`
           WHERE `col_name` = '体育学院'
      )
 );

-- ----------------------------------------------------------
-- 3.4 删除全表数据（危险操作！）
-- ----------------------------------------------------------
-- DELETE FROM `tb_record`;   -- 删除所有行，AUTO_INCREMENT 不重置
-- TRUNCATE TABLE `tb_record`; -- 删除所有行且重置 AUTO_INCREMENT，更快但不可恢复

-- ----------------------------------------------------------
-- 3.5 使用 LIMIT 限制删除行数
-- ----------------------------------------------------------
-- 分批删除，避免一次性删除大量数据导致锁表
DELETE
  FROM `tb_record`
 WHERE `sel_date` < '2017-01-01'
 LIMIT 1000;


-- ============================================================
-- 第四部分：REPLACE 操作
-- ============================================================
-- REPLACE 的工作逻辑：
--   如果插入的数据与已有记录的主键或唯一索引冲突，
--   则先删除旧行，再插入新行；否则直接插入。

-- ----------------------------------------------------------
-- 4.1 基本 REPLACE 用法
-- ----------------------------------------------------------
-- 若 tea_id=1122 已存在则替换，否则新增
REPLACE INTO `tb_teacher` (`tea_id`, `tea_name`, `tea_title`, `col_id`)
VALUES (1122, '张三丰', '名誉教授', 1);

-- ----------------------------------------------------------
-- 4.2 REPLACE 用于数据同步/更新
-- ----------------------------------------------------------
-- 场景：从外部系统同步教师数据，存在则更新，不存在则插入
REPLACE INTO `tb_teacher` (`tea_id`, `tea_name`, `tea_title`, `col_id`)
VALUES
    (1122, '张三丰', '终身教授', 1),
    (1133, '宋远桥', '教授', 1),
    (9988, '灭绝师太', '教授', 2);  -- 新教师，直接插入


-- ============================================================
-- 第五部分：事务（Transaction）
-- ============================================================
-- 事务的 ACID 特性：
--   A - 原子性（Atomicity）：事务中的操作要么全部成功，要么全部回滚
--   C - 一致性（Consistency）：事务前后数据库保持一致状态
--   I - 隔离性（Isolation）：并发事务之间互不干扰
--   D - 持久性（Durability）：事务提交后数据永久保存

-- ----------------------------------------------------------
-- 5.1 事务基本语法
-- ----------------------------------------------------------
-- START TRANSACTION / BEGIN   -- 开启事务
-- COMMIT                      -- 提交事务
-- ROLLBACK                    -- 回滚事务
-- SAVEPOINT <name>            -- 设置保存点
-- ROLLBACK TO SAVEPOINT <name> -- 回滚到保存点

-- ----------------------------------------------------------
-- 5.2 示例：学生成绩录入（原子操作）
-- ----------------------------------------------------------
-- 确保一条选课记录的成绩录入和关联操作要么全部成功，要么全部失败
START TRANSACTION;

    -- 步骤1：插入一条新的选课记录
    INSERT INTO `tb_record` (`stu_id`, `cou_id`, `sel_date`, `score`)
    VALUES (1001, 8888, CURDATE(), NULL);

    -- 步骤2：更新课程的选课人数统计（假设表中存在该字段）
    -- UPDATE `tb_course`
    --    SET `cou_count` = `cou_count` + 1
    --  WHERE `cou_id` = 8888;

    -- 验证操作无误后提交
COMMIT;

-- 如果过程中出现异常，则回滚
-- ROLLBACK;


-- ============================================================
-- 第六部分：企业级综合案例
-- ============================================================

-- ----------------------------------------------------------
-- 案例一：批量数据导入
-- 场景：新学期开始，需要从外部系统批量导入学生数据
-- ----------------------------------------------------------

-- 创建临时暂存表
DROP TABLE IF EXISTS `tb_student_staging`;
CREATE TEMPORARY TABLE `tb_student_staging` (
    `stu_id`      INT         NOT NULL,
    `stu_name`    VARCHAR(20) NOT NULL,
    `stu_sex`     TINYINT     DEFAULT 0,
    `stu_birth`   DATE        DEFAULT NULL,
    `stu_addr`    VARCHAR(255) DEFAULT NULL,
    `col_id`      INT         NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 第一步：将外部数据加载到暂存表（批量插入，高效）
INSERT INTO `tb_student_staging`
    (`stu_id`, `stu_name`, `stu_sex`, `stu_birth`, `stu_addr`, `col_id`)
VALUES
    (4001, '令狐冲', 1, '1996-05-15', '河南洛阳', 1),
    (4002, '任盈盈', 0, '1997-08-22', '河南洛阳', 1),
    (4003, '风清扬', 1, '1960-01-01', '陕西华山', 1),
    (4004, '仪  琳', 0, '1998-03-10', '湖南衡阳', 2),
    (4005, '向问天', 1, '1970-11-30', NULL, 3);

-- 第二步：在暂存表上做数据校验
-- 检查学号是否与已有数据冲突
SELECT s.`stu_id`
  FROM `tb_student_staging` s
  JOIN `tb_student` t ON s.`stu_id` = t.`stu_id`;

-- 第三步：校验通过后，批量导入正式表
-- 使用 INSERT IGNORE 跳过主键冲突的记录
INSERT IGNORE INTO `tb_student`
    (`stu_id`, `stu_name`, `stu_sex`, `stu_birth`, `stu_addr`, `col_id`)
SELECT `stu_id`, `stu_name`, `stu_sex`, `stu_birth`, `stu_addr`, `col_id`
  FROM `tb_student_staging`;

-- 第四步：清理暂存表
DROP TEMPORARY TABLE IF EXISTS `tb_student_staging`;


-- ----------------------------------------------------------
-- 案例二：订单处理事务
-- 场景：学生选课是一个完整的事务操作，包含多个步骤
-- ----------------------------------------------------------

-- 假设选课系统需要满足：
--   1. 课程未满员
--   2. 学生未重复选课
--   3. 同时更新课程人数

DELIMITER $$

CREATE PROCEDURE IF NOT EXISTS `sp_enroll_course`(
    IN p_stu_id  INT,
    IN p_cou_id  INT,
    OUT p_result VARCHAR(50)
)
BEGIN
    DECLARE v_already_enrolled INT DEFAULT 0;
    DECLARE v_course_exists    INT DEFAULT 0;

    -- 声明异常处理：任何 SQL 异常都触发回滚
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_result = '选课失败：系统异常，已回滚';
    END;

    START TRANSACTION;

        -- 检查1：学生是否已选该课程
        SELECT COUNT(*) INTO v_already_enrolled
          FROM `tb_record`
         WHERE `stu_id` = p_stu_id
           AND `cou_id` = p_cou_id;

        IF v_already_enrolled > 0 THEN
            ROLLBACK;
            SET p_result = '选课失败：该课程已选修';
        ELSE
            -- 检查2：课程是否存在
            SELECT COUNT(*) INTO v_course_exists
              FROM `tb_course`
             WHERE `cou_id` = p_cou_id;

            IF v_course_exists = 0 THEN
                ROLLBACK;
                SET p_result = '选课失败：课程不存在';
            ELSE
                -- 插入选课记录
                INSERT INTO `tb_record` (`stu_id`, `cou_id`, `sel_date`, `score`)
                VALUES (p_stu_id, p_cou_id, CURDATE(), NULL);

                -- 更新课程选课人数（假设 tb_course 有 enrollment_count 字段）
                -- UPDATE `tb_course`
                --    SET `enrollment_count` = `enrollment_count` + 1
                --  WHERE `cou_id` = p_cou_id;

                COMMIT;
                SET p_result = '选课成功';
            END IF;
        END IF;
END$$

DELIMITER ;

-- 调用存储过程示例
-- CALL `sp_enroll_course`(1002, 3333, @result);
-- SELECT @result;


-- ----------------------------------------------------------
-- 案例三：库存/成绩批量更新
-- 场景：期末批量录入学生成绩，使用事务保证数据一致性
-- ----------------------------------------------------------

START TRANSACTION;

    -- 设置保存点，便于部分回滚
    SAVEPOINT before_score_update;

    -- 批量录入考试成绩
    UPDATE `tb_record`
       SET `score` = CASE `stu_id`
           WHEN 1001 THEN 95
           WHEN 1002 THEN 78
           WHEN 1033 THEN 88
           WHEN 1572 THEN 62
           WHEN 1378 THEN 91
           WHEN 2035 THEN 85
           WHEN 3755 THEN 73
       END
     WHERE `cou_id` = 1111
       AND `sel_date` = '2019-09-02'
       AND `score` IS NULL;

    -- 验证更新结果
    SELECT `stu_id`, `score`
      FROM `tb_record`
     WHERE `cou_id` = 1111
       AND `sel_date` = '2019-09-02';

    -- 如果结果有误，可回滚到保存点
    -- ROLLBACK TO SAVEPOINT before_score_update;

    -- 确认无误后提交
COMMIT;


-- ----------------------------------------------------------
-- 案例四：并发库存扣减模拟（乐观锁模式）
-- 场景：多个操作同时修改同一行数据时的冲突处理
-- ----------------------------------------------------------

-- 表结构示例（假设用于课程名额管理）
-- CREATE TABLE `tb_course_quota` (
--     `cou_id`  INT NOT NULL PRIMARY KEY,
--     `quota`   INT NOT NULL DEFAULT 50,     -- 总名额
--     `version` INT NOT NULL DEFAULT 0       -- 乐观锁版本号
-- ) ENGINE=InnoDB;

-- 乐观锁更新模式：通过 version 字段检测并发冲突
-- UPDATE `tb_course_quota`
--    SET `quota`   = `quota` - 1,
--        `version` = `version` + 1
--  WHERE `cou_id` = 1111
--    AND `version` = @current_version    -- 读取时记录的版本号
--    AND `quota` > 0;
-- -- 如果 affected_rows = 0，说明被其他事务抢先修改，需要重试


-- ----------------------------------------------------------
-- 案例五：使用 REPLACE 实现数据同步
-- 场景：从外部系统同步最新的教师职称信息
-- ----------------------------------------------------------

-- 假设外部系统推送了一批教师数据
-- REPLACE 会自动处理"存在则更新，不存在则插入"的逻辑
REPLACE INTO `tb_teacher` (`tea_id`, `tea_name`, `tea_title`, `col_id`)
VALUES
    (1122, '张三丰', '终身教授', 1),     -- 已存在，更新职称
    (1133, '宋远桥', '教授', 1),         -- 已存在，更新职称
    (1144, '杨  逍', '教授', 1),         -- 已存在，更新职称
    (2255, '范  遥', '教授', 2),         -- 已存在，更新职称
    (3366, '韦一笑', '讲师', 3),         -- 已存在，更新职称
    (7700, '空见大师', '教授', 4);        -- 新增教师


-- ============================================================
-- 常用技巧与注意事项总结
-- ============================================================
--
-- 1. INSERT 注意事项：
--    - 主键不能重复，否则报 Duplicated Entry 错误
--    - 省略的列必须有默认值或允许 NULL
--    - 批量插入比逐条插入效率高很多
--    - 使用 LOW_PRIORITY 可降低写操作对读操作的影响
--
-- 2. UPDATE 注意事项：
--    - 务必带 WHERE 子句，否则更新全表
--    - WHERE 中优先使用主键或唯一索引定位
--    - SET 后面的 = 是赋值，其他位置的 = 是比较运算符
--    - 可用 CASE WHEN 实现条件批量更新
--
-- 3. DELETE 注意事项：
--    - 务必带 WHERE 子句，否则删除全表
--    - DELETE 不会重置 AUTO_INCREMENT
--    - TRUNCATE 重置 AUTO_INCREMENT 且更快，但不可恢复
--    - 大量删除时用 LIMIT 分批处理，避免长时间锁表
--
-- 4. REPLACE 注意事项：
--    - 依赖主键或唯一索引判断冲突
--    - 冲突时先删后插，AUTO_INCREMENT 会递增
--    - 适合"有则更新，无则插入"的同步场景
--
-- 5. 事务注意事项：
--    - MySQL 中只有 InnoDB 引擎支持事务
--    - 事务中避免使用 DDL（CREATE/ALTER/DROP），会隐式提交
--    - 合理使用 SAVEPOINT 实现部分回滚
--    - 事务不宜过长，避免长时间持有锁
