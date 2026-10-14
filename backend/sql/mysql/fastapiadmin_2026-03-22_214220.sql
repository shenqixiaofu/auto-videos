-- MySQL dump 10.13  Distrib 9.6.0, for macos26.2 (arm64)
--
-- Host: 127.0.0.1    Database: fastapiadmin
-- ------------------------------------------------------
-- Server version	8.4.3

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `app_myapp`
--

DROP TABLE IF EXISTS `app_myapp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `app_myapp` (
  `name` varchar(64) NOT NULL COMMENT '应用名称',
  `access_url` varchar(500) NOT NULL COMMENT '访问地址',
  `icon_url` varchar(300) DEFAULT NULL COMMENT '应用图标URL',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `uuid` varchar(64) NOT NULL COMMENT 'UUID全局唯一标识',
  `status` varchar(10) NOT NULL COMMENT '是否启用(0:启用 1:禁用)',
  `description` text COMMENT '备注/描述',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime NOT NULL COMMENT '更新时间',
  `created_id` int DEFAULT NULL COMMENT '创建人ID',
  `updated_id` int DEFAULT NULL COMMENT '更新人ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_app_myapp_uuid` (`uuid`),
  KEY `ix_app_myapp_id` (`id`),
  KEY `ix_app_myapp_updated_time` (`updated_time`),
  KEY `ix_app_myapp_updated_id` (`updated_id`),
  KEY `ix_app_myapp_created_time` (`created_time`),
  KEY `ix_app_myapp_status` (`status`),
  KEY `ix_app_myapp_created_id` (`created_id`),
  CONSTRAINT `app_myapp_ibfk_1` FOREIGN KEY (`created_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `app_myapp_ibfk_2` FOREIGN KEY (`updated_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='应用系统表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `app_myapp`
--

/*!40000 ALTER TABLE `app_myapp` DISABLE KEYS */;
/*!40000 ALTER TABLE `app_myapp` ENABLE KEYS */;

--
-- Table structure for table `apscheduler_jobs`
--

DROP TABLE IF EXISTS `apscheduler_jobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `apscheduler_jobs` (
  `id` varchar(191) NOT NULL,
  `next_run_time` double DEFAULT NULL,
  `job_state` blob NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_apscheduler_jobs_next_run_time` (`next_run_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `apscheduler_jobs`
--

/*!40000 ALTER TABLE `apscheduler_jobs` DISABLE KEYS */;
/*!40000 ALTER TABLE `apscheduler_jobs` ENABLE KEYS */;

--
-- Table structure for table `gen_demo`
--

DROP TABLE IF EXISTS `gen_demo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gen_demo` (
  `name` varchar(64) NOT NULL COMMENT '名称',
  `a` int DEFAULT NULL COMMENT '整数',
  `b` bigint DEFAULT NULL COMMENT '大整数',
  `c` float DEFAULT NULL COMMENT '浮点数',
  `d` tinyint(1) NOT NULL COMMENT '布尔型',
  `e` date DEFAULT NULL COMMENT '日期',
  `f` time DEFAULT NULL COMMENT '时间',
  `g` datetime DEFAULT NULL COMMENT '日期时间',
  `h` text COMMENT '长文本',
  `i` json DEFAULT NULL COMMENT '元数据(JSON格式)',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `uuid` varchar(64) NOT NULL COMMENT 'UUID全局唯一标识',
  `status` varchar(10) NOT NULL COMMENT '是否启用(0:启用 1:禁用)',
  `description` text COMMENT '备注/描述',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime NOT NULL COMMENT '更新时间',
  `created_id` int DEFAULT NULL COMMENT '创建人ID',
  `updated_id` int DEFAULT NULL COMMENT '更新人ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_gen_demo_uuid` (`uuid`),
  KEY `ix_gen_demo_updated_time` (`updated_time`),
  KEY `ix_gen_demo_created_id` (`created_id`),
  KEY `ix_gen_demo_id` (`id`),
  KEY `ix_gen_demo_status` (`status`),
  KEY `ix_gen_demo_updated_id` (`updated_id`),
  KEY `ix_gen_demo_created_time` (`created_time`),
  CONSTRAINT `gen_demo_ibfk_1` FOREIGN KEY (`created_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `gen_demo_ibfk_2` FOREIGN KEY (`updated_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='示例表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gen_demo`
--

/*!40000 ALTER TABLE `gen_demo` DISABLE KEYS */;
/*!40000 ALTER TABLE `gen_demo` ENABLE KEYS */;

--
-- Table structure for table `gen_table`
--

DROP TABLE IF EXISTS `gen_table`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gen_table` (
  `table_name` varchar(200) NOT NULL COMMENT '表名称',
  `table_comment` varchar(500) DEFAULT NULL COMMENT '表描述',
  `class_name` varchar(100) NOT NULL COMMENT '实体类名称',
  `package_name` varchar(100) DEFAULT NULL COMMENT '生成包路径',
  `module_name` varchar(30) DEFAULT NULL COMMENT '生成模块名',
  `business_name` varchar(30) DEFAULT NULL COMMENT '生成业务名',
  `function_name` varchar(100) DEFAULT NULL COMMENT '生成功能名',
  `sub_table_name` varchar(64) DEFAULT NULL COMMENT '关联子表的表名',
  `sub_table_fk_name` varchar(64) DEFAULT NULL COMMENT '子表关联的外键名',
  `parent_menu_id` int DEFAULT NULL COMMENT '父菜单ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `uuid` varchar(64) NOT NULL COMMENT 'UUID全局唯一标识',
  `status` varchar(10) NOT NULL COMMENT '是否启用(0:启用 1:禁用)',
  `description` text COMMENT '备注/描述',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime NOT NULL COMMENT '更新时间',
  `created_id` int DEFAULT NULL COMMENT '创建人ID',
  `updated_id` int DEFAULT NULL COMMENT '更新人ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_gen_table_uuid` (`uuid`),
  KEY `ix_gen_table_created_time` (`created_time`),
  KEY `ix_gen_table_updated_time` (`updated_time`),
  KEY `ix_gen_table_created_id` (`created_id`),
  KEY `ix_gen_table_id` (`id`),
  KEY `ix_gen_table_status` (`status`),
  KEY `ix_gen_table_updated_id` (`updated_id`),
  CONSTRAINT `gen_table_ibfk_1` FOREIGN KEY (`created_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `gen_table_ibfk_2` FOREIGN KEY (`updated_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='代码生成表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gen_table`
--

/*!40000 ALTER TABLE `gen_table` DISABLE KEYS */;
/*!40000 ALTER TABLE `gen_table` ENABLE KEYS */;

--
-- Table structure for table `gen_table_column`
--

DROP TABLE IF EXISTS `gen_table_column`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gen_table_column` (
  `column_name` varchar(200) NOT NULL COMMENT '列名称',
  `column_comment` varchar(500) DEFAULT NULL COMMENT '列描述',
  `column_type` varchar(100) NOT NULL COMMENT '列类型',
  `column_length` varchar(50) DEFAULT NULL COMMENT '列长度',
  `column_default` varchar(200) DEFAULT NULL COMMENT '列默认值',
  `is_pk` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否主键',
  `is_increment` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否自增',
  `is_nullable` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否允许为空',
  `is_unique` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否唯一',
  `python_type` varchar(100) DEFAULT NULL COMMENT 'Python类型',
  `python_field` varchar(200) DEFAULT NULL COMMENT 'Python字段名',
  `is_insert` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否为新增字段',
  `is_edit` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否编辑字段',
  `is_list` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否列表字段',
  `is_query` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否查询字段',
  `query_type` varchar(50) DEFAULT NULL COMMENT '查询方式',
  `html_type` varchar(100) DEFAULT NULL COMMENT '显示类型',
  `dict_type` varchar(200) DEFAULT NULL COMMENT '字典类型',
  `sort` int NOT NULL COMMENT '排序',
  `table_id` int NOT NULL COMMENT '归属表编号',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `uuid` varchar(64) NOT NULL COMMENT 'UUID全局唯一标识',
  `status` varchar(10) NOT NULL COMMENT '是否启用(0:启用 1:禁用)',
  `description` text COMMENT '备注/描述',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime NOT NULL COMMENT '更新时间',
  `created_id` int DEFAULT NULL COMMENT '创建人ID',
  `updated_id` int DEFAULT NULL COMMENT '更新人ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_gen_table_column_uuid` (`uuid`),
  KEY `ix_gen_table_column_created_id` (`created_id`),
  KEY `ix_gen_table_column_status` (`status`),
  KEY `ix_gen_table_column_table_id` (`table_id`),
  KEY `ix_gen_table_column_created_time` (`created_time`),
  KEY `ix_gen_table_column_updated_id` (`updated_id`),
  KEY `ix_gen_table_column_id` (`id`),
  KEY `ix_gen_table_column_updated_time` (`updated_time`),
  CONSTRAINT `gen_table_column_ibfk_1` FOREIGN KEY (`table_id`) REFERENCES `gen_table` (`id`) ON DELETE CASCADE,
  CONSTRAINT `gen_table_column_ibfk_2` FOREIGN KEY (`created_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `gen_table_column_ibfk_3` FOREIGN KEY (`updated_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='代码生成表字段';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gen_table_column`
--

/*!40000 ALTER TABLE `gen_table_column` DISABLE KEYS */;
/*!40000 ALTER TABLE `gen_table_column` ENABLE KEYS */;

--
-- Table structure for table `sys_dept`
--

DROP TABLE IF EXISTS `sys_dept`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_dept` (
  `name` varchar(64) NOT NULL COMMENT '部门名称',
  `order` int NOT NULL COMMENT '显示排序',
  `code` varchar(16) DEFAULT NULL COMMENT '部门编码',
  `leader` varchar(32) DEFAULT NULL COMMENT '部门负责人',
  `phone` varchar(11) DEFAULT NULL COMMENT '手机',
  `email` varchar(64) DEFAULT NULL COMMENT '邮箱',
  `parent_id` int DEFAULT NULL COMMENT '父级部门ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `uuid` varchar(64) NOT NULL COMMENT 'UUID全局唯一标识',
  `status` varchar(10) NOT NULL COMMENT '是否启用(0:启用 1:禁用)',
  `description` text COMMENT '备注/描述',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_sys_dept_uuid` (`uuid`),
  KEY `ix_sys_dept_status` (`status`),
  KEY `ix_sys_dept_code` (`code`),
  KEY `ix_sys_dept_created_time` (`created_time`),
  KEY `ix_sys_dept_id` (`id`),
  KEY `ix_sys_dept_parent_id` (`parent_id`),
  KEY `ix_sys_dept_updated_time` (`updated_time`),
  CONSTRAINT `sys_dept_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `sys_dept` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='部门表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_dept`
--

/*!40000 ALTER TABLE `sys_dept` DISABLE KEYS */;
INSERT INTO `sys_dept` VALUES ('集团总公司',1,'GROUP','部门负责人','1582112620','deptadmin@example.com',NULL,1,'b130be75-715b-4e4a-882a-43bee48c9530','0','集团总公司','2026-03-22 21:41:55','2026-03-22 21:41:55');
/*!40000 ALTER TABLE `sys_dept` ENABLE KEYS */;

--
-- Table structure for table `sys_dict_data`
--

DROP TABLE IF EXISTS `sys_dict_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_dict_data` (
  `dict_sort` int NOT NULL COMMENT '字典排序',
  `dict_label` varchar(255) NOT NULL COMMENT '字典标签',
  `dict_value` varchar(255) NOT NULL COMMENT '字典键值',
  `css_class` varchar(255) DEFAULT NULL COMMENT '样式属性（其他样式扩展）',
  `list_class` varchar(255) DEFAULT NULL COMMENT '表格回显样式',
  `is_default` tinyint(1) NOT NULL COMMENT '是否默认（True是 False否）',
  `dict_type` varchar(255) NOT NULL COMMENT '字典类型',
  `dict_type_id` int NOT NULL COMMENT '字典类型ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `uuid` varchar(64) NOT NULL COMMENT 'UUID全局唯一标识',
  `status` varchar(10) NOT NULL COMMENT '是否启用(0:启用 1:禁用)',
  `description` text COMMENT '备注/描述',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_sys_dict_data_uuid` (`uuid`),
  KEY `dict_type_id` (`dict_type_id`),
  KEY `ix_sys_dict_data_updated_time` (`updated_time`),
  KEY `ix_sys_dict_data_status` (`status`),
  KEY `ix_sys_dict_data_created_time` (`created_time`),
  KEY `ix_sys_dict_data_id` (`id`),
  CONSTRAINT `sys_dict_data_ibfk_1` FOREIGN KEY (`dict_type_id`) REFERENCES `sys_dict_type` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='字典数据表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_dict_data`
--

/*!40000 ALTER TABLE `sys_dict_data` DISABLE KEYS */;
INSERT INTO `sys_dict_data` VALUES (1,'男','0','blue',NULL,1,'sys_user_sex',1,1,'a3925a6b-8c5d-4564-a22a-1ecae69a85a0','0','性别男','2026-03-22 21:41:55','2026-03-22 21:41:55'),(2,'女','1','pink',NULL,0,'sys_user_sex',1,2,'c5a324ed-2af5-49bb-a2a5-04b41a8d2670','0','性别女','2026-03-22 21:41:55','2026-03-22 21:41:55'),(3,'未知','2','red',NULL,0,'sys_user_sex',1,3,'b55a204f-677e-4447-8a80-4264e6cee193','0','性别未知','2026-03-22 21:41:55','2026-03-22 21:41:55'),(1,'是','1','','primary',1,'sys_yes_no',2,4,'787d5139-f2c6-491e-98a8-1f95ccf5036a','0','是','2026-03-22 21:41:55','2026-03-22 21:41:55'),(2,'否','0','','danger',0,'sys_yes_no',2,5,'fc1bfbb5-62c4-4b22-be6b-bd78d80ae578','0','否','2026-03-22 21:41:55','2026-03-22 21:41:55'),(1,'启用','1','','primary',0,'sys_common_status',3,6,'4b477840-17e0-459b-b160-8d016f4fb552','0','启用状态','2026-03-22 21:41:55','2026-03-22 21:41:55'),(2,'停用','0','','danger',0,'sys_common_status',3,7,'11f65497-060d-4b82-bd2e-bb80385ffe86','0','停用状态','2026-03-22 21:41:55','2026-03-22 21:41:55'),(1,'通知','1','blue','warning',1,'sys_notice_type',4,8,'7baceef1-cba3-451f-987b-2c7a0ae38947','0','通知','2026-03-22 21:41:55','2026-03-22 21:41:55'),(2,'公告','2','orange','success',0,'sys_notice_type',4,9,'9a63a8ae-3323-446f-a338-fd73150136b0','0','公告','2026-03-22 21:41:55','2026-03-22 21:41:55'),(99,'其他','0','','info',0,'sys_oper_type',5,10,'b73910c6-bbf7-4b8e-8bf2-896203a37481','0','其他操作','2026-03-22 21:41:55','2026-03-22 21:41:55'),(1,'新增','1','','info',0,'sys_oper_type',5,11,'6ddcda90-ea3d-43f7-9b60-ce6564402558','0','新增操作','2026-03-22 21:41:55','2026-03-22 21:41:55'),(2,'修改','2','','info',0,'sys_oper_type',5,12,'b24f2515-22bb-442c-a23e-783d486c8944','0','修改操作','2026-03-22 21:41:55','2026-03-22 21:41:55'),(3,'删除','3','','danger',0,'sys_oper_type',5,13,'ffa4c7e4-84b4-417f-a3b1-a9c1042f72b6','0','删除操作','2026-03-22 21:41:55','2026-03-22 21:41:55'),(4,'分配权限','4','','primary',0,'sys_oper_type',5,14,'f6b6527a-88a5-4b82-ab62-46f3352b50d3','0','授权操作','2026-03-22 21:41:55','2026-03-22 21:41:55'),(5,'导出','5','','warning',0,'sys_oper_type',5,15,'1bfd138d-9ee8-4658-a214-6b87d51a8ca2','0','导出操作','2026-03-22 21:41:55','2026-03-22 21:41:55'),(6,'导入','6','','warning',0,'sys_oper_type',5,16,'757b798f-5ed7-4273-bce8-5cd0b1dd0caf','0','导入操作','2026-03-22 21:41:55','2026-03-22 21:41:55'),(7,'强退','7','','danger',0,'sys_oper_type',5,17,'5e88d6c8-68d7-4fa2-ad4d-0ea6013ff884','0','强退操作','2026-03-22 21:41:55','2026-03-22 21:41:55'),(8,'生成代码','8','','warning',0,'sys_oper_type',5,18,'9607a533-a566-4341-8395-641ac1c23cab','0','生成操作','2026-03-22 21:41:55','2026-03-22 21:41:55'),(9,'清空数据','9','','danger',0,'sys_oper_type',5,19,'df43b5b1-e74e-477e-8354-802a101848a0','0','清空操作','2026-03-22 21:41:55','2026-03-22 21:41:55'),(1,'默认(Memory)','default','',NULL,1,'sys_job_store',6,20,'8b9fcf52-22ea-4e1c-b61e-b80c49c4076e','0','默认分组','2026-03-22 21:41:55','2026-03-22 21:41:55'),(2,'数据库(Sqlalchemy)','sqlalchemy','',NULL,0,'sys_job_store',6,21,'5349390b-c79c-4801-9acd-248fcd69f7bb','0','数据库分组','2026-03-22 21:41:55','2026-03-22 21:41:55'),(3,'数据库(Redis)','redis','',NULL,0,'sys_job_store',6,22,'c225fd24-5a59-43ab-946a-b7a257b2a0ad','0','reids分组','2026-03-22 21:41:55','2026-03-22 21:41:55'),(1,'线程池','default','',NULL,0,'sys_job_executor',7,23,'2cc36ab3-a884-493f-8cf0-be8f2f9bfe7b','0','线程池','2026-03-22 21:41:55','2026-03-22 21:41:55'),(2,'进程池','processpool','',NULL,0,'sys_job_executor',7,24,'20fa32be-0db8-4f2d-8c5c-ffcf63f1a0b7','0','进程池','2026-03-22 21:41:55','2026-03-22 21:41:55'),(1,'演示函数','scheduler_test.job','',NULL,1,'sys_job_function',8,25,'3b9b2a66-eebe-41ad-850c-7f95ce46a230','0','演示函数','2026-03-22 21:41:55','2026-03-22 21:41:55'),(1,'指定日期(date)','date','',NULL,1,'sys_job_trigger',9,26,'5ac992fc-436f-4551-8dd0-65d964306c2e','0','指定日期任务触发器','2026-03-22 21:41:55','2026-03-22 21:41:55'),(2,'间隔触发器(interval)','interval','',NULL,0,'sys_job_trigger',9,27,'c4ce465f-170e-4535-80c0-7298182f2433','0','间隔触发器任务触发器','2026-03-22 21:41:55','2026-03-22 21:41:55'),(3,'cron表达式','cron','',NULL,0,'sys_job_trigger',9,28,'760117e8-5047-4d21-84a0-32873963a195','0','间隔触发器任务触发器','2026-03-22 21:41:55','2026-03-22 21:41:55'),(1,'默认(default)','default','',NULL,1,'sys_list_class',10,29,'d0d30a32-7417-40b0-9208-fde765f60342','0','默认表格回显样式','2026-03-22 21:41:55','2026-03-22 21:41:55'),(2,'主要(primary)','primary','',NULL,0,'sys_list_class',10,30,'308115be-074a-4712-ae50-115c8ab86a2d','0','主要表格回显样式','2026-03-22 21:41:55','2026-03-22 21:41:55'),(3,'成功(success)','success','',NULL,0,'sys_list_class',10,31,'fb44390d-2474-4b8f-8a57-c79af49062ae','0','成功表格回显样式','2026-03-22 21:41:55','2026-03-22 21:41:55'),(4,'信息(info)','info','',NULL,0,'sys_list_class',10,32,'3917263d-a48f-4388-9492-602486f686b5','0','信息表格回显样式','2026-03-22 21:41:55','2026-03-22 21:41:55'),(5,'警告(warning)','warning','',NULL,0,'sys_list_class',10,33,'18231fb4-cf78-49d3-93af-af47e7c3773a','0','警告表格回显样式','2026-03-22 21:41:55','2026-03-22 21:41:55'),(6,'危险(danger)','danger','',NULL,0,'sys_list_class',10,34,'cd743016-334a-47a5-af5c-400443a05cab','0','危险表格回显样式','2026-03-22 21:41:55','2026-03-22 21:41:55');
/*!40000 ALTER TABLE `sys_dict_data` ENABLE KEYS */;

--
-- Table structure for table `sys_dict_type`
--

DROP TABLE IF EXISTS `sys_dict_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_dict_type` (
  `dict_name` varchar(64) NOT NULL COMMENT '字典名称',
  `dict_type` varchar(255) NOT NULL COMMENT '字典类型',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `uuid` varchar(64) NOT NULL COMMENT 'UUID全局唯一标识',
  `status` varchar(10) NOT NULL COMMENT '是否启用(0:启用 1:禁用)',
  `description` text COMMENT '备注/描述',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `dict_type` (`dict_type`),
  UNIQUE KEY `ix_sys_dict_type_uuid` (`uuid`),
  KEY `ix_sys_dict_type_updated_time` (`updated_time`),
  KEY `ix_sys_dict_type_status` (`status`),
  KEY `ix_sys_dict_type_id` (`id`),
  KEY `ix_sys_dict_type_created_time` (`created_time`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='字典类型表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_dict_type`
--

/*!40000 ALTER TABLE `sys_dict_type` DISABLE KEYS */;
INSERT INTO `sys_dict_type` VALUES ('用户性别','sys_user_sex',1,'1acc1297-0311-493c-a76d-f6475a0abadd','0','用户性别列表','2026-03-22 21:41:55','2026-03-22 21:41:55'),('系统是否','sys_yes_no',2,'d41895b7-41e8-4ade-a548-3981bcd5be23','0','系统是否列表','2026-03-22 21:41:55','2026-03-22 21:41:55'),('系统状态','sys_common_status',3,'8f77b79d-d492-46c9-969d-a1280684af84','0','系统状态','2026-03-22 21:41:55','2026-03-22 21:41:55'),('通知类型','sys_notice_type',4,'84d2cf97-3ad2-41ee-8b48-6964e4ff2f16','0','通知类型列表','2026-03-22 21:41:55','2026-03-22 21:41:55'),('操作类型','sys_oper_type',5,'5ca9ff63-bf1b-4d24-a161-739845eae2a5','0','操作类型列表','2026-03-22 21:41:55','2026-03-22 21:41:55'),('任务存储器','sys_job_store',6,'af5b20a9-17fd-4ff6-9901-e49b751f4b4f','0','任务分组列表','2026-03-22 21:41:55','2026-03-22 21:41:55'),('任务执行器','sys_job_executor',7,'5ea092d7-3f58-42fa-9460-eb714c489a71','0','任务执行器列表','2026-03-22 21:41:55','2026-03-22 21:41:55'),('任务函数','sys_job_function',8,'cfb7a32d-c158-4d62-a30f-c588c6d810e1','0','任务函数列表','2026-03-22 21:41:55','2026-03-22 21:41:55'),('任务触发器','sys_job_trigger',9,'e0b9a395-1f81-4635-8009-c2ac9c2877ec','0','任务触发器列表','2026-03-22 21:41:55','2026-03-22 21:41:55'),('表格回显样式','sys_list_class',10,'3932a1de-713e-40d0-8c4a-efdabb9b1c6f','0','表格回显样式列表','2026-03-22 21:41:55','2026-03-22 21:41:55');
/*!40000 ALTER TABLE `sys_dict_type` ENABLE KEYS */;

--
-- Table structure for table `sys_log`
--

DROP TABLE IF EXISTS `sys_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_log` (
  `type` int NOT NULL COMMENT '日志类型(1登录日志 2操作日志)',
  `request_path` varchar(255) NOT NULL COMMENT '请求路径',
  `request_method` varchar(10) NOT NULL COMMENT '请求方式',
  `request_payload` longtext COMMENT '请求体',
  `request_ip` varchar(50) DEFAULT NULL COMMENT '请求IP地址',
  `login_location` varchar(255) DEFAULT NULL COMMENT '登录位置',
  `request_os` varchar(64) DEFAULT NULL COMMENT '操作系统',
  `request_browser` varchar(64) DEFAULT NULL COMMENT '浏览器',
  `response_code` int NOT NULL COMMENT '响应状态码',
  `response_json` longtext COMMENT '响应体',
  `process_time` varchar(20) DEFAULT NULL COMMENT '处理时间',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `uuid` varchar(64) NOT NULL COMMENT 'UUID全局唯一标识',
  `status` varchar(10) NOT NULL COMMENT '是否启用(0:启用 1:禁用)',
  `description` text COMMENT '备注/描述',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime NOT NULL COMMENT '更新时间',
  `created_id` int DEFAULT NULL COMMENT '创建人ID',
  `updated_id` int DEFAULT NULL COMMENT '更新人ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_sys_log_uuid` (`uuid`),
  KEY `ix_sys_log_status` (`status`),
  KEY `ix_sys_log_created_id` (`created_id`),
  KEY `ix_sys_log_updated_time` (`updated_time`),
  KEY `ix_sys_log_id` (`id`),
  KEY `ix_sys_log_updated_id` (`updated_id`),
  KEY `ix_sys_log_created_time` (`created_time`),
  CONSTRAINT `sys_log_ibfk_1` FOREIGN KEY (`created_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `sys_log_ibfk_2` FOREIGN KEY (`updated_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='系统日志表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_log`
--

/*!40000 ALTER TABLE `sys_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `sys_log` ENABLE KEYS */;

--
-- Table structure for table `sys_menu`
--

DROP TABLE IF EXISTS `sys_menu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_menu` (
  `name` varchar(50) NOT NULL COMMENT '菜单名称',
  `type` int NOT NULL COMMENT '菜单类型(1:目录 2:菜单 3:按钮/权限 4:链接)',
  `order` int NOT NULL COMMENT '显示排序',
  `permission` varchar(100) DEFAULT NULL COMMENT '权限标识(如:module_system:user:query)',
  `icon` varchar(50) DEFAULT NULL COMMENT '菜单图标',
  `route_name` varchar(100) DEFAULT NULL COMMENT '路由名称',
  `route_path` varchar(200) DEFAULT NULL COMMENT '路由路径',
  `component_path` varchar(200) DEFAULT NULL COMMENT '组件路径',
  `redirect` varchar(200) DEFAULT NULL COMMENT '重定向地址',
  `hidden` tinyint(1) NOT NULL COMMENT '是否隐藏(True:隐藏 False:显示)',
  `keep_alive` tinyint(1) NOT NULL COMMENT '是否缓存(True:是 False:否)',
  `always_show` tinyint(1) NOT NULL COMMENT '是否始终显示(True:是 False:否)',
  `title` varchar(50) DEFAULT NULL COMMENT '菜单标题',
  `params` json DEFAULT NULL COMMENT '路由参数(JSON对象)',
  `affix` tinyint(1) NOT NULL COMMENT '是否固定标签页(True:是 False:否)',
  `parent_id` int DEFAULT NULL COMMENT '父菜单ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `uuid` varchar(64) NOT NULL COMMENT 'UUID全局唯一标识',
  `status` varchar(10) NOT NULL COMMENT '是否启用(0:启用 1:禁用)',
  `description` text COMMENT '备注/描述',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_sys_menu_uuid` (`uuid`),
  KEY `ix_sys_menu_updated_time` (`updated_time`),
  KEY `ix_sys_menu_status` (`status`),
  KEY `ix_sys_menu_created_time` (`created_time`),
  KEY `ix_sys_menu_id` (`id`),
  KEY `ix_sys_menu_parent_id` (`parent_id`),
  CONSTRAINT `sys_menu_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `sys_menu` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=156 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='菜单表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_menu`
--

/*!40000 ALTER TABLE `sys_menu` DISABLE KEYS */;
INSERT INTO `sys_menu` VALUES ('仪表盘',1,1,'','client','Dashboard','/dashboard',NULL,'/dashboard/workplace',0,1,1,'仪表盘','null',0,NULL,1,'c8e5563e-4331-4d26-bdf2-939b2cdb3cfb','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('系统管理',1,2,NULL,'system','System','/system',NULL,'/system/menu',0,1,0,'系统管理','null',0,NULL,2,'77c07b3b-1d62-4579-abda-9b9dd43282ad','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('监控管理',1,3,NULL,'monitor','Monitor','/monitor',NULL,'/monitor/online',0,1,0,'监控管理','null',0,NULL,3,'e04a642a-4c72-4d0f-8e66-ada7b49039b5','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('接口管理',1,4,NULL,'document','Common','/common',NULL,'/common/docs',0,1,0,'接口管理','null',0,NULL,4,'dc6f403b-1c25-471c-b7c0-8f9ca9a91610','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('代码管理',1,5,NULL,'code','Generator','/generator',NULL,'/generator/gencode',0,1,0,'代码管理','null',0,NULL,5,'0ed5686b-6598-4671-966c-b904d683ef02','0','代码管理','2026-03-22 21:41:55','2026-03-22 21:41:55'),('应用管理',1,6,NULL,'el-icon-ShoppingBag','Application','/application',NULL,'/application/myapp',0,1,0,'应用管理','null',0,NULL,6,'2ba38a17-a5fa-47b5-9225-d8309336cfe8','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('AI管理',1,7,NULL,'el-icon-ChatLineSquare','AI','/ai',NULL,'/ai/chat',0,1,0,'AI管理','null',0,NULL,7,'876e6273-b524-4f3c-ba22-04dd2e09cf02','0','AI管理','2026-03-22 21:41:55','2026-03-22 21:41:55'),('任务管理',1,8,NULL,'el-icon-SetUp','Task','/task',NULL,'/task/job',0,1,0,'任务管理','null',0,NULL,8,'4a0632bc-a8d7-4880-aa6a-8d40d23c4b29','0','任务管理','2026-03-22 21:41:55','2026-03-22 21:41:55'),('案例管理',1,9,NULL,'menu','Example','/example',NULL,'/example/demo',0,1,0,'案例管理','null',0,NULL,9,'80a94935-63f6-46ce-b9bd-a387391ab8d1','0','案例管理','2026-03-22 21:41:55','2026-03-22 21:41:55'),('工作台',2,1,'dashboard:workplace:query','el-icon-PieChart','Workplace','/dashboard/workplace','dashboard/workplace',NULL,0,1,0,'工作台','null',0,1,10,'a22dc48b-4ad9-4e0e-b9e1-dd27d685721c','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('菜单管理',2,1,'module_system:menu:query','menu','Menu','/system/menu','module_system/menu/index',NULL,0,1,0,'菜单管理','null',0,2,11,'1b3cc062-9ddd-4c17-a7fb-323f0e32140c','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('部门管理',2,2,'module_system:dept:query','tree','Dept','/system/dept','module_system/dept/index',NULL,0,1,0,'部门管理','null',0,2,12,'4aec1ecd-43a5-4c9a-ade0-a3ac152e6110','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('岗位管理',2,3,'module_system:position:query','el-icon-Coordinate','Position','/system/position','module_system/position/index',NULL,0,1,0,'岗位管理','null',0,2,13,'708b84a3-e4b2-4341-80bb-ce353f9ad470','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('角色管理',2,4,'module_system:role:query','role','Role','/system/role','module_system/role/index',NULL,0,1,0,'角色管理','null',0,2,14,'42ecfa54-4976-44e3-a698-1023dcdd6679','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('用户管理',2,5,'module_system:user:query','el-icon-User','User','/system/user','module_system/user/index',NULL,0,1,0,'用户管理','null',0,2,15,'f2a2916b-4325-490c-b9f7-eb8c887f85c4','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('日志管理',2,6,'module_system:log:query','el-icon-Aim','Log','/system/log','module_system/log/index',NULL,0,1,0,'日志管理','null',0,2,16,'43ee9ddf-0353-4793-83dd-f195e0be1f5d','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('公告管理',2,7,'module_system:notice:query','bell','Notice','/system/notice','module_system/notice/index',NULL,0,1,0,'公告管理','null',0,2,17,'b464f8de-f898-4f1a-ada1-0acd30cb9b0e','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('参数管理',2,8,'module_system:param:query','setting','Params','/system/param','module_system/param/index',NULL,0,1,0,'参数管理','null',0,2,18,'3f74c540-bc88-4809-a073-eb92d9e1de4a','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('字典管理',2,9,'module_system:dict_type:query','dict','Dict','/system/dict','module_system/dict/index',NULL,0,1,0,'字典管理','null',0,2,19,'eb64e13c-c9f8-4d72-aa65-aef65058d00c','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('在线用户',2,1,'module_monitor:online:query','el-icon-Headset','MonitorOnline','/monitor/online','module_monitor/online/index',NULL,0,1,0,'在线用户','null',0,3,20,'1a9eee50-bbf3-4974-a96c-3206f3ab7e63','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('服务器监控',2,2,'module_monitor:server:query','el-icon-Odometer','MonitorServer','/monitor/server','module_monitor/server/index',NULL,0,1,0,'服务器监控','null',0,3,21,'3ca31c2e-d85b-4094-af4a-5ec53ed19897','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('缓存监控',2,3,'module_monitor:cache:query','el-icon-Stopwatch','MonitorCache','/monitor/cache','module_monitor/cache/index',NULL,0,1,0,'缓存监控','null',0,3,22,'ba5a4983-28ce-4954-bf9e-3cf8231eb26c','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('文件管理',2,4,'module_monitor:resource:query','el-icon-Files','Resource','/monitor/resource','module_monitor/resource/index',NULL,0,1,0,'文件管理','null',0,3,23,'f98f60e2-36fe-426f-94ac-d6cce6e7ca8a','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('Swagger文档',4,1,'module_common:docs:query','api','Docs','/common/docs','module_common/docs/index',NULL,0,1,0,'Swagger文档','null',0,4,24,'5646002f-adca-4309-9d60-c772b8554699','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('Redoc文档',4,2,'module_common:redoc:query','el-icon-Document','Redoc','/common/redoc','module_common/redoc/index',NULL,0,1,0,'Redoc文档','null',0,4,25,'216530ad-a777-4bad-aa6f-c68e00d82771','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('LangJin文档',4,3,'module_common:ljdoc:query','el-icon-Document','Ljdoc','/common/ljdoc','module_common/ljdoc/index',NULL,0,1,0,'LangJin文档','null',0,4,26,'d239ebe8-b225-443e-b638-68207b57ecd6','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('代码生成',2,1,'module_generator:gencode:query','code','GenCode','/generator/gencode','module_generator/gencode/index',NULL,0,1,0,'代码生成','null',0,5,27,'b66b82c9-8ccc-41ad-9a30-351f09ed35e0','0','代码生成','2026-03-22 21:41:55','2026-03-22 21:41:55'),('我的应用',2,1,'module_application:myapp:query','el-icon-ShoppingCartFull','MYAPP','/application/myapp','module_application/myapp/index',NULL,0,1,0,'我的应用','null',0,6,28,'efd03910-5105-4f33-a705-3dae504594c1','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('AI智能助手',2,1,'module_ai:chat:query','el-icon-ChatDotRound','Chat','/ai/chat','module_ai/chat/index',NULL,0,1,0,'AI智能助手','null',0,7,29,'9946ccc6-4e71-4be4-82d6-a3448533644f','0','AI智能助手','2026-03-22 21:41:55','2026-03-22 21:41:55'),('会话记忆',2,2,'module_ai:chat:query','el-icon-ChatLineSquare','Memory','/ai/memory','module_ai/memory/index',NULL,0,1,0,'会话记忆','null',0,7,30,'4bab8591-f650-4358-a178-43b589a0b651','0','会话记忆管理','2026-03-22 21:41:55','2026-03-22 21:41:55'),('调度器监控',2,1,'module_task:job:query','el-icon-DataLine','Job','/task/job','module_task/job/index',NULL,0,1,0,'调度器监控','null',0,8,31,'a630154c-f6ef-4872-94bd-04523de6a8bf','0','调度器监控','2026-03-22 21:41:55','2026-03-22 21:41:55'),('节点管理',2,2,'module_task:node:query','el-icon-Postcard','Node','/task/node','module_task/node/index',NULL,0,1,0,'节点管理','null',0,8,32,'67b567e2-66c1-425d-9cf4-ecf294de0090','0','节点管理','2026-03-22 21:41:55','2026-03-22 21:41:55'),('示例管理',2,1,'module_example:demo:query','menu','Demo','/example/demo','module_example/demo/index',NULL,0,1,0,'示例管理','null',0,9,33,'e2349f7f-3da8-4121-828d-74ae5fe11bbb','0','示例管理','2026-03-22 21:41:55','2026-03-22 21:41:55'),('创建菜单',3,1,'module_system:menu:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建菜单','null',0,11,34,'f4cc190e-1e2e-46b0-ac5d-51359fc2dcf1','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('修改菜单',3,2,'module_system:menu:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改菜单','null',0,11,35,'11dcc82f-6aed-41da-8fe2-96b031c7585c','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('删除菜单',3,3,'module_system:menu:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除菜单','null',0,11,36,'3095209c-44ab-4bec-9703-cbb7e0bb65e7','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('批量修改菜单状态',3,4,'module_system:menu:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改菜单状态','null',0,11,37,'18d42376-cf61-4ef3-8ec2-9c933de2196f','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('详情菜单',3,5,'module_system:menu:detail',NULL,NULL,NULL,NULL,NULL,0,1,0,'详情菜单','null',0,11,38,'3fc01b1f-3644-4087-8310-5f5042012aef','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('查询菜单',3,6,'module_system:menu:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'查询菜单','null',0,11,39,'908405d7-c48c-49ff-90e8-e417535abd66','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('创建部门',3,1,'module_system:dept:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建部门','null',0,12,40,'23063e04-0fd8-4c4b-9079-0243b80544b5','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('修改部门',3,2,'module_system:dept:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改部门','null',0,12,41,'229eb072-ad37-4457-be27-053d5479950e','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('删除部门',3,3,'module_system:dept:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除部门','null',0,12,42,'76d7cdc8-2567-499d-86e8-3792c8ebc738','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('批量修改部门状态',3,4,'module_system:dept:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改部门状态','null',0,12,43,'11596dee-cd04-48b0-a514-f002a76aed6c','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('详情部门',3,5,'module_system:dept:detail',NULL,NULL,NULL,NULL,NULL,0,1,0,'详情部门','null',0,12,44,'fa3c9930-2703-4be1-b9ca-9fbdc55a47f2','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('查询部门',3,6,'module_system:dept:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'查询部门','null',0,12,45,'30d7441f-4b04-42c6-88af-a376c0991f04','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('创建岗位',3,1,'module_system:position:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建岗位','null',0,13,46,'e4bacd6e-33d8-4ccf-8a8a-5a7f87786dd4','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('修改岗位',3,2,'module_system:position:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改岗位','null',0,13,47,'11975c57-9040-4140-85b0-94cc85c90604','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('删除岗位',3,3,'module_system:position:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改岗位','null',0,13,48,'7f5392c3-f8f3-422e-a161-7c9babc386f1','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('批量修改岗位状态',3,4,'module_system:position:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改岗位状态','null',0,13,49,'cb3e5b6c-d315-44f1-a9a3-4ae8a7803272','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('岗位导出',3,5,'module_system:position:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'岗位导出','null',0,13,50,'1da12377-f702-4950-98dc-1e5c26b8d0d0','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('详情岗位',3,6,'module_system:position:detail',NULL,NULL,NULL,NULL,NULL,0,1,0,'详情岗位','null',0,13,51,'189cb3db-6a10-49b7-8309-e1f595bc001d','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('查询岗位',3,7,'module_system:position:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'查询岗位','null',0,13,52,'b057a38c-52b2-4d70-b7d9-d4becc112f70','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('创建角色',3,1,'module_system:role:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建角色','null',0,14,53,'f713b931-3f5b-4748-ab72-fc9cf126023e','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('修改角色',3,2,'module_system:role:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改角色','null',0,14,54,'9f8ea2d0-b901-4ac5-8fe1-2af9bc939c51','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('删除角色',3,3,'module_system:role:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除角色','null',0,14,55,'79d1b0c6-8283-4bfc-9be4-331f247cd5c9','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('批量修改角色状态',3,4,'module_system:role:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改角色状态','null',0,14,56,'3ffef25d-01c9-440b-8397-5215cd65d286','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('角色导出',3,5,'module_system:role:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'角色导出','null',0,14,57,'28b88a67-072c-4fec-8450-0b7e88d6d349','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('详情角色',3,6,'module_system:role:detail',NULL,NULL,NULL,NULL,NULL,0,1,0,'详情角色','null',0,14,58,'bda987b7-480d-428b-9b74-4f8bc2227a65','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('查询角色',3,7,'module_system:role:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'查询角色','null',0,14,59,'5fc2aa84-90fb-4bbf-816a-1cba1cb142f4','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('分配权限',3,8,'module_system:role:permission',NULL,NULL,NULL,NULL,NULL,0,1,0,'分配权限','null',0,14,60,'bc99a1b8-a13d-4f17-9b43-222050db5213','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('创建用户',3,1,'module_system:user:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建用户','null',0,15,61,'3d514b08-b345-4a56-8e7d-34761edd6f71','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('修改用户',3,2,'module_system:user:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改用户','null',0,15,62,'a8b48297-f6ca-4041-968a-1ccb5c585ed5','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('删除用户',3,3,'module_system:user:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除用户','null',0,15,63,'b65c0699-2274-4f0f-a911-d806a932d2cd','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('批量修改用户状态',3,4,'module_system:user:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改用户状态','null',0,15,64,'375f94c4-31a5-48db-ab97-5c2168d66869','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('导出用户',3,5,'module_system:user:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出用户','null',0,15,65,'eb5cb1ea-8ca5-48fd-81c8-1e2ae9b1d7ea','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('导入用户',3,6,'module_system:user:import',NULL,NULL,NULL,NULL,NULL,0,1,0,'导入用户','null',0,15,66,'3fe12532-ebd0-456f-8593-bdf86397e20a','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('下载用户导入模板',3,7,'module_system:user:download',NULL,NULL,NULL,NULL,NULL,0,1,0,'下载用户导入模板','null',0,15,67,'b57173c3-24b9-41e2-994d-9cff7d35a1ee','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('详情用户',3,8,'module_system:user:detail',NULL,NULL,NULL,NULL,NULL,0,1,0,'详情用户','null',0,15,68,'bf7afe3e-f6ab-4246-9c2d-df8d9e6e0a58','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('查询用户',3,9,'module_system:user:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'查询用户','null',0,15,69,'9ba01eb4-f708-4dff-b428-505c5ad7f710','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('日志删除',3,1,'module_system:log:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'日志删除','null',0,16,70,'83cc14be-be84-459b-968e-76a6c958d7ab','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('日志导出',3,2,'module_system:log:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'日志导出','null',0,16,71,'873557f8-38c3-4d54-9178-80cacde860f1','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('日志详情',3,3,'module_system:log:detail',NULL,NULL,NULL,NULL,NULL,0,1,0,'日志详情','null',0,16,72,'1099842f-41aa-4e73-b98e-c87d2aacbb5e','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('查询日志',3,4,'module_system:log:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'查询日志','null',0,16,73,'e8d7a433-7e13-4f5b-a221-3af7d3dad109','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('公告创建',3,1,'module_system:notice:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'公告创建','null',0,17,74,'093c1e15-8862-4206-8574-5ccb518fa9e1','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('公告修改',3,2,'module_system:notice:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改用户','null',0,17,75,'e008baca-3169-4f9f-be8c-da91fe66106d','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('公告删除',3,3,'module_system:notice:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'公告删除','null',0,17,76,'510597ed-9b94-40a3-91e3-177c6f63bdfa','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('公告导出',3,4,'module_system:notice:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'公告导出','null',0,17,77,'021495d0-7aa8-4865-8d00-a2217f4225da','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('公告批量修改状态',3,5,'module_system:notice:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'公告批量修改状态','null',0,17,78,'4d06a7a5-30c7-4a37-9b6e-d782e80bd3b0','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('公告详情',3,6,'module_system:notice:detail',NULL,NULL,NULL,NULL,NULL,0,1,0,'公告详情','null',0,17,79,'5cbafddd-a54e-4bdc-80b2-5592a73c46fb','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('查询公告',3,5,'module_system:notice:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'查询公告','null',0,17,80,'b6d352fe-e02b-491b-ab8d-d4a354eae18d','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('创建参数',3,1,'module_system:param:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建参数','null',0,18,81,'eaa07086-239c-48fc-a111-0999048bd71f','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('修改参数',3,2,'module_system:param:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改参数','null',0,18,82,'acb1f953-4e45-4b41-a137-256075d722aa','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('删除参数',3,3,'module_system:param:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除参数','null',0,18,83,'6c285e44-758b-452f-93c5-252baaa0daf2','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('导出参数',3,4,'module_system:param:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出参数','null',0,18,84,'2ccbbeba-36d4-45f1-89c7-0af6ef46ca68','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('参数上传',3,5,'module_system:param:upload',NULL,NULL,NULL,NULL,NULL,0,1,0,'参数上传','null',0,18,85,'4c0cf360-fc13-414c-8ead-98499f6ae57f','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('参数详情',3,6,'module_system:param:detail',NULL,NULL,NULL,NULL,NULL,0,1,0,'参数详情','null',0,18,86,'356065bd-409b-4390-8518-097824780aee','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('查询参数',3,7,'module_system:param:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'查询参数','null',0,18,87,'4153828a-193c-438e-9cf6-8b1d59260e99','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('创建字典类型',3,1,'module_system:dict_type:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建字典类型','null',0,19,88,'8bd900fc-3fb4-4b16-9160-de288a5e4275','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('修改字典类型',3,2,'module_system:dict_type:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改字典类型','null',0,19,89,'c311c342-f240-431a-ae6d-c50ef5453f7b','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('删除字典类型',3,3,'module_system:dict_type:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除字典类型','null',0,19,90,'85f1e068-9d71-49bc-858e-c498e6f2a1f0','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('导出字典类型',3,4,'module_system:dict_type:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出字典类型','null',0,19,91,'2566fab6-2687-4544-921a-a46b2ca884f1','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('批量修改字典状态',3,5,'module_system:dict_type:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出字典类型','null',0,19,92,'2506453f-d7f5-4385-bb9a-4ee0ff227e79','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('字典数据查询',3,6,'module_system:dict_data:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'字典数据查询','null',0,19,93,'893184ea-1f7e-48bb-a1d9-fd2c8b6fcef2','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('创建字典数据',3,7,'module_system:dict_data:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建字典数据','null',0,19,94,'691361a1-c0b0-40e1-aece-34dba317ca21','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('修改字典数据',3,8,'module_system:dict_data:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改字典数据','null',0,19,95,'590ddb32-ee9d-4f43-8cdc-8dcedf4059c5','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('删除字典数据',3,9,'module_system:dict_data:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除字典数据','null',0,19,96,'6ce3604d-7167-4fb9-afcf-344c4d967e2c','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('导出字典数据',3,10,'module_system:dict_data:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出字典数据','null',0,19,97,'09476164-b3d5-4d95-bf5a-e675b9132f6f','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('批量修改字典数据状态',3,11,'module_system:dict_data:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改字典数据状态','null',0,19,98,'2c0e368e-f756-4c2a-a175-7b5a89866383','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('详情字典类型',3,12,'module_system:dict_type:detail',NULL,NULL,NULL,NULL,NULL,0,1,0,'详情字典类型','null',0,19,99,'e41cb820-fad4-4ddf-8cda-d4801bffa9b3','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('查询字典类型',3,13,'module_system:dict_type:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'查询字典类型','null',0,19,100,'625502ab-d491-471b-b542-8068b95a8f88','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('详情字典数据',3,14,'module_system:dict_data:detail',NULL,NULL,NULL,NULL,NULL,0,1,0,'详情字典数据','null',0,19,101,'25340ec4-3c6d-4d27-ad67-520706ac330e','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('在线用户强制下线',3,1,'module_monitor:online:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'在线用户强制下线','null',0,20,102,'659c8c01-24ce-4219-8206-460190ff3a29','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('清除缓存',3,1,'module_monitor:cache:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'清除缓存','null',0,22,103,'d6cf75f9-91cb-4b45-bf0b-d6522123432b','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('文件上传',3,1,'module_monitor:resource:upload',NULL,NULL,NULL,NULL,NULL,0,1,0,'文件上传','null',0,23,104,'1cb9d7ee-1bc7-4733-853a-9520c1d1b0d3','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('文件下载',3,2,'module_monitor:resource:download',NULL,NULL,NULL,NULL,NULL,0,1,0,'文件下载','null',0,23,105,'2b728756-5c55-4c7e-929d-7d51615c32ba','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('文件删除',3,3,'module_monitor:resource:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'文件删除','null',0,23,106,'bdece4a3-541e-407e-9af9-01043bc81e06','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('文件移动',3,4,'module_monitor:resource:move',NULL,NULL,NULL,NULL,NULL,0,1,0,'文件移动','null',0,23,107,'6d7ed601-afdc-4be1-9da8-0623afad7651','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('文件复制',3,5,'module_monitor:resource:copy',NULL,NULL,NULL,NULL,NULL,0,1,0,'文件复制','null',0,23,108,'43fbede9-b02c-49c3-9709-59e80cc3da24','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('文件重命名',3,6,'module_monitor:resource:rename',NULL,NULL,NULL,NULL,NULL,0,1,0,'文件重命名','null',0,23,109,'3c3c0209-4909-418c-877b-c7d02b36a33a','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('创建目录',3,7,'module_monitor:resource:create_dir',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建目录','null',0,23,110,'6bf6f087-0ec2-4696-ae8e-27f7f7857153','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('导出文件列表',3,9,'module_monitor:resource:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出文件列表','null',0,23,111,'2a35b375-07af-42f3-97b7-e0579c45fe74','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('查询代码生成业务表列表',3,1,'module_generator:gencode:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'查询代码生成业务表列表','null',0,27,112,'63db7b17-1463-48df-b321-e4be9e4d9da0','0','查询代码生成业务表列表','2026-03-22 21:41:55','2026-03-22 21:41:55'),('创建表结构',3,2,'module_generator:gencode:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建表结构','null',0,27,113,'76a88c93-8161-46e0-8e2c-09a6066696dd','0','创建表结构','2026-03-22 21:41:55','2026-03-22 21:41:55'),('编辑业务表信息',3,3,'module_generator:gencode:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'编辑业务表信息','null',0,27,114,'84584564-8ede-45a2-88c6-ff1f19a3c3e3','0','编辑业务表信息','2026-03-22 21:41:55','2026-03-22 21:41:55'),('删除业务表信息',3,4,'module_generator:gencode:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除业务表信息','null',0,27,115,'a6ffd80d-1a5c-4c83-9e76-cfbdc2e7ff2b','0','删除业务表信息','2026-03-22 21:41:55','2026-03-22 21:41:55'),('导入表结构',3,5,'module_generator:gencode:import',NULL,NULL,NULL,NULL,NULL,0,1,0,'导入表结构','null',0,27,116,'9bb618a3-405a-4e8e-9231-c76991a1dc4b','0','导入表结构','2026-03-22 21:41:55','2026-03-22 21:41:55'),('批量生成代码',3,6,'module_generator:gencode:operate',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量生成代码','null',0,27,117,'c81af38a-4329-47e7-8360-c4bd9030b197','0','批量生成代码','2026-03-22 21:41:55','2026-03-22 21:41:55'),('生成代码到指定路径',3,7,'module_generator:gencode:code',NULL,NULL,NULL,NULL,NULL,0,1,0,'生成代码到指定路径','null',0,27,118,'350104ad-9e7f-4639-91ce-a57efed4e34b','0','生成代码到指定路径','2026-03-22 21:41:55','2026-03-22 21:41:55'),('查询数据库表列表',3,8,'module_generator:dblist:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'查询数据库表列表','null',0,27,119,'e6ade0c6-42d8-4cc4-95c5-a322791a7504','0','查询数据库表列表','2026-03-22 21:41:55','2026-03-22 21:41:55'),('同步数据库',3,9,'module_generator:db:sync',NULL,NULL,NULL,NULL,NULL,0,1,0,'同步数据库','null',0,27,120,'f8328984-15cf-4c13-9b4c-73161328293c','0','同步数据库','2026-03-22 21:41:55','2026-03-22 21:41:55'),('创建应用',3,1,'module_application:myapp:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建应用','null',0,28,121,'5a5c6f48-d23d-4787-af53-d0ca4f46f940','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('修改应用',3,2,'module_application:myapp:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改应用','null',0,28,122,'6c50b13c-30ee-4f23-9181-6a015767f0a4','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('删除应用',3,3,'module_application:myapp:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除应用','null',0,28,123,'0468eebd-21f0-44c1-b302-6bb21674e710','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('批量修改应用状态',3,4,'module_application:myapp:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改应用状态','null',0,28,124,'18757f4d-97b6-48ea-a68d-b8cadc322e35','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('详情应用',3,5,'module_application:myapp:detail',NULL,NULL,NULL,NULL,NULL,0,1,0,'详情应用','null',0,28,125,'72d27543-8182-412f-8f48-a33b54ad294f','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('查询应用',3,6,'module_application:myapp:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'查询应用','null',0,28,126,'be55c811-c1e3-431a-a410-775660f87c59','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('AI对话',3,1,'module_ai:chat:ws',NULL,NULL,NULL,NULL,NULL,0,1,0,'AI对话','null',0,29,127,'f3ab61b1-061e-46ee-b3d3-039ee35cb470','0','AI对话','2026-03-22 21:41:55','2026-03-22 21:41:55'),('查询会话',3,2,'module_ai:chat:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'查询会话','null',0,29,128,'2b217acd-01db-4d7a-a70e-8c946e0b5d4d','0','查询会话','2026-03-22 21:41:55','2026-03-22 21:41:55'),('会话详情',3,3,'module_ai:chat:detail',NULL,NULL,NULL,NULL,NULL,0,1,0,'会话详情','null',0,29,129,'0a0dbf2e-46b8-44a8-bf94-b8a75a377a04','0','会话详情','2026-03-22 21:41:55','2026-03-22 21:41:55'),('创建会话',3,4,'module_ai:chat:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建会话','null',0,29,130,'e58425ca-1b7e-4e1e-9da6-0a3496ea7c43','0','创建会话','2026-03-22 21:41:55','2026-03-22 21:41:55'),('更新会话',3,5,'module_ai:chat:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'更新会话','null',0,29,131,'2011a7ef-2326-4ddf-81ff-f27a1af9b6c7','0','更新会话','2026-03-22 21:41:55','2026-03-22 21:41:55'),('删除会话',3,6,'module_ai:chat:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除会话','null',0,29,132,'d8519110-6303-4fb3-aa08-35b0344037a0','0','删除会话','2026-03-22 21:41:55','2026-03-22 21:41:55'),('查询会话记忆',3,1,'module_ai:chat:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'查询会话记忆','null',0,30,133,'506eb504-f1ab-4a3d-bf53-b436f0349bc1','0','查询会话记忆','2026-03-22 21:41:55','2026-03-22 21:41:55'),('会话记忆详情',3,2,'module_ai:chat:detail',NULL,NULL,NULL,NULL,NULL,0,1,0,'会话记忆详情','null',0,30,134,'6894b999-b1ba-4d3e-98de-5b4f05e6d561','0','会话记忆详情','2026-03-22 21:41:55','2026-03-22 21:41:55'),('删除会话记忆',3,3,'module_ai:chat:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除会话记忆','null',0,30,135,'ccbff8c1-0d60-4179-83b8-a2bac7681609','0','删除会话记忆','2026-03-22 21:41:55','2026-03-22 21:41:55'),('查询调度器',3,1,'module_task:job:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'查询调度器','null',0,31,136,'67d88f16-fa1f-4f50-bf36-b05bf3dd29fc','0','查询调度器','2026-03-22 21:41:55','2026-03-22 21:41:55'),('控制调度器',3,2,'module_task:job:scheduler',NULL,NULL,NULL,NULL,NULL,0,1,0,'控制调度器','null',0,31,137,'428cce0d-f075-45f8-97fd-db3a921c850d','0','控制调度器','2026-03-22 21:41:55','2026-03-22 21:41:55'),('操作任务',3,3,'module_task:job:task',NULL,NULL,NULL,NULL,NULL,0,1,0,'操作任务','null',0,31,138,'cb72ac39-6e44-407c-9730-dd2d9d6948f0','0','操作任务','2026-03-22 21:41:55','2026-03-22 21:41:55'),('删除执行日志',3,4,'module_task:job:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除执行日志','null',0,31,139,'c3717657-016d-4756-9a6f-2eebb7891ba9','0','删除执行日志','2026-03-22 21:41:55','2026-03-22 21:41:55'),('详情执行日志',3,5,'module_task:job:detail',NULL,NULL,NULL,NULL,NULL,0,1,0,'详情执行日志','null',0,31,140,'8b20e41d-30b2-4a8f-9550-b1b4f54ffa3f','0','详情执行日志','2026-03-22 21:41:55','2026-03-22 21:41:55'),('创建节点',3,1,'module_task:node:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建节点','null',0,32,141,'9fd327f5-30fc-40d5-9712-04e4744f63a0','0','创建节点','2026-03-22 21:41:55','2026-03-22 21:41:55'),('调试节点',3,2,'module_task:node:execute',NULL,NULL,NULL,NULL,NULL,0,1,0,'调试节点','null',0,32,142,'c2f5b117-4823-4632-93b8-0c5f3a13182e','0','调试节点','2026-03-22 21:41:55','2026-03-22 21:41:55'),('修改节点',3,3,'module_task:node:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'修改节点','null',0,32,143,'139fffda-448e-4ae6-a70a-04d686f3a72c','0','修改节点','2026-03-22 21:41:55','2026-03-22 21:41:55'),('删除节点',3,4,'module_task:node:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除节点','null',0,32,144,'4dc81ef6-ac7c-4cb6-82f8-d377e2bbec7a','0','删除节点','2026-03-22 21:41:55','2026-03-22 21:41:55'),('详情节点',3,5,'module_task:node:detail',NULL,NULL,NULL,NULL,NULL,0,1,0,'详情节点','null',0,32,145,'aa302d6c-60c3-45c6-9477-2245c4e72aff','0','详情节点','2026-03-22 21:41:55','2026-03-22 21:41:55'),('查询节点',3,6,'module_task:node:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'查询节点','null',0,32,146,'de803d31-2ccc-4b37-9dab-24611e89fdd6','0','查询节点','2026-03-22 21:41:55','2026-03-22 21:41:55'),('创建示例',3,1,'module_example:demo:create',NULL,NULL,NULL,NULL,NULL,0,1,0,'创建示例','null',0,33,147,'5dcf446f-f2d5-492d-a2e2-309961a8e519','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('更新示例',3,2,'module_example:demo:update',NULL,NULL,NULL,NULL,NULL,0,1,0,'更新示例','null',0,33,148,'8a3092db-79c9-4c35-a58b-8eb1f4d255ba','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('删除示例',3,3,'module_example:demo:delete',NULL,NULL,NULL,NULL,NULL,0,1,0,'删除示例','null',0,33,149,'64753421-b9fd-4f63-b5eb-f67962954bb8','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('批量修改示例状态',3,4,'module_example:demo:patch',NULL,NULL,NULL,NULL,NULL,0,1,0,'批量修改示例状态','null',0,33,150,'5c3e7d59-0dbe-484d-8bba-b80d75a104b3','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('导出示例',3,5,'module_example:demo:export',NULL,NULL,NULL,NULL,NULL,0,1,0,'导出示例','null',0,33,151,'d57144c6-3392-48a9-b64f-249d97dfd606','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('导入示例',3,6,'module_example:demo:import',NULL,NULL,NULL,NULL,NULL,0,1,0,'导入示例','null',0,33,152,'0e59c64b-1693-49bf-addd-3fd1b1a1b62f','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('下载导入示例模版',3,7,'module_example:demo:download',NULL,NULL,NULL,NULL,NULL,0,1,0,'下载导入示例模版','null',0,33,153,'4ff86544-47d1-4467-8276-7545a41ec170','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('详情示例',3,8,'module_example:demo:detail',NULL,NULL,NULL,NULL,NULL,0,1,0,'详情示例','null',0,33,154,'d49f0b07-3926-407a-9345-f9888f0cc980','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('查询示例',3,9,'module_example:demo:query',NULL,NULL,NULL,NULL,NULL,0,1,0,'查询示例','null',0,33,155,'6da2f9be-c8e6-454e-9f65-ac0cf4bac935','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55');
/*!40000 ALTER TABLE `sys_menu` ENABLE KEYS */;

--
-- Table structure for table `sys_notice`
--

DROP TABLE IF EXISTS `sys_notice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_notice` (
  `notice_title` varchar(64) NOT NULL COMMENT '公告标题',
  `notice_type` varchar(1) NOT NULL COMMENT '公告类型(1通知 2公告)',
  `notice_content` text COMMENT '公告内容',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `uuid` varchar(64) NOT NULL COMMENT 'UUID全局唯一标识',
  `status` varchar(10) NOT NULL COMMENT '是否启用(0:启用 1:禁用)',
  `description` text COMMENT '备注/描述',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime NOT NULL COMMENT '更新时间',
  `created_id` int DEFAULT NULL COMMENT '创建人ID',
  `updated_id` int DEFAULT NULL COMMENT '更新人ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_sys_notice_uuid` (`uuid`),
  KEY `ix_sys_notice_updated_time` (`updated_time`),
  KEY `ix_sys_notice_id` (`id`),
  KEY `ix_sys_notice_created_id` (`created_id`),
  KEY `ix_sys_notice_status` (`status`),
  KEY `ix_sys_notice_updated_id` (`updated_id`),
  KEY `ix_sys_notice_created_time` (`created_time`),
  CONSTRAINT `sys_notice_ibfk_1` FOREIGN KEY (`created_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `sys_notice_ibfk_2` FOREIGN KEY (`updated_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='通知公告表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_notice`
--

/*!40000 ALTER TABLE `sys_notice` DISABLE KEYS */;
/*!40000 ALTER TABLE `sys_notice` ENABLE KEYS */;

--
-- Table structure for table `sys_param`
--

DROP TABLE IF EXISTS `sys_param`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_param` (
  `config_name` varchar(64) NOT NULL COMMENT '参数名称',
  `config_key` varchar(500) NOT NULL COMMENT '参数键名',
  `config_value` varchar(500) DEFAULT NULL COMMENT '参数键值',
  `config_type` tinyint(1) DEFAULT NULL COMMENT '系统内置(True:是 False:否)',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `uuid` varchar(64) NOT NULL COMMENT 'UUID全局唯一标识',
  `status` varchar(10) NOT NULL COMMENT '是否启用(0:启用 1:禁用)',
  `description` text COMMENT '备注/描述',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_sys_param_uuid` (`uuid`),
  KEY `ix_sys_param_updated_time` (`updated_time`),
  KEY `ix_sys_param_status` (`status`),
  KEY `ix_sys_param_id` (`id`),
  KEY `ix_sys_param_created_time` (`created_time`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='系统参数表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_param`
--

/*!40000 ALTER TABLE `sys_param` DISABLE KEYS */;
INSERT INTO `sys_param` VALUES ('网站名称','sys_web_title','FastApiAdmin',1,1,'18f6b43f-b2c0-4ef8-94ee-a0750c38ab4f','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('网站描述','sys_web_description','FastApiAdmin 是完全开源的权限管理系统',1,2,'4e8f70cc-1d43-46ae-916b-6e6969367fad','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('网页图标','sys_web_favicon','https://service.fastapiadmin.com/api/v1/static/image/favicon.png',1,3,'fb114b74-2e26-42ff-8492-84c044ba7b0a','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('网站Logo','sys_web_logo','https://service.fastapiadmin.com/api/v1/static/image/logo.png',1,4,'df42b3de-de17-42d2-a2bc-3a9071d7b2ed','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('登录背景','sys_login_background','https://service.fastapiadmin.com/api/v1/static/image/background.svg',1,5,'fa11ca40-ecba-46c4-8080-54d46f9af5b3','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('版权信息','sys_web_copyright','Copyright © 2025-2026 service.fastapiadmin.com 版权所有',1,6,'47cde296-be9c-4905-a776-7990a96f6924','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('备案信息','sys_keep_record','陕ICP备2025069493号-1',1,7,'2e7f6174-ae08-4f32-9dcd-411bca3f6e04','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('帮助文档','sys_help_doc','https://service.fastapiadmin.com',1,8,'5a28b4d5-f62b-4e7c-b5e1-00c7a121b83a','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('隐私政策','sys_web_privacy','https://github.com/fastapiadmin/FastapiAdmin/blob/master/LICENSE',1,9,'7065d0ed-59b1-4336-9602-a4c437fcc191','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('用户协议','sys_web_clause','https://github.com/fastapiadmin/FastapiAdmin/blob/master/LICENSE',1,10,'1ee04427-c9ed-4688-ab57-62db4efadc94','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('源码代码','sys_git_code','https://github.com/fastapiadmin/FastapiAdmin.git',1,11,'e114486c-8a8a-4b34-9758-392c3b96180f','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('项目版本','sys_web_version','2.0.0',1,12,'cb570b8d-4610-4806-97cd-b35fcca4620a','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('演示模式启用','demo_enable','false',1,13,'94b844c2-078c-43a3-ad06-5a7eef9a5a14','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('演示访问IP白名单','ip_white_list','[\"127.0.0.1\"]',1,14,'e5ccafa1-b38a-403c-aec6-3805453f90d0','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('接口白名单','white_api_list_path','[\"/api/v1/system/auth/login\", \"/api/v1/system/auth/token/refresh\", \"/api/v1/system/auth/captcha/get\", \"/api/v1/system/auth/logout\", \"/api/v1/system/config/info\", \"/api/v1/system/user/current/info\", \"/api/v1/system/notice/available\", \"/api/v1/system/auth/auto-login/users\", \"/api/v1/system/auth/auto-login/token\", \"/api/v1/system/auth/auto-login\"]',1,15,'5b55e073-d71d-48a9-990d-fbab63f455cd','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('访问IP黑名单','ip_black_list','[]',1,16,'28a9e77d-3cd5-4db4-9885-ec9b0d9c4d42','0','初始化数据','2026-03-22 21:41:55','2026-03-22 21:41:55'),('调度器状态','scheduler_status','stopped',1,17,'175f6e33-e6f2-447e-8cd4-4e5251c7e089','0',NULL,'2026-03-22 21:42:06','2026-03-22 21:42:06');
/*!40000 ALTER TABLE `sys_param` ENABLE KEYS */;

--
-- Table structure for table `sys_position`
--

DROP TABLE IF EXISTS `sys_position`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_position` (
  `name` varchar(64) NOT NULL COMMENT '岗位名称',
  `order` int NOT NULL COMMENT '显示排序',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `uuid` varchar(64) NOT NULL COMMENT 'UUID全局唯一标识',
  `status` varchar(10) NOT NULL COMMENT '是否启用(0:启用 1:禁用)',
  `description` text COMMENT '备注/描述',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime NOT NULL COMMENT '更新时间',
  `created_id` int DEFAULT NULL COMMENT '创建人ID',
  `updated_id` int DEFAULT NULL COMMENT '更新人ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_sys_position_uuid` (`uuid`),
  KEY `ix_sys_position_created_id` (`created_id`),
  KEY `ix_sys_position_updated_id` (`updated_id`),
  KEY `ix_sys_position_status` (`status`),
  KEY `ix_sys_position_id` (`id`),
  KEY `ix_sys_position_updated_time` (`updated_time`),
  KEY `ix_sys_position_created_time` (`created_time`),
  CONSTRAINT `sys_position_ibfk_1` FOREIGN KEY (`created_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `sys_position_ibfk_2` FOREIGN KEY (`updated_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='岗位表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_position`
--

/*!40000 ALTER TABLE `sys_position` DISABLE KEYS */;
/*!40000 ALTER TABLE `sys_position` ENABLE KEYS */;

--
-- Table structure for table `sys_role`
--

DROP TABLE IF EXISTS `sys_role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_role` (
  `name` varchar(64) NOT NULL COMMENT '角色名称',
  `code` varchar(16) DEFAULT NULL COMMENT '角色编码',
  `order` int NOT NULL COMMENT '显示排序',
  `data_scope` int NOT NULL COMMENT '数据权限范围(1:仅本人 2:本部门 3:本部门及以下 4:全部 5:自定义)',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `uuid` varchar(64) NOT NULL COMMENT 'UUID全局唯一标识',
  `status` varchar(10) NOT NULL COMMENT '是否启用(0:启用 1:禁用)',
  `description` text COMMENT '备注/描述',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_sys_role_uuid` (`uuid`),
  KEY `ix_sys_role_created_time` (`created_time`),
  KEY `ix_sys_role_code` (`code`),
  KEY `ix_sys_role_status` (`status`),
  KEY `ix_sys_role_id` (`id`),
  KEY `ix_sys_role_updated_time` (`updated_time`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='角色表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_role`
--

/*!40000 ALTER TABLE `sys_role` DISABLE KEYS */;
INSERT INTO `sys_role` VALUES ('管理员角色','ADMIN',1,4,1,'06b86f22-0105-42e7-b9d6-b36614f4e2eb','0','初始化角色','2026-03-22 21:41:55','2026-03-22 21:41:55');
/*!40000 ALTER TABLE `sys_role` ENABLE KEYS */;

--
-- Table structure for table `sys_role_depts`
--

DROP TABLE IF EXISTS `sys_role_depts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_role_depts` (
  `role_id` int NOT NULL COMMENT '角色ID',
  `dept_id` int NOT NULL COMMENT '部门ID',
  PRIMARY KEY (`role_id`,`dept_id`),
  KEY `dept_id` (`dept_id`),
  CONSTRAINT `sys_role_depts_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `sys_role` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `sys_role_depts_ibfk_2` FOREIGN KEY (`dept_id`) REFERENCES `sys_dept` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='角色部门关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_role_depts`
--

/*!40000 ALTER TABLE `sys_role_depts` DISABLE KEYS */;
/*!40000 ALTER TABLE `sys_role_depts` ENABLE KEYS */;

--
-- Table structure for table `sys_role_menus`
--

DROP TABLE IF EXISTS `sys_role_menus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_role_menus` (
  `role_id` int NOT NULL COMMENT '角色ID',
  `menu_id` int NOT NULL COMMENT '菜单ID',
  PRIMARY KEY (`role_id`,`menu_id`),
  KEY `menu_id` (`menu_id`),
  CONSTRAINT `sys_role_menus_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `sys_role` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `sys_role_menus_ibfk_2` FOREIGN KEY (`menu_id`) REFERENCES `sys_menu` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='角色菜单关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_role_menus`
--

/*!40000 ALTER TABLE `sys_role_menus` DISABLE KEYS */;
/*!40000 ALTER TABLE `sys_role_menus` ENABLE KEYS */;

--
-- Table structure for table `sys_user`
--

DROP TABLE IF EXISTS `sys_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_user` (
  `username` varchar(64) NOT NULL COMMENT '用户名/登录账号',
  `password` varchar(255) NOT NULL COMMENT '密码哈希',
  `name` varchar(32) NOT NULL COMMENT '昵称',
  `mobile` varchar(11) DEFAULT NULL COMMENT '手机号',
  `email` varchar(64) DEFAULT NULL COMMENT '邮箱',
  `gender` varchar(1) DEFAULT NULL COMMENT '性别(0:男 1:女 2:未知)',
  `avatar` varchar(255) DEFAULT NULL COMMENT '头像URL地址',
  `is_superuser` tinyint(1) NOT NULL COMMENT '是否超管',
  `last_login` datetime DEFAULT NULL COMMENT '最后登录时间',
  `gitee_login` varchar(32) DEFAULT NULL COMMENT 'Gitee登录',
  `github_login` varchar(32) DEFAULT NULL COMMENT 'Github登录',
  `wx_login` varchar(32) DEFAULT NULL COMMENT '微信登录',
  `qq_login` varchar(32) DEFAULT NULL COMMENT 'QQ登录',
  `dept_id` int DEFAULT NULL COMMENT '部门ID',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `uuid` varchar(64) NOT NULL COMMENT 'UUID全局唯一标识',
  `status` varchar(10) NOT NULL COMMENT '是否启用(0:启用 1:禁用)',
  `description` text COMMENT '备注/描述',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime NOT NULL COMMENT '更新时间',
  `created_id` int DEFAULT NULL COMMENT '创建人ID',
  `updated_id` int DEFAULT NULL COMMENT '更新人ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `ix_sys_user_uuid` (`uuid`),
  UNIQUE KEY `mobile` (`mobile`),
  UNIQUE KEY `email` (`email`),
  KEY `ix_sys_user_updated_id` (`updated_id`),
  KEY `ix_sys_user_created_time` (`created_time`),
  KEY `ix_sys_user_updated_time` (`updated_time`),
  KEY `ix_sys_user_id` (`id`),
  KEY `ix_sys_user_created_id` (`created_id`),
  KEY `ix_sys_user_dept_id` (`dept_id`),
  KEY `ix_sys_user_status` (`status`),
  CONSTRAINT `sys_user_ibfk_1` FOREIGN KEY (`dept_id`) REFERENCES `sys_dept` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `sys_user_ibfk_2` FOREIGN KEY (`created_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `sys_user_ibfk_3` FOREIGN KEY (`updated_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_user`
--

/*!40000 ALTER TABLE `sys_user` DISABLE KEYS */;
INSERT INTO `sys_user` VALUES ('admin','$2b$12$e2IJgS/cvHgJ0H3G7Xa08OXoXnk6N/NX3IZRtubBDElA0VLZhkNOa','超级管理员',NULL,NULL,'0','https://service.fastapiadmin.com/api/v1/static/image/avatar.png',1,NULL,NULL,NULL,NULL,NULL,1,1,'e10a66c6-a5a5-4367-8f5e-54d30b1f8631','0','超级管理员','2026-03-22 21:41:55','2026-03-22 21:41:55',NULL,NULL);
/*!40000 ALTER TABLE `sys_user` ENABLE KEYS */;

--
-- Table structure for table `sys_user_positions`
--

DROP TABLE IF EXISTS `sys_user_positions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_user_positions` (
  `user_id` int NOT NULL COMMENT '用户ID',
  `position_id` int NOT NULL COMMENT '岗位ID',
  PRIMARY KEY (`user_id`,`position_id`),
  KEY `position_id` (`position_id`),
  CONSTRAINT `sys_user_positions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `sys_user_positions_ibfk_2` FOREIGN KEY (`position_id`) REFERENCES `sys_position` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户岗位关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_user_positions`
--

/*!40000 ALTER TABLE `sys_user_positions` DISABLE KEYS */;
/*!40000 ALTER TABLE `sys_user_positions` ENABLE KEYS */;

--
-- Table structure for table `sys_user_roles`
--

DROP TABLE IF EXISTS `sys_user_roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_user_roles` (
  `user_id` int NOT NULL COMMENT '用户ID',
  `role_id` int NOT NULL COMMENT '角色ID',
  PRIMARY KEY (`user_id`,`role_id`),
  KEY `role_id` (`role_id`),
  CONSTRAINT `sys_user_roles_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `sys_user_roles_ibfk_2` FOREIGN KEY (`role_id`) REFERENCES `sys_role` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户角色关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_user_roles`
--

/*!40000 ALTER TABLE `sys_user_roles` DISABLE KEYS */;
INSERT INTO `sys_user_roles` VALUES (1,1);
/*!40000 ALTER TABLE `sys_user_roles` ENABLE KEYS */;

--
-- Table structure for table `task_job`
--

DROP TABLE IF EXISTS `task_job`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `task_job` (
  `job_id` varchar(64) NOT NULL COMMENT '任务ID',
  `job_name` varchar(128) DEFAULT NULL COMMENT '任务名称',
  `trigger_type` varchar(32) DEFAULT NULL COMMENT '触发方式: cron/interval/date/manual',
  `status` varchar(16) NOT NULL COMMENT '执行状态',
  `next_run_time` varchar(64) DEFAULT NULL COMMENT '下次执行时间',
  `job_state` text COMMENT '任务状态信息',
  `result` text COMMENT '执行结果',
  `error` text COMMENT '错误信息',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `uuid` varchar(64) NOT NULL COMMENT 'UUID全局唯一标识',
  `description` text COMMENT '备注/描述',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_task_job_uuid` (`uuid`),
  KEY `ix_task_job_created_time` (`created_time`),
  KEY `ix_task_job_id` (`id`),
  KEY `ix_task_job_updated_time` (`updated_time`),
  KEY `ix_task_job_job_id` (`job_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='任务执行日志表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `task_job`
--

/*!40000 ALTER TABLE `task_job` DISABLE KEYS */;
/*!40000 ALTER TABLE `task_job` ENABLE KEYS */;

--
-- Table structure for table `task_node`
--

DROP TABLE IF EXISTS `task_node`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `task_node` (
  `name` varchar(64) NOT NULL COMMENT '节点名称',
  `code` varchar(32) NOT NULL COMMENT '节点编码',
  `jobstore` varchar(64) DEFAULT NULL COMMENT '存储器',
  `executor` varchar(64) DEFAULT NULL COMMENT '执行器',
  `trigger` varchar(64) DEFAULT NULL COMMENT '触发器',
  `trigger_args` text COMMENT '触发器参数',
  `func` text COMMENT '代码块',
  `args` text COMMENT '位置参数',
  `kwargs` text COMMENT '关键字参数',
  `coalesce` tinyint(1) DEFAULT NULL COMMENT '是否合并运行',
  `max_instances` int DEFAULT NULL COMMENT '最大实例数',
  `start_date` varchar(64) DEFAULT NULL COMMENT '开始时间',
  `end_date` varchar(64) DEFAULT NULL COMMENT '结束时间',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `uuid` varchar(64) NOT NULL COMMENT 'UUID全局唯一标识',
  `status` varchar(10) NOT NULL COMMENT '是否启用(0:启用 1:禁用)',
  `description` text COMMENT '备注/描述',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime NOT NULL COMMENT '更新时间',
  `created_id` int DEFAULT NULL COMMENT '创建人ID',
  `updated_id` int DEFAULT NULL COMMENT '更新人ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  UNIQUE KEY `ix_task_node_uuid` (`uuid`),
  KEY `ix_task_node_updated_time` (`updated_time`),
  KEY `ix_task_node_created_id` (`created_id`),
  KEY `ix_task_node_status` (`status`),
  KEY `ix_task_node_updated_id` (`updated_id`),
  KEY `ix_task_node_created_time` (`created_time`),
  KEY `ix_task_node_id` (`id`),
  CONSTRAINT `task_node_ibfk_1` FOREIGN KEY (`created_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `task_node_ibfk_2` FOREIGN KEY (`updated_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='节点类型表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `task_node`
--

/*!40000 ALTER TABLE `task_node` DISABLE KEYS */;
/*!40000 ALTER TABLE `task_node` ENABLE KEYS */;

--
-- Dumping routines for database 'fastapiadmin'
--
--
-- WARNING: can't read the INFORMATION_SCHEMA.libraries table. It's most probably an old server 8.4.3.
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-03-22 21:42:26
