# facebook-auto-persona-fill Specification

## Purpose
TBD - created by archiving change facebook-cloud-auto-persona-fill. Update Purpose after archive.
## Requirements
### Requirement: Facebook 筛选入口打开批量人设选择页面

桌面外壳 SHALL 仅在环境栏平台筛选为 Facebook 时显示“批量设置人设”入口。点击后 SHALL 打开现有账号人设浮层的批量模式，让用户在其中选择语气、点赞倾向、内容偏好和发言语言，并预览将用于全部缺失账号的同一份人设。环境栏 MUST NOT 再显示独立语言选择；其他平台及“全部”筛选 MUST 隐藏入口。

#### Scenario: 人工选择批量人设
- **WHEN** 客户筛选 Facebook 环境并点击“批量设置人设”
- **THEN** 客户端打开人设选择页，说明只处理未设置账号且所有目标使用同一份人设，用户未确认前不创建 Cloud 运行

#### Scenario: 其他分类没有入口
- **WHEN** 环境栏筛选为全部、小红书或视频号
- **THEN** 批量人设入口隐藏且不能从该视图提交运行

### Requirement: 批量模板由客户端选择确定且不调用 Cloud 生成器

批量模式 SHALL 根据用户已选择的语气、点赞倾向、内容偏好和 Facebook 发言语言，在客户端确定性构建一份合法 `soulYaml` 并展示预览。相同选择 SHALL 产生相同模板；该路径 MUST NOT 调用 `persona.generate`、PersonaGenerator、方向池或按账号差异化生成。单账号人设生成路径不受本要求影响。

#### Scenario: 生成批量模板预览
- **WHEN** 用户完成全部必选项并点击生成人设
- **THEN** 客户端本地构建一份含所选语言与偏好的 `soulYaml`，进入预览确认，不发送模型生成请求

#### Scenario: 修改选择后重新预览
- **WHEN** 用户返回修改任一偏好并再次生成
- **THEN** 客户端以新选择替换草稿；未点击确认批量设置前 Cloud 不筛选或写入账号

### Requirement: 客户端只提交已确认人设且不提交目标 ID

用户确认批量人设后，Edge SHALL 经 customer-auth 提交严格的 `{ platform: "facebook", soulYaml }` 和主进程生成的 Idempotency-Key。MUST NOT 提交账号 ID、环境 ID、客户 ID、客户端人设状态、`strategy`、独立 `writingLanguage`、账号凭据、cookie、2FA 或代理资料。Cloud SHALL 从鉴权令牌确定客户并严格拒绝多余字段、非法模板或缺失 Facebook 发言语言的模板。

#### Scenario: 正常提交所选人设
- **WHEN** 用户确认批量模板
- **THEN** Edge 只提交平台与该模板，Cloud 不接收目标列表，响应不泄漏账号明细

#### Scenario: 绕过界面提交选择器或自动策略
- **WHEN** 请求携带 `accountIds`、`envKeys`、`userId`、`strategy`、独立 `writingLanguage` 或其他未允许字段
- **THEN** Cloud 拒绝请求且不创建运行、不写人设

### Requirement: Cloud 只筛选缺失账号并原样写入同一人设

Cloud SHALL 快照当前客户权威归属的 Facebook 环境，并在处理时复核当前客户归属、真实环境→账号绑定、Facebook 平台、账号存在和跨客户争用。已有有效 `persona_config` 的账号 SHALL 跳过；缺失账号 SHALL 通过原子 create-if-missing 写入运行中已确认的同一份 `soulYaml`。Cloud MUST NOT 在该路径调用模型、改变模板、按账号选择方向或覆盖已有设置。

#### Scenario: 多个缺失账号
- **WHEN** 同一运行解析到多个当前客户的缺失 Facebook 账号
- **THEN** 每个成功目标的 `persona_config.persona` 与用户确认的模板逐字相同

#### Scenario: 已有人设或并发人工设置
- **WHEN** 账号在运行前已有人设，或在批量写入前被人工设置
- **THEN** Cloud 保留既有人设并记录跳过，批量模板不得覆盖

#### Scenario: 尚未绑定的快照环境
- **WHEN** 运行快照包含尚无真实账号绑定的 Facebook 环境
- **THEN** 目标等待绑定；后续握手只对解析出的缺失账号原样写入当次已确认模板，不纳入点击后新增环境

### Requirement: 历史自动生成运行停止模型行为

Cloud SHALL 不再创建 `facebook_auto_v1` 运行。恢复到没有已确认 `soulYaml` 的历史运行时 SHALL fail-closed，把待处理目标终结为具名失败，MUST NOT 继续调用 PersonaGenerator 或回落默认模板。

#### Scenario: 部署后恢复历史运行
- **WHEN** Cloud 恢复一个旧版自动生成运行且没有已确认模板
- **THEN** 该运行不产生任何模型请求或人设写入，并以 `selected_persona_required` 等具名原因失败收敛

### Requirement: 所选人设运行持久、幂等且结果诚实

Cloud SHALL 持久化已确认模板、运行及每个环境目标，并按客户和 Idempotency-Key 去重；重复请求 MUST 返回同一运行且不重复写入。Cloud 重启后 SHALL 继续未终结的所选模板运行。API 受理只表示已安排，客户端 MUST NOT 表述为所有账号均已设置，也不得显示未经 Cloud 确认的完成数量。

#### Scenario: 网络重试重复提交
- **WHEN** Edge 以相同客户和 Idempotency-Key 重试同一模板
- **THEN** Cloud 返回同一运行，不建立第二组目标

#### Scenario: Cloud 在运行中重启
- **WHEN** Cloud 在目标等待绑定或写入过程中重启
- **THEN** 启动恢复继续使用持久化的同一模板；已成功或已跳过目标不重复写入

