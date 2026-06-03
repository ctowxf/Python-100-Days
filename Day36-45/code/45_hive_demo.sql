-- ============================================================================
-- HiveQL Demo Script
-- 配套文档: Day36-45/45.Hive实战.md
-- 覆盖内容: HiveQL基础语法、分区表、分桶表、企业级数据仓库查询
-- ============================================================================


-- ============================================================================
-- 第一部分: 数据库与环境设置
-- ============================================================================

-- 删除已有数据库（CASCADE 同时删除库中所有表）
DROP DATABASE IF EXISTS eshop CASCADE;

-- 创建数据库
CREATE DATABASE IF NOT EXISTS eshop
    COMMENT '电商数据仓库';

-- 切换到目标数据库
USE eshop;

-- 设置本地模式（小数据量时加速执行，避免启动MapReduce分布式任务）
SET hive.exec.mode.local.auto=true;
SET hive.exec.mode.local.auto.input.files.max=128;
SET hive.exec.mode.local.auto.input.bytes.max=134217728;

-- 设置 Reduce 任务个数
SET mapreduce.job.reduces=1;


-- ============================================================================
-- 第二部分: 创建维度表（外部表 + 复杂数据类型）
-- ============================================================================

-- 用户维度表（外部表）
-- 说明: 使用 EXTERNAL 关键字，删表时数据保留在 HDFS 上，不会被删除
CREATE EXTERNAL TABLE IF NOT EXISTS dim_user_info
(
    user_id           STRING      COMMENT '用户ID',
    user_name         STRING      COMMENT '用户名',
    sex               STRING      COMMENT '性别',
    age               INT         COMMENT '年龄',
    city              STRING      COMMENT '所在城市',
    first_active_time STRING      COMMENT '首次激活时间',
    level             INT         COMMENT '用户等级',
    extra1            STRING      COMMENT '扩展字段1（JSON格式，存储手机品牌等信息）',
    extra2            MAP<STRING, STRING> COMMENT '扩展字段2（键值对，存储婚姻状况等标签）'
)
COMMENT '用户维度信息表'
ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '\t'
    COLLECTION ITEMS TERMINATED BY ','
    MAP KEYS TERMINATED BY ':'
LINES TERMINATED BY '\n'
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/eshop.db/dim_user_info';

-- 加载本地数据到用户维度表
LOAD DATA LOCAL INPATH '/home/hadoop/data/user_info/user_info.txt'
    OVERWRITE INTO TABLE dim_user_info;

-- 加载 HDFS 数据到用户维度表（数据已在 HDFS 上时使用）
-- LOAD DATA INPATH '/user/data/user_info.txt'
--     OVERWRITE INTO TABLE dim_user_info;


-- ============================================================================
-- 第三部分: 分区表（Partitioned Table）
-- ============================================================================

-- 用户交易事实表（按日期分区）
-- 说明: 分区字段 dt 不存储在表数据文件中，而是作为 HDFS 路径目录
-- 例如: /user/hive/warehouse/eshop.db/fact_user_trade/dt=2019-03-24/
CREATE TABLE IF NOT EXISTS fact_user_trade
(
    user_name      STRING      COMMENT '用户名',
    piece          INT         COMMENT '购买件数',
    price          DOUBLE      COMMENT '单价',
    pay_amount     DOUBLE      COMMENT '实际支付金额',
    goods_category STRING      COMMENT '商品品类',
    pay_time       BIGINT      COMMENT '支付时间戳（秒）'
)
COMMENT '用户交易事实表（按日期分区）'
PARTITIONED BY (dt STRING COMMENT '交易日期分区，格式: yyyy-MM-dd')
ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '\t'
    LINES TERMINATED BY '\n'
STORED AS TEXTFILE;

-- 加载数据到指定分区
LOAD DATA LOCAL INPATH '/home/hadoop/data/user_trade/2019-03-24.txt'
    INTO TABLE fact_user_trade PARTITION (dt='2019-03-24');

LOAD DATA LOCAL INPATH '/home/hadoop/data/user_trade/2019-04-01.txt'
    INTO TABLE fact_user_trade PARTITION (dt='2019-04-01');


-- ============================================================================
-- 第四部分: 动态分区（Dynamic Partitioning）
-- ============================================================================

-- 开启动态分区功能
SET hive.exec.dynamic.partition=true;

-- 设置非严格模式（严格模式下至少需要指定一个静态分区列）
SET hive.exec.dynamic.partition.mode=nonstrict;

-- 全局最多创建 1000 个动态分区
SET hive.exec.dynamic.partitions=1000;

-- 每个节点最多创建 10000 个动态分区
SET hive.exec.dynamic.partitions.pernode=10000;

-- 多级分区表：按年、月、日三级分区
CREATE TABLE IF NOT EXISTS fact_order_detail
(
    order_id        STRING      COMMENT '订单ID',
    user_name       STRING      COMMENT '用户名',
    goods_id        STRING      COMMENT '商品ID',
    goods_name      STRING      COMMENT '商品名称',
    goods_category  STRING      COMMENT '商品品类',
    quantity        INT         COMMENT '购买数量',
    unit_price      DECIMAL(10,2) COMMENT '商品单价',
    pay_amount      DECIMAL(10,2) COMMENT '支付金额'
)
COMMENT '订单明细事实表（按年/月/日三级分区）'
PARTITIONED BY (dt_year STRING, dt_month STRING, dt_day STRING)
ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '\t'
    LINES TERMINATED BY '\n'
STORED AS ORC;

-- 通过动态分区插入数据（根据 SELECT 结果自动生成分区目录）
-- INSERT OVERWRITE TABLE fact_order_detail
--     PARTITION (dt_year, dt_month, dt_day)
-- SELECT order_id, user_name, goods_id, goods_name,
--        goods_category, quantity, unit_price, pay_amount,
--        YEAR(order_time) AS dt_year,
--        MONTH(order_time) AS dt_month,
--        DAY(order_time) AS dt_day
--   FROM staging_orders;

-- 修复分区（当手动在 HDFS 上创建分区目录后，需要执行此命令同步元数据）
MSCK REPAIR TABLE fact_user_trade;


-- ============================================================================
-- 第五部分: 分桶表（Bucketed Table）
-- ============================================================================

-- 用户行为日志表（按 user_id 分桶）
-- 说明: 分桶将数据按哈希值分布到固定数量的文件中
-- 优势: 优化等值 Join、支持高效数据抽样、数据均匀分布
CREATE TABLE IF NOT EXISTS fact_user_behavior
(
    user_id         STRING      COMMENT '用户ID',
    item_id         STRING      COMMENT '商品/内容ID',
    behavior_type   STRING      COMMENT '行为类型（view/click/collect/buy）',
    behavior_time   TIMESTAMP   COMMENT '行为发生时间',
    device_type     STRING      COMMENT '设备类型（mobile/pc/tablet）',
    session_id      STRING      COMMENT '会话ID'
)
COMMENT '用户行为日志表（按 user_id 分桶，16 个桶）'
CLUSTERED BY (user_id) INTO 16 BUCKETS
ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '\t'
    LINES TERMINATED BY '\n'
STORED AS ORC;

-- 插入分桶表数据前需设置以下参数
SET hive.enforce.bucketing=true;

-- INSERT OVERWRITE TABLE fact_user_behavior
-- SELECT user_id, item_id, behavior_type, behavior_time,
--        device_type, session_id
--   FROM staging_behavior;


-- ============================================================================
-- 第六部分: 分区 + 分桶复合表
-- ============================================================================

-- 订单表：按日期分区 + 按用户ID分桶
-- 同时利用分区裁剪和分桶优化 Join
CREATE TABLE IF NOT EXISTS fact_order
(
    order_id        STRING        COMMENT '订单ID',
    user_id         STRING        COMMENT '用户ID',
    goods_id        STRING        COMMENT '商品ID',
    goods_name      STRING        COMMENT '商品名称',
    order_amount    DECIMAL(12,2) COMMENT '订单金额',
    order_status    INT           COMMENT '订单状态（0待付款/1已付款/2已发货/3已完成/4已取消）',
    create_time     TIMESTAMP     COMMENT '下单时间'
)
COMMENT '订单事实表（按日期分区 + 按用户ID分桶）'
PARTITIONED BY (dt STRING COMMENT '订单日期分区')
CLUSTERED BY (user_id) INTO 32 BUCKETS
ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '\t'
    LINES TERMINATED BY '\n'
STORED AS ORC
TBLPROPERTIES ('orc.compress'='SNAPPY');


-- ============================================================================
-- 第七部分: ORC / Parquet 列式存储表
-- ============================================================================

-- ORC 格式存储（自带索引和压缩，适合分析型查询）
CREATE TABLE IF NOT EXISTS dim_product
(
    product_id      STRING        COMMENT '商品ID',
    product_name    STRING        COMMENT '商品名称',
    category_id     STRING        COMMENT '品类ID',
    category_name   STRING        COMMENT '品类名称',
    brand           STRING        COMMENT '品牌',
    original_price  DECIMAL(10,2) COMMENT '原价',
    current_price   DECIMAL(10,2) COMMENT '现价',
    stock           INT           COMMENT '库存数量',
    tags            ARRAY<STRING> COMMENT '商品标签（数组类型）',
    attributes      MAP<STRING, STRING> COMMENT '商品属性（键值对类型）'
)
COMMENT '商品维度表（ORC列式存储）'
ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '\t'
    COLLECTION ITEMS TERMINATED BY ','
    MAP KEYS TERMINATED BY ':'
LINES TERMINATED BY '\n'
STORED AS ORC
TBLPROPERTIES ('orc.compress'='ZLIB');

-- Parquet 格式存储（跨平台兼容性好，适合与 Spark 交互）
CREATE TABLE IF NOT EXISTS fact_web_log
(
    log_id          STRING        COMMENT '日志ID',
    user_id         STRING        COMMENT '用户ID',
    page_url        STRING        COMMENT '页面URL',
    referer_url     STRING        COMMENT '来源URL',
    ip_address      STRING        COMMENT 'IP地址',
    user_agent      STRING        COMMENT '浏览器UA',
    request_time    TIMESTAMP     COMMENT '请求时间'
)
COMMENT 'Web访问日志事实表（Parquet格式）'
PARTITIONED BY (dt STRING COMMENT '日志日期分区')
ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '\t'
    LINES TERMINATED BY '\n'
STORED AS PARQUET;


-- ============================================================================
-- 第八部分: 基础查询（数据提取与过滤）
-- ============================================================================

-- 查询北京女性用户的姓名（取前10个）
SELECT user_name
  FROM dim_user_info
 WHERE city = 'beijing'
   AND sex = 'female'
 LIMIT 10;

-- 查询2019年3月24日购买了 food 类商品的用户名、购买数量和支付金额
-- 说明: WHERE 子句包含分区字段 dt，Hive 会自动进行分区裁剪（Partition Pruning）
SELECT user_name
     , piece
     , pay_amount
  FROM fact_user_trade
 WHERE dt = '2019-03-24'
   AND goods_category = 'food';

-- 统计用户 ELLA 在2018年的总支付金额和最近最远两次消费间隔天数
-- 使用 UNIX 时间戳转换函数 FROM_UNIXTIME 和日期差函数 DATEDIFF
SELECT SUM(pay_amount) AS total_pay
     , DATEDIFF(
           MAX(FROM_UNIXTIME(pay_time, 'yyyy-MM-dd')),
           MIN(FROM_UNIXTIME(pay_time, 'yyyy-MM-dd'))
       ) AS gap_days
  FROM fact_user_trade
 WHERE YEAR(dt) = 2018
   AND user_name = 'ELLA';


-- ============================================================================
-- 第九部分: 分组聚合（GROUP BY / HAVING / 子查询）
-- ============================================================================

-- 查询2019年1月至4月，每个品类的购买人数和累计支付金额
SELECT goods_category
     , COUNT(DISTINCT user_name) AS total_user
     , SUM(pay_amount)           AS total_pay
  FROM fact_user_trade
 WHERE dt BETWEEN '2019-01-01' AND '2019-04-30'
 GROUP BY goods_category;

-- 查询2019年4月支付金额超过5万元的用户
SELECT user_name
     , SUM(pay_amount) AS total_pay
  FROM fact_user_trade
 WHERE dt BETWEEN '2019-04-01' AND '2019-04-30'
 GROUP BY user_name
HAVING SUM(pay_amount) > 50000;

-- 查询2018年购买品类在两个以上的用户数
-- 使用子查询 + HAVING 过滤
SELECT COUNT(*) AS multi_category_user_count
  FROM (
    SELECT user_name
         , COUNT(DISTINCT goods_category) AS category_count
      FROM fact_user_trade
     WHERE YEAR(dt) = 2018
     GROUP BY user_name
    HAVING COUNT(DISTINCT goods_category) > 2
) t;

-- 查询2019年4月支付金额最多的前5名用户
SELECT user_name
     , SUM(pay_amount) AS total_pay
  FROM fact_user_trade
 WHERE dt BETWEEN '2019-04-01' AND '2019-04-30'
 GROUP BY user_name
 ORDER BY total_pay DESC
 LIMIT 5;

-- 统计不同年龄段的用户数（CASE WHEN 条件分段）
SELECT CASE
           WHEN age < 20 THEN '20岁以下'
           WHEN age < 30 THEN '20-29岁'
           WHEN age < 40 THEN '30-39岁'
           ELSE '40岁以上'
       END AS age_segment
     , COUNT(DISTINCT user_id) AS user_count
  FROM dim_user_info
 GROUP BY CASE
              WHEN age < 20 THEN '20岁以下'
              WHEN age < 30 THEN '20-29岁'
              WHEN age < 40 THEN '30-39岁'
              ELSE '40岁以上'
          END;


-- ============================================================================
-- 第十部分: 复杂类型函数（MAP / ARRAY / JSON）
-- ============================================================================

-- 统计激活时间在2018年，年龄在20-40岁之间的用户婚姻状况
-- 使用 MAP 类型取值: extra2['marriage_status']
SELECT age_segment
     , IF(marriage_status = '1', '已婚', '未婚') AS marriage_status
     , COUNT(*) AS user_count
  FROM (
    SELECT CASE
               WHEN age < 20 THEN '20岁以下'
               WHEN age < 30 THEN '20-30岁'
               WHEN age < 40 THEN '30-40岁'
               ELSE '40岁以上'
           END AS age_segment
         , extra2['marriage_status'] AS marriage_status
      FROM dim_user_info
     WHERE TO_DATE(first_active_time) BETWEEN '2018-01-01' AND '2018-12-31'
) t
 WHERE age_segment IN ('20-30岁', '30-40岁')
 GROUP BY age_segment, IF(marriage_status = '1', '已婚', '未婚');

-- 统计不同手机品牌的用户数（从 JSON 字段中提取数据）
-- 使用 GET_JSON_OBJECT 函数解析 JSON 字符串
SELECT GET_JSON_OBJECT(extra1, '$.phonebrand') AS phone_brand
     , COUNT(DISTINCT user_id) AS user_count
  FROM dim_user_info
 GROUP BY GET_JSON_OBJECT(extra1, '$.phonebrand');

-- 统计每个用户购买过哪些品类的商品（COLLECT_SET 去重聚合为数组）
SELECT user_name
     , COLLECT_SET(goods_category) AS purchased_categories
  FROM fact_user_trade
 GROUP BY user_name;

-- 将数组拼接为逗号分隔的字符串
SELECT user_name
     , CONCAT_WS(', ', COLLECT_SET(goods_category)) AS category_list
  FROM fact_user_trade
 GROUP BY user_name;

-- 将数据聚合成 MAP 类型（品类 -> 购买次数）
SELECT user_name
     , STR_TO_MAP(
           CONCAT_WS(',', COLLECT_LIST(CONCAT(goods_category, ':', cnt)))
       ) AS category_count_map
  FROM (
    SELECT user_name
         , goods_category
         , COUNT(*) AS cnt
      FROM fact_user_trade
     GROUP BY user_name, goods_category
) t
 GROUP BY user_name;


-- ============================================================================
-- 第十一部分: 横向展开（LATERAL VIEW + EXPLODE）
-- ============================================================================

-- 创建视图：每个用户在2019年4月购买的商品品类集合
CREATE OR REPLACE VIEW v_user_categories
AS
SELECT user_name
     , COLLECT_SET(goods_category) AS categories
  FROM fact_user_trade
 WHERE dt BETWEEN '2019-04-01' AND '2019-04-30'
 GROUP BY user_name;

-- 创建视图：每个用户在2019年4月的商品品类与购买次数映射
CREATE OR REPLACE VIEW v_user_category_map
AS
SELECT user_name
     , STR_TO_MAP(
           CONCAT_WS(',', COLLECT_LIST(CONCAT(goods_category, ':', cnt)))
       ) AS category_cnt_map
  FROM (
    SELECT user_name
         , goods_category
         , COUNT(*) AS cnt
      FROM fact_user_trade
     WHERE dt BETWEEN '2019-04-01' AND '2019-04-30'
     GROUP BY user_name, goods_category
) t
 GROUP BY user_name;

-- 横向展开 ARRAY 类型：将每个用户的品类数组拆成多行
-- 用途: 宽表转窄表，便于后续按品类进行分析
SELECT user_name
     , category
  FROM v_user_categories
LATERAL VIEW EXPLODE(categories) t AS category;

-- 横向展开 MAP 类型：将品类-次数映射拆成多行
-- 用途: 键值对数据的逐行分析
SELECT user_name
     , category
     , cnt
  FROM v_user_category_map
LATERAL VIEW EXPLODE(category_cnt_map) t AS category, cnt;

-- LATERAL VIEW + json_tuple：从 JSON 日志中批量抽取字段
-- 比 GET_JSON_OBJECT 效率更高（一次解析多个字段）
-- SELECT log_id, ip_addr, device_type
--   FROM fact_web_log
-- LATERAL VIEW json_tuple(log_json, 'ip', 'device') t AS ip_addr, device_type;


-- ============================================================================
-- 第十二部分: 数据抽样（Sampling）
-- ============================================================================

-- 概率抽样：按 10% 概率随机抽取行
SELECT *
  FROM fact_user_trade
 WHERE dt = '2019-04-01'
   AND RAND() < 0.1;

-- 分桶抽样（逻辑桶）：按 user_name 哈希映射到 10 个桶，取第 1 个桶
-- 约为总量的 1/10，且同一用户的记录始终在同一桶中，保证一致性
SELECT *
  FROM fact_user_trade
 TABLESAMPLE(BUCKET 1 OUT OF 10 ON user_name);

-- 每组固定样本数：每个品类随机取 5 条交易记录
SELECT *
  FROM (
    SELECT *
         , ROW_NUMBER() OVER(PARTITION BY goods_category ORDER BY RAND()) AS rn
      FROM fact_user_trade
     WHERE dt = '2019-04-01'
) t
 WHERE rn <= 5;


-- ============================================================================
-- 第十三部分: 窗口函数（Window Functions）
-- ============================================================================

-- ROW_NUMBER: 每个品类中支付金额最高的前3笔交易
SELECT *
  FROM (
    SELECT user_name
         , goods_category
         , pay_amount
         , ROW_NUMBER() OVER(
               PARTITION BY goods_category
               ORDER BY pay_amount DESC
           ) AS rn
      FROM fact_user_trade
     WHERE dt = '2019-04-01'
) t
 WHERE rn <= 3;

-- RANK 与 DENSE_RANK: 用户按总消费金额排名（含并列处理）
SELECT user_name
     , total_pay
     , RANK()       OVER(ORDER BY total_pay DESC) AS rank_val
     , DENSE_RANK() OVER(ORDER BY total_pay DESC) AS dense_rank_val
  FROM (
    SELECT user_name
         , SUM(pay_amount) AS total_pay
      FROM fact_user_trade
     WHERE dt BETWEEN '2019-04-01' AND '2019-04-30'
     GROUP BY user_name
) t;

-- LAG / LEAD: 计算用户相邻两次购买的时间间隔
SELECT user_name
     , pay_date
     , prev_pay_date
     , DATEDIFF(pay_date, prev_pay_date) AS days_since_last_purchase
  FROM (
    SELECT user_name
         , FROM_UNIXTIME(pay_time, 'yyyy-MM-dd') AS pay_date
         , LAG(FROM_UNIXTIME(pay_time, 'yyyy-MM-dd'), 1) OVER(
               PARTITION BY user_name ORDER BY pay_time
           ) AS prev_pay_date
      FROM fact_user_trade
     WHERE dt BETWEEN '2019-04-01' AND '2019-04-30'
) t;

-- 累计求和: 每个用户在2019年4月的累计消费金额
SELECT user_name
     , pay_date
     , daily_pay
     , SUM(daily_pay) OVER(
           PARTITION BY user_name
           ORDER BY pay_date
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS cumulative_pay
  FROM (
    SELECT user_name
         , FROM_UNIXTIME(pay_time, 'yyyy-MM-dd') AS pay_date
         , SUM(pay_amount) AS daily_pay
      FROM fact_user_trade
     WHERE dt BETWEEN '2019-04-01' AND '2019-04-30'
     GROUP BY user_name, FROM_UNIXTIME(pay_time, 'yyyy-MM-dd')
) t;


-- ============================================================================
-- 第十四部分: GROUPING SETS / CUBE / ROLLUP（多维聚合）
-- ============================================================================

-- GROUPING SETS: 按指定的维度组合分别聚合（结果集包含多个维度的汇总行）
-- 示例: 同时查看「品类+城市」、「仅品类」、「仅城市」三种维度的销售汇总
-- SELECT goods_category
--      , city
--      , SUM(pay_amount) AS total_pay
--   FROM fact_user_trade t
--   JOIN dim_user_info u ON t.user_name = u.user_name
--  WHERE t.dt BETWEEN '2019-04-01' AND '2019-04-30'
--  GROUP BY goods_category, city
-- GROUPING SETS (
--     (goods_category, city),
--     (goods_category),
--     (city),
--     ()
-- );

-- CUBE: 自动生成所有维度组合（2^n 种，n=维度列数）
-- SELECT goods_category
--      , city
--      , SUM(pay_amount) AS total_pay
--   FROM fact_user_trade t
--   JOIN dim_user_info u ON t.user_name = u.user_name
--  WHERE t.dt BETWEEN '2019-04-01' AND '2019-04-30'
--  GROUP BY goods_category, city
--  CUBE;


-- ============================================================================
-- 第十五部分: 排序方式对比
-- ============================================================================

-- ORDER BY: 全局排序（所有数据汇入单个 Reducer，大结果集慎用）
SELECT user_name
     , SUM(pay_amount) AS total_pay
  FROM fact_user_trade
 WHERE dt BETWEEN '2019-04-01' AND '2019-04-30'
 GROUP BY user_name
 ORDER BY total_pay DESC
 LIMIT 10;

-- SORT BY: 每个 Reducer 内部排序（局部有序，不保证全局顺序）
-- 适合大表分片排序后导出
-- SELECT user_name, pay_amount
--   FROM fact_user_trade
--  WHERE dt = '2019-04-01'
--  SORT BY pay_amount DESC;

-- DISTRIBUTE BY + SORT BY: 按字段分发到同一 Reducer 并在内部排序
-- 适合按用户分组后按时间排序的场景
-- SELECT user_name, goods_category, pay_amount, pay_time
--   FROM fact_user_trade
--  WHERE dt = '2019-04-01'
-- DISTRIBUTE BY user_name
--  SORT BY user_name, pay_time DESC;

-- CLUSTER BY: DISTRIBUTE BY + SORT BY 的语法糖（只能升序）
-- SELECT user_name, pay_amount
--   FROM fact_user_trade
--  WHERE dt = '2019-04-01'
--  CLUSTER BY user_name;


-- ============================================================================
-- 第十六部分: 数据写入方式
-- ============================================================================

-- INSERT INTO: 追加数据（不覆盖已有数据）
-- INSERT INTO TABLE fact_user_trade PARTITION (dt='2019-05-01')
-- SELECT user_name, piece, price, pay_amount, goods_category, pay_time
--   FROM staging_trade
--  WHERE trade_date = '2019-05-01';

-- INSERT OVERWRITE: 覆盖数据（先删除原有数据再写入）
-- INSERT OVERWRITE TABLE fact_user_trade PARTITION (dt='2019-05-01')
-- SELECT user_name, piece, price, pay_amount, goods_category, pay_time
--   FROM staging_trade
--  WHERE trade_date = '2019-05-01';

-- CREATE TABLE AS SELECT (CTAS): 根据查询结果创建新表
-- CREATE TABLE tmp_high_value_users AS
-- SELECT user_name
--      , SUM(pay_amount) AS total_pay
--      , COUNT(*) AS order_count
--   FROM fact_user_trade
--  WHERE dt BETWEEN '2019-01-01' AND '2019-12-31'
--  GROUP BY user_name
-- HAVING SUM(pay_amount) > 100000;

-- 导出数据到 HDFS 目录
-- INSERT OVERWRITE DIRECTORY '/tmp/export/user_trade/'
--     ROW FORMAT DELIMITED
--     FIELDS TERMINATED BY ','
-- SELECT user_name, pay_amount, goods_category
--   FROM fact_user_trade
--  WHERE dt = '2019-04-01';


-- ============================================================================
-- 第十七部分: 企业级数据仓库查询示例
-- ============================================================================

-- -------------------------------------------------------
-- 1. 月度GMV趋势分析
-- 按月统计总交易额、订单数、客单价
-- -------------------------------------------------------
SELECT SUBSTR(dt, 1, 7)              AS trade_month
     , SUM(pay_amount)               AS gmv
     , COUNT(*)                      AS order_count
     , ROUND(SUM(pay_amount) / COUNT(DISTINCT user_name), 2) AS avg_spend_per_user
  FROM fact_user_trade
 WHERE dt BETWEEN '2019-01-01' AND '2019-12-31'
 GROUP BY SUBSTR(dt, 1, 7)
 ORDER BY trade_month;

-- -------------------------------------------------------
-- 2. 用户生命周期价值 (LTV) 分析
-- 计算每个用户的首次消费日期、累计消费金额、消费天数
-- -------------------------------------------------------
SELECT user_name
     , MIN(dt)                      AS first_purchase_date
     , MAX(dt)                      AS last_purchase_date
     , DATEDIFF(MAX(dt), MIN(dt))   AS lifecycle_days
     , SUM(pay_amount)              AS total_ltv
     , COUNT(DISTINCT dt)           AS active_days
     , ROUND(SUM(pay_amount) / COUNT(DISTINCT dt), 2) AS avg_daily_spend
  FROM fact_user_trade
 GROUP BY user_name
 ORDER BY total_ltv DESC
 LIMIT 20;

-- -------------------------------------------------------
-- 3. 品类销售占比分析
-- 计算每个品类的销售额占总销售额的百分比
-- -------------------------------------------------------
SELECT goods_category
     , category_pay
     , total_pay
     , ROUND(category_pay / total_pay * 100, 2) AS pay_percentage
  FROM (
    SELECT goods_category
         , SUM(pay_amount) AS category_pay
      FROM fact_user_trade
     WHERE dt BETWEEN '2019-04-01' AND '2019-04-30'
     GROUP BY goods_category
) t
 CROSS JOIN (
    SELECT SUM(pay_amount) AS total_pay
      FROM fact_user_trade
     WHERE dt BETWEEN '2019-04-01' AND '2019-04-30'
) total
 ORDER BY pay_percentage DESC;

-- -------------------------------------------------------
-- 4. 用户复购率分析
-- 统计在指定时间段内购买超过一次的用户比例
-- -------------------------------------------------------
SELECT COUNT(*) AS total_users
     , SUM(CASE WHEN purchase_days > 1 THEN 1 ELSE 0 END) AS repeat_users
     , ROUND(
           SUM(CASE WHEN purchase_days > 1 THEN 1 ELSE 0 END) / COUNT(*) * 100,
           2
       ) AS repeat_rate_pct
  FROM (
    SELECT user_name
         , COUNT(DISTINCT dt) AS purchase_days
      FROM fact_user_trade
     WHERE dt BETWEEN '2019-01-01' AND '2019-06-30'
     GROUP BY user_name
) t;

-- -------------------------------------------------------
-- 5. 留存分析（Cohort Analysis）
-- 统计用户在首次消费月份后的后续月份活跃情况
-- -------------------------------------------------------
SELECT cohort_month
     , DATEDIFF(SUBSTR(active_dt, 1, 7), cohort_month) AS months_since_first
     , COUNT(DISTINCT user_name) AS retained_users
  FROM (
    SELECT user_name
         , MIN(SUBSTR(dt, 1, 7)) OVER(PARTITION BY user_name) AS cohort_month
         , dt AS active_dt
      FROM fact_user_trade
) t
 GROUP BY cohort_month, DATEDIFF(SUBSTR(active_dt, 1, 7), cohort_month)
 ORDER BY cohort_month, months_since_first;

-- -------------------------------------------------------
-- 6. RFM 模型分层（简化版）
-- R(Recency): 最近一次消费距今天数
-- F(Frequency): 消费频次（消费天数）
-- M(Monetary): 消费总金额
-- -------------------------------------------------------
SELECT user_name
     , recency
     , frequency
     , monetary
     , CASE
           WHEN recency <= 30 AND frequency >= 10 AND monetary >= 50000 THEN '高价值用户'
           WHEN recency <= 30 AND frequency >= 5  THEN '活跃用户'
           WHEN recency <= 90                      THEN '一般用户'
           WHEN recency <= 180                     THEN '沉默用户'
           ELSE '流失用户'
       END AS user_segment
  FROM (
    SELECT user_name
         , DATEDIFF('2019-04-30', MAX(dt)) AS recency
         , COUNT(DISTINCT dt)               AS frequency
         , SUM(pay_amount)                  AS monetary
      FROM fact_user_trade
     WHERE dt BETWEEN '2018-01-01' AND '2019-04-30'
     GROUP BY user_name
) t
 ORDER BY monetary DESC;

-- -------------------------------------------------------
-- 7. 商品关联分析（购物篮分析简化版）
-- 找出经常被同一用户在同一日购买的品类组合
-- -------------------------------------------------------
SELECT a.goods_category AS category_a
     , b.goods_category AS category_b
     , COUNT(DISTINCT a.user_name) AS co_occurrence_count
  FROM (SELECT DISTINCT user_name, dt, goods_category FROM fact_user_trade) a
  JOIN (SELECT DISTINCT user_name, dt, goods_category FROM fact_user_trade) b
    ON a.user_name = b.user_name
   AND a.dt = b.dt
   AND a.goods_category < b.goods_category
 WHERE a.dt BETWEEN '2019-04-01' AND '2019-04-30'
 GROUP BY a.goods_category, b.goods_category
HAVING COUNT(DISTINCT a.user_name) >= 10
 ORDER BY co_occurrence_count DESC
 LIMIT 20;

-- -------------------------------------------------------
-- 8. 每日活跃用户 (DAU) 趋势
-- 统计每天的不同用户访问数
-- -------------------------------------------------------
-- SELECT dt
--      , COUNT(DISTINCT user_id) AS dau
--   FROM fact_user_behavior
--  WHERE behavior_type = 'view'
--  GROUP BY dt
--  ORDER BY dt;


-- ============================================================================
-- 第十八部分: 性能优化参数设置
-- ============================================================================

-- 启用 MapJoin（小表自动加载到内存，避免 Shuffle）
SET hive.auto.convert.join=true;

-- MapJoin 小表大小阈值（默认 25MB）
SET hive.mapjoin.smalltable.filesize=25600000;

-- 启用并行执行（多个互不依赖的 Stage 可以并行运行）
SET hive.exec.parallel=true;
SET hive.exec.parallel.thread.number=8;

-- 启用列裁剪（只读取查询涉及的列，减少 IO）
SET hive.optimize.cp=true;

-- 启用分区裁剪（WHERE 中包含分区字段时自动裁剪无关分区）
SET hive.optimize.pruner=true;

-- Map 端预聚合（类似 Combiner，减少 Shuffle 数据量）
SET hive.map.aggr=true;

-- 设置 ORC 文件的压缩方式
SET hive.exec.orc.default.compress=SNAPPY;


-- ============================================================================
-- 第十九部分: 辅助命令
-- ============================================================================

-- 查看表结构
-- DESC FORMATTED fact_user_trade;
-- DESC EXTENDED fact_user_trade;

-- 查看建表语句
-- SHOW CREATE TABLE fact_user_trade;

-- 查看分区列表
-- SHOW PARTITIONS fact_user_trade;

-- 查看当前数据库中的所有表
-- SHOW TABLES;

-- 查看表的分区信息
-- DESC fact_user_trade PARTITION (dt='2019-04-01');

-- 分析表统计信息（用于查询优化器）
-- ANALYZE TABLE fact_user_trade PARTITION (dt='2019-04-01') COMPUTE STATISTICS;
-- ANALYZE TABLE fact_user_trade COMPUTE STATISTICS FOR COLUMNS;
