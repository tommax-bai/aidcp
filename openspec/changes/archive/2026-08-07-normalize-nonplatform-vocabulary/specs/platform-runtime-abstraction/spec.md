## MODIFIED Requirements

### Requirement: 协议语义保持平台无关

平台抽象 SHALL 优先复用具有相同业务含义和页面副作用的命令语义合同。浏览词汇的消息名携带平台段（如 `{platform}.note.open`），同构名按平台分别登记、语义合同一致；新增平台 MUST NOT 借平台段让同构命令偏离该共享语义合同；当同一业务意图在不同平台需要不同可观察副作用时，系统 SHALL 定义不同的固定副作用命令并由 Cloud 平台策略显式选择，MUST NOT 让同一命令或可选 mode/direct 字段按平台改变导航行为。

新增真实通用语义时，系统 MAY 增加平台无关消息类型，但 MUST 同步 Cloud/Edge `protocol.ts`、Cloud command mapping、Edge active-command routing、`docs/protocol.md`、能力协商与协议验收。浏览 surface 与 open purpose、以及派生 `noteId` 与独立 `observation` 见证包 SHALL 继续作为既有消息上的平台无关 optional 字段承载。

#### Scenario: 相同副作用复用平台无关命令
- **WHEN** 多个平台都能以相同前置条件、页面副作用与结果合同执行一个动作
- **THEN** 它们复用同一份命令语义合同并由各平台 adapter 实现（平台无关命令共用同一个名字；带平台段的浏览命令按平台登记同构名、合同一致）

#### Scenario: 不同副作用拆成不同命令
- **WHEN** 本人身份采集在 Facebook 必须留在当前页、在 Xiaohongshu 必须进入本人主页
- **THEN** Cloud 分别选择 `identity.read_current_page` 与 `identity.read_self_profile`
- **AND** MUST NOT 通过同一个 `xiaohongshu.profile.open` 的平台分支或 `direct` 字段表达差异

#### Scenario: 新真实语义跨协议同步
- **WHEN** 新增 `identity.read_current_page`、`identity.read_self_profile` 与 `identity.observed`
- **THEN** 两端协议枚举、命令映射、主动路由、协议文档、能力协商与验收测试同步更新

#### Scenario: surface 与 purpose 是平台无关字段扩展
- **WHEN** 为 `{platform}.note.open` 增加 `surface`/`purpose`、为 `action.completed` 增加派生 `noteId`/`observation`
- **THEN** 这些字段的语义不以任何平台名命名、缺省时逐位等于既有行为
