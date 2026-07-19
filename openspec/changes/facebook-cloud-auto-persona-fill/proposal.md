## Why

Facebook 批量创建环境后，客户端逐账号判断人设状态再提交账号 ID，既增加交互负担，也会把状态未知或陈旧的本地投影误当成云端事实。需要把“补齐当前客户所有未设置人设的 Facebook 账号”收口为一个云端意图，由云端基于客户环境归属、已确认的环境→账号绑定和人设存储自行选择目标。

## What Changes

- Facebook 批量创建表单增加一个默认开启的简单选项：“创建后由云端自动补齐未设置人设”，并只要求为整批选择一次发言语言；不新增账号选择、统计弹窗或跳转。
- 批量创建全部完成并通过现有客户归属确认后，Edge 只向 customer-auth API 提交一次无账号 ID 的补齐意图；Facebook 凭据、cookie、2FA 和代理资料仍不上传云端。
- Cloud 为该意图快照当前客户权威归属的 Facebook 环境和本批发言语言：已有账号绑定的立即检查，尚未绑定的保留等待，待环境首次登录握手建立绑定后继续处理。
- Cloud 仅为缺失有效 `persona_config` 的账号生成并持久化人设，已有任何有效人设均跳过且绝不覆盖；跨客户绑定冲突、未知账号和非法平台均 fail-closed。
- 新增显式 `facebook_auto_v1` 自动生成策略，从受控方向池按账号稳定选取生成种子，并继续使用现有人设生成器的账号差异化、结构校验、有限重试和单写落库通道。
- 补齐任务持久化、幂等且可在 Cloud 重启后恢复；生成或落库失败保留真实失败状态，不把“已排队”表述为“已设置”。

## Capabilities

### New Capabilities

- `facebook-auto-persona-fill`: 客户范围内、无客户端账号 ID 的 Facebook 缺失人设快照、延迟绑定补齐、幂等生成与诚实结果状态。

### Modified Capabilities

- `adspower-environment-provisioning`: Facebook 批量创建可选择在创建成功后提交云端自动补齐意图，同时保持凭据本地内存边界与创建结果真实性。

## Impact

- `aidcp-edge`: Facebook 批量创建表单、渲染层 IPC 入参、Electron 主进程 customer-auth 请求和批量创建回执。
- `aidcp-cloud`: customer-auth API、客户环境归属存储、环境绑定注册钩子、人设自动补齐任务存储与编排。
- PostgreSQL 新增客户人设补齐运行/目标表；不迁移或覆盖现有 `persona_config`。
- OpenSpec 更新 `adspower-environment-provisioning`，并新增 `facebook-auto-persona-fill` 能力规格。
