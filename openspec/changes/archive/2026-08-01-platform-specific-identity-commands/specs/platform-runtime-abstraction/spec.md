## MODIFIED Requirements

### Requirement: 协议语义保持平台无关

平台抽象 SHALL 优先复用具有相同业务含义和页面副作用的平台无关命令。新增平台 MUST NOT 引入以平台名命名的协议消息类型来表达相同固定语义；当同一业务意图在不同平台需要不同可观察副作用时，系统 SHALL 定义不同的固定副作用命令并由 Cloud 平台策略显式选择，MUST NOT 让同一命令或可选 mode/direct 字段按平台改变导航行为。

新增真实通用语义时，系统 MAY 增加平台无关消息类型，但 MUST 同步 Cloud/Edge `protocol.ts`、Cloud command mapping、Edge active-command routing、`docs/protocol.md`、能力协商与协议验收。浏览 surface 与 open purpose、以及派生 `noteId` 与独立 `observation` 见证包 SHALL 继续作为既有消息上的平台无关 optional 字段承载。

#### Scenario: 相同副作用复用平台无关命令
- **WHEN** 多个平台都能以相同前置条件、页面副作用与结果合同执行一个动作
- **THEN** 它们复用同一个不含平台名的协议命令并由各平台 adapter 实现

#### Scenario: 不同副作用拆成不同命令
- **WHEN** 本人身份采集在 Facebook 必须留在当前页、在 Xiaohongshu 必须进入本人主页
- **THEN** Cloud 分别选择 `identity.read_current` 与 `identity.read_self_profile`
- **AND** MUST NOT 通过同一个 `profile.open` 的平台分支或 `direct` 字段表达差异

#### Scenario: 新真实语义跨协议同步
- **WHEN** 新增 `identity.read_current`、`identity.read_self_profile` 与 `identity.observed`
- **THEN** 两端协议枚举、命令映射、主动路由、协议文档、能力协商与验收测试同步更新

#### Scenario: surface 与 purpose 是平台无关字段扩展
- **WHEN** 为 `note.open` 增加 `surface`/`purpose`、为 `action.completed` 增加派生 `noteId`/`observation`
- **THEN** 这些字段的语义不以任何平台名命名、缺省时逐位等于既有行为

## ADDED Requirements

### Requirement: 平台 driver 与 Native adapter 声明准确命令集

每个浏览器平台 driver SHALL 声明可路由的版本化语义页面命令；每个 Native adapter manifest SHALL 声明实际实现的准确命令集。Edge 对 Cloud 的命令能力声明 MUST 取两者交集。声明漂移、缺少命令或版本不匹配时，该命令能力 MUST 不可用，MUST NOT 仅凭 broad `browse`、`identity`、`profile_visit` 或 adapter version 推断支持。

#### Scenario: broad capability 不能替代准确命令
- **WHEN** Facebook driver 声明 `browse` 和 `identity`，但 Native adapter 未声明 `identity_read_current`
- **THEN** Edge 不向 Cloud 声明运行期当前页身份读取能力

#### Scenario: Native 拒绝平台外命令
- **WHEN** 一个语义命令不在当前 Native session 平台的准确命令集中
- **THEN** Native 在 CDP 派发前返回 `unsupported_command`
- **AND** MUST NOT 路由到其他平台 adapter 或 JavaScript fallback

