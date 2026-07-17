## ADDED Requirements

### Requirement: 回复配置缺失必须由显式安全初始化恢复

internal panel API SHALL 提供 permission-gated `POST /api/accounts/:accountId/reply-config/initialize`。请求 MUST 要求 `interaction.config.edit`、`expectedVersion=0` 并验证账号 platform=`wechat_channels`；成功只创建使用默认关闭发送/自动化 policy、两渠道默认 profile 的 draft v1，不创建启用模板/规则、不发布、不修改 runtime controls。重复或并发初始化 MUST 以当前版本冲突返回，MUST NOT 覆盖既有配置。

#### Scenario: 新视频号账号初始化安全草稿
- **WHEN** 有 config.edit 权限的管理员对无 config head 的视频号账号执行初始化
- **THEN** Cloud 原子创建 draft v1、publishedVersion 仍为空、发送与自动化保持关闭，并记录无正文审计

#### Scenario: 初始化不能覆盖已有草稿或发布版本
- **WHEN** 账号已经有任意 config head 后再次调用初始化
- **THEN** Cloud 返回版本冲突与当前版本，既有模板、规则、profile 和 publishedVersion 不变化

#### Scenario: 非视频号账号不能初始化互动回复配置
- **WHEN** 管理员对 XHS 或 Facebook 账号调用初始化
- **THEN** API 返回不可用/不存在且不创建 interaction config 行

### Requirement: Console 必须把缺少配置呈现为可初始化状态

Console 回复设置抽屉 SHALL 区分 permission denied、配置缺失和普通加载失败。配置缺失时 SHALL 显示初始化说明与显式按钮；初始化成功后重新读取服务端真态并进入 draft 编辑页，MUST NOT 在按钮点击前本地伪造默认快照或显示已发布。

#### Scenario: 新账号打开回复设置
- **WHEN** 聚合配置读取返回 INTERACTION_CONFIG_MISSING
- **THEN** 页面显示“尚未初始化回复配置”和“初始化安全草稿”，而不是通用加载失败

#### Scenario: 初始化成功后仍提示未发布
- **WHEN** 初始化 API 成功并重新读取 draft v1
- **THEN** 页面显示 draft v1、published 未发布，并要求创建模板/规则和显式发布
