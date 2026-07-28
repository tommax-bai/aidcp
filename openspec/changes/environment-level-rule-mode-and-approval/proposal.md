## Why

Facebook 规则模式与账号全局免审目前都以账号为持久化主键，而客户实际按环境运营：环境是稳定的产品对象，账号只是该环境当前的执行对象，换账号就换环境。账号级持久化导致换绑后配置丢失、旧账号离开环境后仍携带配置，与慢启动在 `environment-level-slow-start` 中已经解决过的问题完全同构。

更直接的阻塞是：客户在批量创建 Facebook 环境那一刻**还没有账号**，因此今天无法在创建时选择运行方式或免审策略，只能在环境跑起来、账号绑定之后再逐个补配，或者引入一套「按环境挂起意向、等绑定再应用」的额外机制。把两项配置迁到环境级即可让它们在创建当刻直接落库，不需要挂起意向机制。

## What Changes

- 规则模式配置的持久化主键从账号改为环境。运行期按当前绑定账号反查所在环境读取配置；绑定未知、绑定冲突或跨客户争用 MUST fail-closed 为「不启用规则模式」。
- 评论审批覆盖策略（`source_rules|auto_approve_all`，即全局免审）的持久化主键从账号改为环境。有效模式解析改为按当前绑定账号反查环境；解析不出唯一环境 MUST fail-closed 回落 `source_rules`。
- **规则进度、浏览去重事实与批次终态继续以账号为键，不迁移。** 配置回答「这个环境要不要跑规则」，进度回答「这个账号已经做到哪」，两者是不同事实；换账号后新账号从零开始收集并重新去重是正确语义。
- **BREAKING（授权边界）**：全局免审从「只接受受内部 JWT 守护的后台请求」放宽为「后台内部通道 + 客户对自有环境的 customer-auth 通道」两个写入口。客户通道 MUST 按 env ownership 逐请求 fail-closed，MUST NOT 接受账号选择器，并 MUST 以可区分的操作人身份留审计。
- **BREAKING（创建默认值）**：Facebook 创建不再无条件开启慢启动。创建表单提供三选一的运行方式——普通 / 冷启动 / 规则——三者互斥；选择冷启动才开启环境级慢启动，选择普通或规则则不开启。界面 MUST 明示未选冷启动时不套用 7 天额度爬坡。
- Facebook 创建表单额外提供全局免审勾选，单个与批量创建均适用，随归属完成请求一并落到环境。
- 管理后台的规则模式开关与全局免审选择从按账号配置改为按环境配置。
- 归属完成接口在既有 `slowStartEnabled` 之外接受可选的运行方式与免审字段；字段仍走严格白名单，非 Facebook 平台提交 MUST 整请求 fail-closed。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `facebook-rule-mode`: 配置权威主键由账号改为环境，并显式声明进度与去重事实继续按账号存续。
- `client-facebook-rule-mode-toggle`: 客户端环境作用域开关由「解析到账号后写账号」改为真正的环境级持久化，并支持未绑定环境预设。
- `scoped-approval-policy`: 评论审批覆盖策略改为环境级持久化，新增客户自有环境写入口，后台配置面改为按环境。
- `client-customer-auth`: 归属完成接口接受运行方式与免审意图；新增 env-scoped 免审读写路由。
- `adspower-environment-provisioning`: Facebook 单个与批量创建改为显式三选一运行方式并提供免审可选项，取代无条件默认慢启动。

## Impact

- **Control**：本变更文档与交付记录。依赖 `facebook-rule-mode-cadence` 与 `client-facebook-rule-mode-toggle` 先行归档——两者的能力规格尚未并入 `openspec/specs/`，本变更的对应 delta MUST NOT 先于它们生效。
- **Data**：`facebook_rule_mode_config` 与 `account_comment_approval_policy` 主键与外键改指环境；按现有唯一绑定把存量账号行回填到其所在环境；旧账号键列停止参与运行时读写但暂留作可回滚数据，本变更不执行破坏性删列。两表与 `client_environments` 同属 `aidcp-api` 单写域，改键不引入跨服务写入。
- **Cloud / API**：配置存储与内存副本改键；新增按账号反查环境的读路径并接入既有环境↔账号映射；customer-auth 新增免审路由并扩展归属完成契约；面板 API 写入口改按环境定位。
- **Console**：规则模式与全局免审改为环境维度的配置入口与真态展示。
- **Edge**：创建表单新增运行方式三选一与免审勾选，取代写死的慢启动意图；提交字段随归属完成请求下发。
- **Out of scope**：规则模式脱离人设入口闸不在本变更范围内，另立变更承接；本变更不改变慢启动对规则模式的绝对优先权，不改变规则定义版本，不改变风控、配额与审批安全闸。
