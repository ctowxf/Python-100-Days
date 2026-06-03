-- ============================================================================
-- 37_ddl_demo.sql
-- DDL (数据定义语言) 综合演示 —— 企业级电商数据库
-- 覆盖内容: CREATE / ALTER / DROP TABLE, 以及各类约束 (Constraints)
-- 说明: 本脚本基于 MySQL 8.x 编写, 使用 InnoDB 存储引擎, utf8mb4 字符集
-- ============================================================================

-- ============================================================================
-- 第一部分: 创建数据库 (CREATE DATABASE)
-- ============================================================================

-- 如果存在名为 ecommerce 的数据库就删除它 (仅限开发/学习环境, 生产环境慎用!)
DROP DATABASE IF EXISTS `ecommerce`;

-- 创建电商数据库, 指定默认字符集为 utf8mb4 (支持 Emoji 和国际化)
CREATE DATABASE `ecommerce`
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_general_ci;

-- 切换到 ecommerce 数据库上下文
USE `ecommerce`;

-- ============================================================================
-- 第二部分: 创建表 (CREATE TABLE) 及各类约束演示
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 2.1 用户表 (tb_user)
-- 约束演示: PRIMARY KEY, NOT NULL, DEFAULT, UNIQUE, AUTO_INCREMENT, CHECK
-- ----------------------------------------------------------------------------
CREATE TABLE `tb_user`
(
    `user_id`      BIGINT UNSIGNED AUTO_INCREMENT              COMMENT '用户ID (自增主键)',
    `username`     VARCHAR(50)  NOT NULL                        COMMENT '用户名',
    `password`     VARCHAR(255) NOT NULL                        COMMENT '密码 (存储哈希值)',
    `email`        VARCHAR(100) NOT NULL                        COMMENT '电子邮箱',
    `phone`        VARCHAR(20)  DEFAULT NULL                    COMMENT '手机号码',
    `nickname`     VARCHAR(50)  DEFAULT ''                      COMMENT '昵称',
    `avatar_url`   VARCHAR(500) DEFAULT ''                      COMMENT '头像地址',
    `gender`       TINYINT      NOT NULL DEFAULT 0              COMMENT '性别: 0-未知, 1-男, 2-女',
    `status`       TINYINT      NOT NULL DEFAULT 1              COMMENT '状态: 0-禁用, 1-正常, 2-冻结',
    `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP    COMMENT '注册时间',
    `updated_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                               ON UPDATE CURRENT_TIMESTAMP            COMMENT '更新时间',
    PRIMARY KEY (`user_id`),
    -- UNIQUE 约束: 保证用户名唯一
    CONSTRAINT `uk_user_username` UNIQUE (`username`),
    -- UNIQUE 约束: 保证邮箱唯一
    CONSTRAINT `uk_user_email` UNIQUE (`email`),
    -- CHECK 约束 (MySQL 8.0.16+): 限制性别取值范围
    CONSTRAINT `chk_user_gender` CHECK (`gender` IN (0, 1, 2)),
    -- CHECK 约束: 限制状态取值范围
    CONSTRAINT `chk_user_status` CHECK (`status` IN (0, 1, 2))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- ----------------------------------------------------------------------------
-- 2.2 用户地址表 (tb_user_address)
-- 约束演示: FOREIGN KEY (外键约束), ON DELETE CASCADE
-- 说明: 一个用户可以有多个收货地址 (一对多关系)
-- ----------------------------------------------------------------------------
CREATE TABLE `tb_user_address`
(
    `address_id`   BIGINT UNSIGNED AUTO_INCREMENT              COMMENT '地址ID',
    `user_id`      BIGINT UNSIGNED NOT NULL                    COMMENT '所属用户ID',
    `receiver`     VARCHAR(50)  NOT NULL                       COMMENT '收件人姓名',
    `phone`        VARCHAR(20)  NOT NULL                       COMMENT '收件人电话',
    `province`     VARCHAR(50)  NOT NULL                       COMMENT '省/直辖市',
    `city`         VARCHAR(50)  NOT NULL                       COMMENT '市',
    `district`     VARCHAR(50)  NOT NULL                       COMMENT '区/县',
    `detail_addr`  VARCHAR(255) NOT NULL                       COMMENT '详细地址',
    `is_default`   TINYINT      NOT NULL DEFAULT 0             COMMENT '是否默认地址: 0-否, 1-是',
    `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`address_id`),
    -- 外键约束: 关联用户表, 删除用户时级联删除其地址
    CONSTRAINT `fk_addr_user_id` FOREIGN KEY (`user_id`)
        REFERENCES `tb_user` (`user_id`) ON DELETE CASCADE,
    -- CHECK 约束: is_default 只能为 0 或 1
    CONSTRAINT `chk_addr_default` CHECK (`is_default` IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户收货地址表';

-- ----------------------------------------------------------------------------
-- 2.3 商品分类表 (tb_category) —— 使用自引用实现无限级分类
-- 约束演示: 自引用外键 (Self-referencing FK)
-- ----------------------------------------------------------------------------
CREATE TABLE `tb_category`
(
    `cat_id`       INT UNSIGNED AUTO_INCREMENT                 COMMENT '分类ID',
    `cat_name`     VARCHAR(100) NOT NULL                       COMMENT '分类名称',
    `parent_id`    INT UNSIGNED DEFAULT NULL                   COMMENT '父分类ID (NULL 表示顶级分类)',
    `level`        TINYINT      NOT NULL DEFAULT 1             COMMENT '分类层级: 1-一级, 2-二级, 3-三级',
    `sort_order`   INT          NOT NULL DEFAULT 0             COMMENT '排序值 (越小越靠前)',
    `is_visible`   TINYINT      NOT NULL DEFAULT 1             COMMENT '是否可见: 0-隐藏, 1-显示',
    `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`cat_id`),
    -- 自引用外键: parent_id 指向本表的 cat_id
    CONSTRAINT `fk_cat_parent_id` FOREIGN KEY (`parent_id`)
        REFERENCES `tb_category` (`cat_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品分类表 (支持无限级分类)';

-- ----------------------------------------------------------------------------
-- 2.4 品牌表 (tb_brand)
-- 约束演示: UNIQUE 约束
-- ----------------------------------------------------------------------------
CREATE TABLE `tb_brand`
(
    `brand_id`     INT UNSIGNED AUTO_INCREMENT                 COMMENT '品牌ID',
    `brand_name`   VARCHAR(100) NOT NULL                       COMMENT '品牌名称',
    `brand_logo`   VARCHAR(500) DEFAULT ''                     COMMENT '品牌 Logo URL',
    `brand_desc`   VARCHAR(1000) DEFAULT ''                    COMMENT '品牌描述',
    `website`      VARCHAR(255) DEFAULT ''                     COMMENT '品牌官网',
    `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`brand_id`),
    -- 品牌名称唯一
    CONSTRAINT `uk_brand_name` UNIQUE (`brand_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='品牌表';

-- ----------------------------------------------------------------------------
-- 2.5 商品表 (tb_product) —— 电商核心表
-- 约束演示: 多个外键约束, DEFAULT, NOT NULL, CHECK
-- ----------------------------------------------------------------------------
CREATE TABLE `tb_product`
(
    `product_id`   BIGINT UNSIGNED AUTO_INCREMENT              COMMENT '商品ID',
    `product_name` VARCHAR(200) NOT NULL                       COMMENT '商品名称',
    `cat_id`       INT UNSIGNED NOT NULL                       COMMENT '所属分类ID',
    `brand_id`     INT UNSIGNED DEFAULT NULL                   COMMENT '所属品牌ID',
    `price`        DECIMAL(10, 2) NOT NULL                     COMMENT '销售价格',
    `market_price` DECIMAL(10, 2) DEFAULT NULL                 COMMENT '市场参考价 (划线价)',
    `cost_price`   DECIMAL(10, 2) DEFAULT NULL                 COMMENT '成本价',
    `stock`        INT UNSIGNED NOT NULL DEFAULT 0             COMMENT '库存数量',
    `sales`        INT UNSIGNED NOT NULL DEFAULT 0             COMMENT '累计销量',
    `main_image`   VARCHAR(500) DEFAULT ''                     COMMENT '商品主图 URL',
    `description`  TEXT                                         COMMENT '商品详细描述 (富文本)',
    `status`       TINYINT      NOT NULL DEFAULT 0             COMMENT '状态: 0-下架, 1-上架, 2-待审核',
    `weight`       DECIMAL(8, 2) DEFAULT NULL                  COMMENT '重量 (kg)',
    `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                               ON UPDATE CURRENT_TIMESTAMP            COMMENT '更新时间',
    PRIMARY KEY (`product_id`),
    -- 外键: 商品所属分类
    CONSTRAINT `fk_prod_cat_id` FOREIGN KEY (`cat_id`)
        REFERENCES `tb_category` (`cat_id`),
    -- 外键: 商品所属品牌
    CONSTRAINT `fk_prod_brand_id` FOREIGN KEY (`brand_id`)
        REFERENCES `tb_brand` (`brand_id`) ON DELETE SET NULL,
    -- CHECK: 价格必须为正数
    CONSTRAINT `chk_prod_price` CHECK (`price` > 0),
    -- CHECK: 库存不能为负
    CONSTRAINT `chk_prod_stock` CHECK (`stock` >= 0),
    -- CHECK: 状态取值合法
    CONSTRAINT `chk_prod_status` CHECK (`status` IN (0, 1, 2)),
    -- 索引: 提高按分类查询的速度
    INDEX `idx_prod_cat_id` (`cat_id`),
    -- 索引: 提高按品牌查询的速度
    INDEX `idx_prod_brand_id` (`brand_id`),
    -- 索引: 按状态和销量查询 (常用于商品列表排序)
    INDEX `idx_prod_status_sales` (`status`, `sales` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品表';

-- ----------------------------------------------------------------------------
-- 2.6 商品SKU表 (tb_product_sku)
-- 说明: SKU (Stock Keeping Unit) 表示具体的库存单元, 如 "红色 / XL码"
-- 约束演示: 复合唯一约束 (Composite UNIQUE), 外键约束
-- ----------------------------------------------------------------------------
CREATE TABLE `tb_product_sku`
(
    `sku_id`       BIGINT UNSIGNED AUTO_INCREMENT              COMMENT 'SKU ID',
    `product_id`   BIGINT UNSIGNED NOT NULL                    COMMENT '所属商品ID',
    `sku_code`     VARCHAR(100) NOT NULL                       COMMENT 'SKU 编码 (唯一标识)',
    `spec_values`  VARCHAR(500) NOT NULL DEFAULT ''             COMMENT '规格值 (JSON 格式, 如 {"颜色":"红色","尺码":"XL"})',
    `price`        DECIMAL(10, 2) NOT NULL                     COMMENT 'SKU 价格',
    `stock`        INT UNSIGNED NOT NULL DEFAULT 0             COMMENT 'SKU 库存',
    `sku_image`    VARCHAR(500) DEFAULT ''                     COMMENT 'SKU 图片 URL',
    `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`sku_id`),
    -- 外键: 关联商品表, 删除商品时级联删除所有 SKU
    CONSTRAINT `fk_sku_product_id` FOREIGN KEY (`product_id`)
        REFERENCES `tb_product` (`product_id`) ON DELETE CASCADE,
    -- 唯一约束: SKU 编码全局唯一
    CONSTRAINT `uk_sku_code` UNIQUE (`sku_code`),
    -- CHECK: SKU 价格必须为正
    CONSTRAINT `chk_sku_price` CHECK (`price` > 0),
    -- CHECK: SKU 库存不能为负
    CONSTRAINT `chk_sku_stock` CHECK (`stock` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品SKU表';

-- ----------------------------------------------------------------------------
-- 2.7 订单表 (tb_order) —— 电商核心交易表
-- 约束演示: 复合索引, DEFAULT 表达式
-- ----------------------------------------------------------------------------
CREATE TABLE `tb_order`
(
    `order_id`      BIGINT UNSIGNED AUTO_INCREMENT             COMMENT '订单ID',
    `order_no`      VARCHAR(64)  NOT NULL                      COMMENT '订单编号 (业务编号, 如 ORD20250101001)',
    `user_id`       BIGINT UNSIGNED NOT NULL                   COMMENT '下单用户ID',
    `address_id`    BIGINT UNSIGNED NOT NULL                   COMMENT '收货地址快照ID',
    `total_amount`  DECIMAL(12, 2) NOT NULL                    COMMENT '订单总金额',
    `pay_amount`    DECIMAL(12, 2) NOT NULL                    COMMENT '实付金额',
    `freight`       DECIMAL(10, 2) NOT NULL DEFAULT 0.00       COMMENT '运费',
    `discount`      DECIMAL(10, 2) NOT NULL DEFAULT 0.00       COMMENT '优惠金额',
    `status`        TINYINT      NOT NULL DEFAULT 0            COMMENT '订单状态: 0-待付款, 1-已付款, 2-已发货, 3-已完成, 4-已取消, 5-已退款',
    `pay_type`      TINYINT      DEFAULT NULL                  COMMENT '支付方式: 1-支付宝, 2-微信, 3-银行卡',
    `pay_time`      DATETIME     DEFAULT NULL                  COMMENT '支付时间',
    `ship_time`     DATETIME     DEFAULT NULL                  COMMENT '发货时间',
    `receive_time`  DATETIME     DEFAULT NULL                  COMMENT '收货时间',
    `remark`        VARCHAR(500) DEFAULT ''                    COMMENT '订单备注',
    `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '下单时间',
    `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP           COMMENT '更新时间',
    PRIMARY KEY (`order_id`),
    -- 唯一约束: 订单编号唯一
    CONSTRAINT `uk_order_no` UNIQUE (`order_no`),
    -- 外键: 关联用户
    CONSTRAINT `fk_order_user_id` FOREIGN KEY (`user_id`)
        REFERENCES `tb_user` (`user_id`),
    -- 外键: 关联收货地址
    CONSTRAINT `fk_order_addr_id` FOREIGN KEY (`address_id`)
        REFERENCES `tb_user_address` (`address_id`),
    -- CHECK: 金额必须为非负
    CONSTRAINT `chk_order_amount` CHECK (`total_amount` >= 0),
    CONSTRAINT `chk_order_pay` CHECK (`pay_amount` >= 0),
    -- CHECK: 状态取值合法
    CONSTRAINT `chk_order_status` CHECK (`status` IN (0, 1, 2, 3, 4, 5)),
    -- 索引: 按用户查询订单 (常见场景)
    INDEX `idx_order_user_id` (`user_id`),
    -- 索引: 按订单状态查询
    INDEX `idx_order_status` (`status`),
    -- 复合索引: 按用户 + 状态查询订单列表
    INDEX `idx_order_user_status` (`user_id`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单表';

-- ----------------------------------------------------------------------------
-- 2.8 订单明细表 (tb_order_item)
-- 约束演示: 外键约束, DECIMAL 精度控制
-- ----------------------------------------------------------------------------
CREATE TABLE `tb_order_item`
(
    `item_id`      BIGINT UNSIGNED AUTO_INCREMENT              COMMENT '明细ID',
    `order_id`     BIGINT UNSIGNED NOT NULL                    COMMENT '所属订单ID',
    `product_id`   BIGINT UNSIGNED NOT NULL                    COMMENT '商品ID',
    `sku_id`       BIGINT UNSIGNED NOT NULL                    COMMENT 'SKU ID',
    `product_name` VARCHAR(200) NOT NULL                       COMMENT '商品名称 (快照)',
    `sku_spec`     VARCHAR(500) DEFAULT ''                     COMMENT '规格信息 (快照)',
    `unit_price`   DECIMAL(10, 2) NOT NULL                    COMMENT '购买时单价 (快照)',
    `quantity`     INT UNSIGNED NOT NULL                       COMMENT '购买数量',
    `subtotal`     DECIMAL(12, 2) NOT NULL                    COMMENT '小计金额',
    `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`item_id`),
    -- 外键: 关联订单, 删除订单时级联删除明细
    CONSTRAINT `fk_oi_order_id` FOREIGN KEY (`order_id`)
        REFERENCES `tb_order` (`order_id`) ON DELETE CASCADE,
    -- 外键: 关联商品
    CONSTRAINT `fk_oi_product_id` FOREIGN KEY (`product_id`)
        REFERENCES `tb_product` (`product_id`),
    -- 外键: 关联 SKU
    CONSTRAINT `fk_oi_sku_id` FOREIGN KEY (`sku_id`)
        REFERENCES `tb_product_sku` (`sku_id`),
    -- CHECK: 数量必须大于 0
    CONSTRAINT `chk_oi_quantity` CHECK (`quantity` > 0),
    -- CHECK: 小计金额必须为非负
    CONSTRAINT `chk_oi_subtotal` CHECK (`subtotal` >= 0),
    -- 索引: 按订单查询明细
    INDEX `idx_oi_order_id` (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单明细表';

-- ----------------------------------------------------------------------------
-- 2.9 支付记录表 (tb_payment)
-- 约束演示: 外键约束, DEFAULT NULL
-- ----------------------------------------------------------------------------
CREATE TABLE `tb_payment`
(
    `payment_id`     BIGINT UNSIGNED AUTO_INCREMENT            COMMENT '支付记录ID',
    `order_id`       BIGINT UNSIGNED NOT NULL                  COMMENT '关联订单ID',
    `trade_no`       VARCHAR(100) DEFAULT NULL                 COMMENT '第三方支付交易号',
    `pay_type`       TINYINT      NOT NULL                     COMMENT '支付方式: 1-支付宝, 2-微信, 3-银行卡',
    `pay_amount`     DECIMAL(12, 2) NOT NULL                   COMMENT '支付金额',
    `status`         TINYINT      NOT NULL DEFAULT 0           COMMENT '支付状态: 0-待支付, 1-支付成功, 2-支付失败, 3-已退款',
    `pay_time`       DATETIME     DEFAULT NULL                 COMMENT '支付完成时间',
    `created_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`payment_id`),
    -- 外键: 关联订单
    CONSTRAINT `fk_pay_order_id` FOREIGN KEY (`order_id`)
        REFERENCES `tb_order` (`order_id`),
    -- CHECK: 支付金额必须大于 0
    CONSTRAINT `chk_pay_amount` CHECK (`pay_amount` > 0),
    -- CHECK: 状态取值合法
    CONSTRAINT `chk_pay_status` CHECK (`status` IN (0, 1, 2, 3)),
    -- 索引: 按订单查询支付记录
    INDEX `idx_pay_order_id` (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='支付记录表';

-- ----------------------------------------------------------------------------
-- 2.10 商品评价表 (tb_review)
-- 约束演示: 复合唯一约束 (同一用户对同一订单明细只能评价一次)
-- ----------------------------------------------------------------------------
CREATE TABLE `tb_review`
(
    `review_id`    BIGINT UNSIGNED AUTO_INCREMENT              COMMENT '评价ID',
    `user_id`      BIGINT UNSIGNED NOT NULL                    COMMENT '评价用户ID',
    `order_id`     BIGINT UNSIGNED NOT NULL                    COMMENT '关联订单ID',
    `item_id`      BIGINT UNSIGNED NOT NULL                    COMMENT '关联订单明细ID',
    `product_id`   BIGINT UNSIGNED NOT NULL                    COMMENT '关联商品ID',
    `rating`       TINYINT      NOT NULL                       COMMENT '评分 (1-5星)',
    `content`      VARCHAR(1000) DEFAULT ''                    COMMENT '评价内容',
    `images`       VARCHAR(2000) DEFAULT ''                    COMMENT '评价图片 (JSON 数组)',
    `is_anonymous` TINYINT      NOT NULL DEFAULT 0             COMMENT '是否匿名: 0-否, 1-是',
    `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '评价时间',
    PRIMARY KEY (`review_id`),
    -- 外键: 关联用户
    CONSTRAINT `fk_rev_user_id` FOREIGN KEY (`user_id`)
        REFERENCES `tb_user` (`user_id`),
    -- 外键: 关联订单
    CONSTRAINT `fk_rev_order_id` FOREIGN KEY (`order_id`)
        REFERENCES `tb_order` (`order_id`),
    -- 外键: 关联订单明细
    CONSTRAINT `fk_rev_item_id` FOREIGN KEY (`item_id`)
        REFERENCES `tb_order_item` (`item_id`),
    -- 外键: 关联商品
    CONSTRAINT `fk_rev_product_id` FOREIGN KEY (`product_id`)
        REFERENCES `tb_product` (`product_id`),
    -- 复合唯一约束: 同一用户对同一订单明细只能评价一次
    CONSTRAINT `uk_rev_user_item` UNIQUE (`user_id`, `item_id`),
    -- CHECK: 评分范围 1-5
    CONSTRAINT `chk_rev_rating` CHECK (`rating` BETWEEN 1 AND 5),
    -- 索引: 按商品查询评价列表
    INDEX `idx_rev_product_id` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品评价表';

-- ----------------------------------------------------------------------------
-- 2.11 购物车表 (tb_cart)
-- 约束演示: 复合唯一约束 (同一用户同一 SKU 只有一条购物车记录)
-- ----------------------------------------------------------------------------
CREATE TABLE `tb_cart`
(
    `cart_id`      BIGINT UNSIGNED AUTO_INCREMENT              COMMENT '购物车记录ID',
    `user_id`      BIGINT UNSIGNED NOT NULL                    COMMENT '用户ID',
    `sku_id`       BIGINT UNSIGNED NOT NULL                    COMMENT 'SKU ID',
    `quantity`     INT UNSIGNED NOT NULL DEFAULT 1             COMMENT '数量',
    `checked`      TINYINT      NOT NULL DEFAULT 1             COMMENT '是否选中: 0-未选中, 1-已选中',
    `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '加入购物车时间',
    `updated_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                               ON UPDATE CURRENT_TIMESTAMP            COMMENT '更新时间',
    PRIMARY KEY (`cart_id`),
    -- 外键: 关联用户, 删除用户时级联删除购物车
    CONSTRAINT `fk_cart_user_id` FOREIGN KEY (`user_id`)
        REFERENCES `tb_user` (`user_id`) ON DELETE CASCADE,
    -- 外键: 关联 SKU
    CONSTRAINT `fk_cart_sku_id` FOREIGN KEY (`sku_id`)
        REFERENCES `tb_product_sku` (`sku_id`) ON DELETE CASCADE,
    -- 复合唯一约束: 同一用户的同一 SKU 只保留一条记录
    CONSTRAINT `uk_cart_user_sku` UNIQUE (`user_id`, `sku_id`),
    -- CHECK: 数量必须大于 0
    CONSTRAINT `chk_cart_quantity` CHECK (`quantity` > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='购物车表';

-- ============================================================================
-- 第三部分: 修改表 (ALTER TABLE) 演示
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 3.1 添加新列: 给用户表添加 "生日" 字段
-- ----------------------------------------------------------------------------
ALTER TABLE `tb_user` ADD COLUMN `birthday` DATE DEFAULT NULL COMMENT '生日';

-- ----------------------------------------------------------------------------
-- 3.2 添加新列并指定位置: 给用户表添加 "会员等级" 字段, 放在 status 之后
-- ----------------------------------------------------------------------------
ALTER TABLE `tb_user` ADD COLUMN `vip_level` TINYINT NOT NULL DEFAULT 0
    COMMENT '会员等级: 0-普通, 1-银卡, 2-金卡, 3-钻石' AFTER `status`;

-- ----------------------------------------------------------------------------
-- 3.3 修改列的数据类型: 将商品描述字段改为 MEDIUMTEXT (支持更长的内容)
-- ----------------------------------------------------------------------------
ALTER TABLE `tb_product` MODIFY COLUMN `description` MEDIUMTEXT COMMENT '商品详细描述 (富文本)';

-- ----------------------------------------------------------------------------
-- 3.4 修改列的名称和类型: 将商品表的 freight 相关 (假设修改订单表的 remark 列名)
-- 说明: CHANGE 可以同时修改列名和列定义, MODIFY 只能修改列定义
-- ----------------------------------------------------------------------------
ALTER TABLE `tb_order` CHANGE COLUMN `remark` `order_remark` VARCHAR(500) DEFAULT '' COMMENT '订单备注';

-- ----------------------------------------------------------------------------
-- 3.5 删除列: 删除用户表的 avatar_url 字段
-- ----------------------------------------------------------------------------
ALTER TABLE `tb_user` DROP COLUMN `avatar_url`;

-- ----------------------------------------------------------------------------
-- 3.6 添加约束: 给订单表添加一个总金额必须大于等于实付金额的 CHECK 约束
-- ----------------------------------------------------------------------------
ALTER TABLE `tb_order` ADD CONSTRAINT `chk_order_total_ge_pay`
    CHECK (`total_amount` >= `pay_amount`);

-- ----------------------------------------------------------------------------
-- 3.7 删除约束: 删除上面添加的 CHECK 约束
-- ----------------------------------------------------------------------------
ALTER TABLE `tb_order` DROP CONSTRAINT `chk_order_total_ge_pay`;

-- ----------------------------------------------------------------------------
-- 3.8 添加索引: 给商品表的价格字段添加索引 (用于价格区间筛选)
-- ----------------------------------------------------------------------------
ALTER TABLE `tb_product` ADD INDEX `idx_prod_price` (`price`);

-- ----------------------------------------------------------------------------
-- 3.9 删除索引: 删除上面添加的索引
-- ----------------------------------------------------------------------------
ALTER TABLE `tb_product` DROP INDEX `idx_prod_price`;

-- ----------------------------------------------------------------------------
-- 3.10 修改表名: 将购物车表重命名 (仅演示, 实际中不建议轻易改名)
-- ----------------------------------------------------------------------------
-- ALTER TABLE `tb_cart` RENAME TO `tb_shopping_cart`;
-- (注释掉, 避免影响后续脚本)

-- ============================================================================
-- 第四部分: 删除表 (DROP TABLE) 演示
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 4.1 删除不存在的表会报错, 使用 IF EXISTS 可以避免
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS `tb_temp_demo`;

-- ----------------------------------------------------------------------------
-- 4.2 创建临时演示表, 然后删除
-- 说明: 由于存在外键约束, 被引用的表不能直接删除, 需要先删除引用它的表
-- ----------------------------------------------------------------------------
CREATE TABLE `tb_temp_demo`
(
    `id`   INT UNSIGNED AUTO_INCREMENT COMMENT '临时ID',
    `name` VARCHAR(50) NOT NULL COMMENT '名称',
    PRIMARY KEY (`id`)
) COMMENT='临时演示表';

-- 删除临时表
DROP TABLE IF EXISTS `tb_temp_demo`;

-- ----------------------------------------------------------------------------
-- 4.3 批量删除: 可以用一条语句同时删除多张表 (注意外键依赖顺序)
-- ----------------------------------------------------------------------------
-- 示例 (已注释): DROP TABLE IF EXISTS `tb_temp_a`, `tb_temp_b`, `tb_temp_c`;

-- ============================================================================
-- 第五部分: 约束总结 (通过实例回顾)
-- ============================================================================
--
-- MySQL 支持的约束类型:
-- +----------------+----------------------------------------------------------+
-- | 约束类型        | 说明                                                      |
-- +----------------+----------------------------------------------------------+
-- | PRIMARY KEY    | 主键约束, 唯一标识一条记录, 不允许为 NULL                  |
-- | FOREIGN KEY    | 外键约束, 维护表之间的参照完整性                            |
-- | UNIQUE         | 唯一约束, 保证列 (或列组合) 的值不重复                     |
-- | NOT NULL       | 非空约束, 保证列的值不能为 NULL                            |
-- | DEFAULT        | 默认值约束, 未指定值时使用默认值                            |
-- | CHECK          | 检查约束 (MySQL 8.0.16+), 限制列值满足指定条件             |
-- | AUTO_INCREMENT | 自增约束, 自动生成唯一序列值 (仅限整数类型)                 |
-- +----------------+----------------------------------------------------------+
--
-- 外键约束的 ON DELETE / ON UPDATE 可选行为:
-- +----------------+----------------------------------------------------------+
-- | 行为            | 说明                                                      |
-- +----------------+----------------------------------------------------------+
-- | RESTRICT       | 默认值, 拒绝删除/更新被引用的记录                          |
-- | CASCADE        | 级联操作, 被引用记录删除/更新时, 引用它的记录也跟着操作     |
-- | SET NULL       | 被引用记录删除/更新时, 引用它的记录的外键列设为 NULL        |
-- | NO ACTION      | 等同于 RESTRICT (在 InnoDB 中)                             |
-- +----------------+----------------------------------------------------------+

-- ============================================================================
-- 脚本执行完毕
-- ============================================================================
