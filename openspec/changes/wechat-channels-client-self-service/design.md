## Context

当前 customer-auth 的 interaction list/detail 已投影 `runtimeControls.stored`、Edge applied version 和 effective capabilities，但 Electron 只用 `applicationStatus` 判写阻断，没有呈现读取开关和读取 capability。运行开关只能经 internal panel API 修改；回复配置也只在 Console 管理，且配置头不存在时聚合 GET 直接失败。客户端动作 handler 还把本地队列动作与平台发送 capability 绑定在一起。

本变更跨 customer-auth、Cloud store/internal API、Electron renderer/main/preload 和 Console。客户 JWT 与 internal panel JWT 必须继续保持不同权限域，renderer 不得获得任意 URL fetch、内部 JWT 或平台凭证。

## Goals / Non-Goals

**Goals:**

- 让当前环境所有者可在客户端安全地开启或关闭评论/私信读取，并看见 stored、Edge applied、effective capability 三层真态。
- 让“没有消息”“收取关闭”“本机未应用”“平台能力不可用”成为不同页面状态。
- 让不触碰平台的队列/草稿动作不再被发送 capability 静默拦截。
- 为回复配置缺失提供可达引导，并让内部管理员可在 Console 显式初始化安全 draft。
- 使用已有 `unread` 数据提供环境内未读标记、角标和去重系统通知。

**Non-Goals:**

- 不向客户 JWT 开放账号写总闸、评论回复/私信发送 capability、自动发送、风险限额、完整私信审计或配置发布权限。
- 不自动发布首次配置，不创建默认自动发送规则，不改变图片私信 v1 恒关闭。
- 不把客户端通知当作 Cloud 持久通知中心，也不新增跨设备已读同步。
- 不构建或发布 Edge 安装包；真实平台写与真实 offboard 继续使用既有人工门禁。

## Decisions

### 1. Customer API 只新增 read-controls 子资源

新增 `PUT /environments/:envKey/interactions/read-controls`，请求只含 `expectedVersion`、`commentsReadEnabled`、`dmReadEnabled`。Cloud 在既有 enabled-user、env ownership、account binding 锁内读取当前 runtime controls，以 CAS 更新两个读取字段并原样保留所有写字段，随后通过既有 runtime-control 下发链通知所属 Edge。

选择受限子资源而不是复用 internal `interaction-runtime-controls`，是为了从 schema 和 handler 层禁止客户修改写能力。renderer 仍只拿具名 IPC，不可传 path/method/header。

### 2. 页面以三层状态而不是单布尔值表达可用性

每个渠道分别展示：

1. stored read enabled：Cloud 配置意图；
2. application status：Edge 是否已应用同版本；
3. effective read capability：平台 probe 是否真实可用。

总“收取互动”开关仅是同时更新两个渠道的便利入口。任一层未就绪时，空态和局部刷新必须说明阻断原因，不能显示“同步正常”或“当前没有互动”。

### 3. 回复配置就绪状态是客户只读投影

list/detail 增加 `replyConfig`：`missing|draft_only|published`、current/draft/published version。客户可据此看见“尚未配置”“草稿未发布”或已发布版本，但不能通过 customer-auth 修改配置。客户端提供明确的“回复设置”说明入口，指向管理后台的账号回复设置路径；真正编辑/发布仍走 internal permission。

### 4. 只有平台发送动作检查发送 capability

通用 gate 继续检查当前 env、Cloud 连接、非 stale 数据、auth 和 runtime controls applied。发送按钮另加 channel send capability。保存草稿、重新生成、忽略、转人工和批准不在 renderer 预先要求平台发送 capability，最终状态/权限仍由 Cloud CAS 与业务门禁裁决。

### 5. Console 用显式初始化创建安全 draft

新增 internal `POST reply-config/initialize`，要求 `interaction.config.edit`、`expectedVersion=0`，并以 CAS/唯一键保证幂等冲突诚实。初始化复用 `DEFAULT_REPLY_POLICY` 与默认两渠道 profile，创建 draft v1；不创建模板/规则、不发布、不打开发送或自动化。Console 识别配置缺失后显示初始化说明和按钮，而不是通用加载失败。

选择显式初始化而不是 GET 隐式建数据，避免只读页面访问产生写副作用和虚假“已配置”状态。

### 6. 未读通知基于首次加载后的新增 messageId

Electron 首次成功加载只建立当前环境 seen 集合，不弹历史通知。后续刷新发现新的 `unread=true` messageId 时更新当前环境角标并通过具名 IPC 请求系统通知；同一 messageId 在进程生命周期内最多通知一次。环境切换使用 envKey 分桶，迟到回包继续丢弃。

## Risks / Trade-offs

- [客户频繁切换读取导致 Edge 控制版本抖动] → 按按钮 busy、CAS 和既有 Edge applied 回报收敛；版本冲突要求刷新后重试。
- [stored 已开但平台 probe 失败被误解为已收取] → 页面逐层展示，不用总开关颜色代表 effective 成功。
- [通知重复或历史消息刷屏] → 首次加载只建基线、按 envKey/messageId 去重、只通知后续新增未读。
- [配置初始化后用户误以为可以回复] → 明示“仅创建安全草稿，仍需模板/规则和发布”；publishedVersion 仍为空。
- [客户绕过 UI 构造写字段] → customer schema additionalProperties=false，Cloud handler allowlist，客户路由从类型上不接受写字段。

## Migration Plan

1. 先部署 Cloud：新增兼容性 customer/internal API 与只读 projection，旧 Edge/Console 不受影响。
2. 部署 Console：配置缺失时可初始化安全 draft。
3. 提交 Edge：新客户端消费新增字段和 API；旧 Cloud 缺字段时保持 unknown/fail-closed，不显示成功。
4. 在 dev 用合成账号验证 read-controls CAS、旧写字段保持不变、首次初始化和通知去重；真实平台写保持关闭。
5. 回滚时先回滚 Edge/Console，再回滚 Cloud；新增 API/字段为 additive，无数据库迁移。

## Open Questions

- 客户端未来是否直接承载模板/规则编辑，需要独立权限与产品设计；本变更先完成安全读取自助和管理后台可达性。
- 跨设备已读同步与持久通知中心不在本次范围，后续若需要应新增明确的数据模型，而不是复用 reply job state 猜测。
