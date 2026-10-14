-- 智能视频 / 自动剪辑 菜单与权限 SQL
-- 幂等规则：目录、页面和按钮分别通过固定路由、组件路径和权限标识判重。
-- 角色授权规则：
-- 1. 优先复制一级目录“AI应用”已有的角色范围；
-- 2. 当前仓库初始化数据没有“AI应用”，因此无匹配授权时复制“AI管理”（route_name = 'AI'）的角色范围；
-- 3. 如果上述两个菜单均无角色授权，则只授予角色编码为 ADMIN 的管理员角色。

START TRANSACTION;

-- 新增一级目录“智能视频”
INSERT INTO `sys_menu` (
  `uuid`,
  `status`,
  `name`,
  `type`,
  `order`,
  `permission`,
  `icon`,
  `route_name`,
  `route_path`,
  `component_path`,
  `redirect`,
  `hidden`,
  `keep_alive`,
  `always_show`,
  `title`,
  `params`,
  `affix`,
  `parent_id`,
  `description`,
  `created_time`,
  `updated_time`
)
SELECT
  REPLACE(UUID(), '-', ''),
  '0',
  '智能视频',
  1,
  root_order.`next_order`,
  NULL,
  'el-icon-VideoCamera',
  'Video',
  '/video',
  NULL,
  '/video/processing',
  0,
  1,
  1,
  '智能视频',
  NULL,
  0,
  NULL,
  '视频素材输入、自动剪辑与成片输出',
  NOW(),
  NOW()
FROM (
  SELECT COALESCE(MAX(`order`), 0) + 1 AS `next_order`
  FROM `sys_menu`
  WHERE `parent_id` IS NULL
) root_order
WHERE NOT EXISTS (
  SELECT 1
  FROM `sys_menu`
  WHERE `type` = 1
    AND (
      `route_name` = 'Video'
      OR `route_path` = '/video'
      OR `name` = '智能视频'
    )
);

-- 新增子菜单“自动剪辑”
INSERT INTO `sys_menu` (
  `uuid`,
  `status`,
  `name`,
  `type`,
  `order`,
  `permission`,
  `icon`,
  `route_name`,
  `route_path`,
  `component_path`,
  `redirect`,
  `hidden`,
  `keep_alive`,
  `always_show`,
  `title`,
  `params`,
  `affix`,
  `parent_id`,
  `description`,
  `created_time`,
  `updated_time`
)
SELECT
  REPLACE(UUID(), '-', ''),
  '0',
  '自动剪辑',
  2,
  1,
  'module_video:processing:query',
  'el-icon-VideoPlay',
  'VideoProcessing',
  '/video/processing',
  'module_video/processing/index',
  NULL,
  0,
  1,
  0,
  '自动剪辑',
  NULL,
  0,
  video_root.`id`,
  '提交视频素材并查看自动剪辑任务及成片产物',
  NOW(),
  NOW()
FROM (
  SELECT `id`
  FROM `sys_menu`
  WHERE `type` = 1
    AND (
      `route_name` = 'Video'
      OR `route_path` = '/video'
      OR `name` = '智能视频'
    )
  ORDER BY CASE
    WHEN `route_name` = 'Video' THEN 1
    WHEN `route_path` = '/video' THEN 2
    ELSE 3
  END
  LIMIT 1
) video_root
WHERE NOT EXISTS (
  SELECT 1
  FROM `sys_menu`
  WHERE `type` = 2
    AND (
      `route_name` = 'VideoProcessing'
      OR `route_path` = '/video/processing'
      OR `component_path` = 'module_video/processing/index'
    )
);

-- 新增自动剪辑页面的按钮权限
INSERT INTO `sys_menu` (
  `uuid`,
  `status`,
  `name`,
  `type`,
  `order`,
  `permission`,
  `icon`,
  `route_name`,
  `route_path`,
  `component_path`,
  `redirect`,
  `hidden`,
  `keep_alive`,
  `always_show`,
  `title`,
  `params`,
  `affix`,
  `parent_id`,
  `description`,
  `created_time`,
  `updated_time`
)
SELECT
  REPLACE(UUID(), '-', ''),
  '0',
  permission_def.`name`,
  3,
  permission_def.`order`,
  permission_def.`permission`,
  NULL,
  NULL,
  NULL,
  NULL,
  NULL,
  0,
  1,
  0,
  permission_def.`name`,
  NULL,
  0,
  processing_page.`id`,
  permission_def.`description`,
  NOW(),
  NOW()
FROM (
  SELECT `id`
  FROM `sys_menu`
  WHERE `type` = 2
    AND (
      `route_name` = 'VideoProcessing'
      OR `route_path` = '/video/processing'
      OR `component_path` = 'module_video/processing/index'
    )
  ORDER BY CASE
    WHEN `component_path` = 'module_video/processing/index' THEN 1
    WHEN `route_name` = 'VideoProcessing' THEN 2
    ELSE 3
  END
  LIMIT 1
) processing_page
CROSS JOIN (
  SELECT 1 AS `order`, '查询自动剪辑任务' AS `name`,
         'module_video:processing:query' AS `permission`, '自动剪辑任务查询权限' AS `description`
  UNION ALL
  SELECT 2, '创建自动剪辑任务', 'module_video:processing:create', '自动剪辑任务创建权限'
  UNION ALL
  SELECT 3, '取消自动剪辑任务', 'module_video:processing:cancel', '自动剪辑任务取消权限'
  UNION ALL
  SELECT 4, '重试自动剪辑任务', 'module_video:processing:retry', '自动剪辑任务重试权限'
  UNION ALL
  SELECT 5, '下载自动剪辑产物', 'module_video:processing:download', '自动剪辑产物下载权限'
  UNION ALL
  SELECT 6, '配置自动剪辑参数', 'module_video:processing:config', '自动剪辑全局配置读写权限'
) permission_def
WHERE NOT EXISTS (
  SELECT 1
  FROM `sys_menu` existing_permission
  WHERE existing_permission.`type` = 3
    AND existing_permission.`permission` = permission_def.`permission`
);

-- 为目录、页面及按钮统一复制角色范围，避免只授权页面却看不到一级目录
INSERT INTO `sys_role_menus` (`role_id`, `menu_id`)
SELECT DISTINCT
  source_roles.`role_id`,
  target_menu.`id`
FROM (
  -- 第一优先级：复制“AI应用”一级目录的角色授权
  SELECT ai_application_roles.`role_id`
  FROM (
    SELECT DISTINCT source_role_menu.`role_id`
    FROM `sys_role_menus` source_role_menu
    JOIN `sys_menu` source_menu
      ON source_menu.`id` = source_role_menu.`menu_id`
    WHERE source_menu.`type` = 1
      AND source_menu.`name` = 'AI应用'
  ) ai_application_roles

  UNION ALL

  -- 第二优先级：不存在“AI应用”角色授权时，复制仓库已有“AI管理”的角色授权
  SELECT ai_management_roles.`role_id`
  FROM (
    SELECT DISTINCT source_role_menu.`role_id`
    FROM `sys_role_menus` source_role_menu
    JOIN `sys_menu` source_menu
      ON source_menu.`id` = source_role_menu.`menu_id`
    WHERE source_menu.`type` = 1
      AND (
        source_menu.`route_name` = 'AI'
        OR source_menu.`name` = 'AI管理'
      )
  ) ai_management_roles
  WHERE NOT EXISTS (
    SELECT 1
    FROM `sys_role_menus` source_role_menu
    JOIN `sys_menu` source_menu
      ON source_menu.`id` = source_role_menu.`menu_id`
    WHERE source_menu.`type` = 1
      AND source_menu.`name` = 'AI应用'
  )

  UNION ALL

  -- 最终回退：两个参照目录均无授权时，仅授予 ADMIN 角色
  SELECT admin_role.`id`
  FROM `sys_role` admin_role
  WHERE admin_role.`code` = 'ADMIN'
    AND NOT EXISTS (
      SELECT 1
      FROM `sys_role_menus` source_role_menu
      JOIN `sys_menu` source_menu
        ON source_menu.`id` = source_role_menu.`menu_id`
      WHERE source_menu.`type` = 1
        AND (
          source_menu.`name` = 'AI应用'
          OR source_menu.`route_name` = 'AI'
          OR source_menu.`name` = 'AI管理'
        )
    )
) source_roles
JOIN `sys_menu` target_menu
  ON (
    (
      target_menu.`type` = 1
      AND (
        target_menu.`route_name` = 'Video'
        OR target_menu.`route_path` = '/video'
        OR target_menu.`name` = '智能视频'
      )
    )
    OR (
      target_menu.`type` = 2
      AND (
        target_menu.`route_name` = 'VideoProcessing'
        OR target_menu.`route_path` = '/video/processing'
        OR target_menu.`component_path` = 'module_video/processing/index'
      )
    )
    OR (
      target_menu.`type` = 3
      AND       target_menu.`permission` IN (
        'module_video:processing:query',
        'module_video:processing:create',
        'module_video:processing:cancel',
        'module_video:processing:retry',
        'module_video:processing:download',
        'module_video:processing:config'
      )
    )
  )
WHERE NOT EXISTS (
  SELECT 1
  FROM `sys_role_menus` existing_role_menu
  WHERE existing_role_menu.`role_id` = source_roles.`role_id`
    AND existing_role_menu.`menu_id` = target_menu.`id`
);

COMMIT;
