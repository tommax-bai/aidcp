## Why

Facebook 环境需要一个人工可控的批量人设入口，但“导入后自动生成”和环境栏“一键补齐”都跳过了用户对人设内容的确认，还让 Cloud 为不同账号自行生成内容。正确边界应是：用户在客户端只选择并确认一份人设，Cloud 只从当前客户的权威 Facebook 环境/账号绑定中筛出尚无人设的账号，把这份完全相同的人设原子写入，绝不替用户选方向或调用模型生成。

## What Changes

- 删除 Facebook 批量创建表单中的“创建后自动补齐”开关、批次语言选择、创建后请求和相关回执；创建环境与设置人设重新解耦。
- 环境栏筛选为 Facebook 时只显示“批量设置人设”入口，不显示独立语言选择。点击后打开现有账号人设选择浮层的批量模式，语言作为完整人设的一部分在浮层内人工选择。
- 批量模式根据用户选择的语气、点赞倾向、内容偏好和语言在客户端确定性生成一份可预览 `soulYaml`；不调用 Cloud 人设生成器。用户确认后才提交该完整人设。
- Edge 只提交 `platform=facebook` 与用户已确认的 `soulYaml`，不提交账号 ID、环境 ID、客户端人设状态、凭据或代理资料。
- Cloud 校验所选人设，快照当前客户权威归属的 Facebook 环境，现读真实环境→账号绑定与 `persona_config`，仅对缺失人设的账号执行原子 create-if-missing；所有目标使用同一份 `soulYaml`，已有设置绝不覆盖。
- Cloud 补齐服务移除 `facebook_auto_v1` 方向池和逐账号 PersonaGenerator 调用。历史自动生成运行若缺少已确认模板将 fail-closed，不再恢复模型生成。
- 运行仍持久、幂等并支持等待当前快照内尚未绑定的环境；受理只表示已安排，不冒充所有账号已设置。

## Capabilities

### New Capabilities

- `facebook-auto-persona-fill`: 客户端人工确认一份人设后，由 Cloud 无账号 ID 地筛选当前客户缺失人设的 Facebook 账号并原样补齐。

### Modified Capabilities

- `adspower-environment-provisioning`: Facebook 单个/批量创建只负责环境创建与客户归属，不再展示或触发任何人设补齐能力。

## Impact

- `aidcp-edge`: 删除批量创建自动补齐控件/请求/回执；环境栏入口改为打开人设浮层批量模式；新增客户端确定性模板构建和所选人设提交 IPC。
- `aidcp-cloud`: customer-auth 请求契约改为接收已确认 `soulYaml`；运行存储新增模板列；补齐编排从逐账号生成改为同模板 create-if-missing。
- PostgreSQL 对既有补齐运行表做非破坏性扩展；`persona_config` 不迁移且已有行不覆盖。
- Cloud 运行时变更部署到 dev；不构建 Edge 安装器。
