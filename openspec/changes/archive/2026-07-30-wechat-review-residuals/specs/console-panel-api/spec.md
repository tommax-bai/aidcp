# console-panel-api（delta）

## ADDED Requirements

### Requirement: 管理后台按线上枚举值取中文文案时未知值必须优雅回落

管理后台按云端下发的线上枚举值渲染中文文案时，MUST NOT 直接裸取手工镜像的文案映射。任何未被镜像收录的线上值 SHALL 回落为**可见的中性标签**（至少呈现该值本身），MUST NOT 渲染为空白、`undefined`，MUST NOT 抛错致整页 white-screen。

此约束覆盖两类映射，二者的失败形态不同、但都必须回落：

1. **对象值徽标映射**（值形如 `{text,color}`）：裸取后读属性会抛错、整页崩。
2. **标量文案映射**（值为字符串，直接作为可见文案渲染）：裸取不抛错，但会静默渲染为空白——运营看到一行没有名字的记录，既不知道它是什么，也不知道界面出了问题。**静默空白是更难发现的失败，MUST 同样禁止。**

用于排序 / 分组的辅助映射对未知值 SHALL 回落为确定性取值（如末位序号），MUST NOT 产生 `NaN` 参与比较——那会让整表顺序不稳定。

回落 MUST NOT 被用作免除镜像同步的借口：它是崩溃与静默空白的防线，探测漂移仍由 `/api/version` live 对拍哨兵负责，两者互补。仓内 MUST 有一道自动守卫（本仓无 ESLint，测试即闸）扫描源码、禁止上述两类映射按线上值裸取，命中即失败并指向唯一的容错取值入口。

#### Scenario: 镜像未收录的动作值渲染为可见原值而非空白

- **WHEN** 云端下发的某条限额记录携带一个后台镜像尚未收录的风控动作值
- **THEN** 该行的动作列渲染出该值本身（中性标签），MUST NOT 为空白或 `undefined`
- **AND** 该页其余行照常渲染，整页 MUST NOT 崩溃

#### Scenario: 未知值不破坏排序

- **WHEN** 列表中同时存在已收录与未收录的枚举值
- **THEN** 未收录值按确定性末位序号参与排序，整表顺序稳定且可重现

#### Scenario: 守卫测试拦截裸取

- **WHEN** 有人新增一处按线上值裸取文案映射并直接渲染的代码
- **THEN** 仓内守卫测试失败，并指出该位置与应改走的容错取值入口

## MODIFIED Requirements

### Requirement: enum 漂移哨兵——`/api/version` 暴露 live 枚举值

`GET /api/version` SHALL 返回面板 API 契约版本**与** live 枚举值及关键 DTO 字段集合的结构指纹，作为前端 `aidcp-console` 的漂移哨兵。这些枚举值 MUST 与云端实现同一套 live 真值。

指纹暴露的枚举集合 SHALL 至少包含两类：

1. **风控 / 告警类**：风控状态 / 配额档位 / 告警分级 / **风控动作全集** / 图片厂商。
2. **面板角色 / 模型配置类**：模型类型 `llmKind`（含 `vision` 视觉角色）/ 生效模型来源 `effectiveSource` / 人设来源 `personaSource` / 思考模式 `thinkingMode`。此类枚举被 console 直接用作 `{text,color}` 徽标映射的键，其漂移会令未同步的 console 出现「键缺失」——故 MUST 纳入哨兵。

**风控动作全集 SHALL 包含云端已实装的全部动作，含入站私信回复动作 `dm_reply`。** console 侧的动作镜像 SHALL 与之逐值一致，且**动作集、中文文案映射键集、徽标色映射键集三者 MUST 双向相等**（漏配或遗留死键均判失败）。console 内若另有手写的动作联合类型副本（如配额行的 wire 类型），它 SHALL 与该镜像逐值一致——**MUST NOT 出现「镜像补齐了、wire 类型仍停在旧集合」的半同步态**。理由：私信回复配额缺省为 0，放开它的唯一运营入口就是安全限额页；镜像漏收该动作会使那几行的动作列空白、编辑弹窗标题显示 `undefined`，运营无法判断该调哪几行。

云端侧这些枚举 MUST 有一份权威 runtime 全集（`as const` 数组）并以 type-level 断言强制其与对应类型全集严格一致（漏 / 多成员均编译失败，对齐 `PANEL_ACCOUNT_FIELDS` / protocol.ts 穷举范式），`/api/version` 从该权威全集导出、而非硬编码副本。

console 端的漂移哨兵测试 MUST 对 `/api/version` 暴露的 live 真值断言，MUST NOT 以「写死的本地副本对副本」方式恒绿——后者无法检出漂移（甚至会在有人修正镜像时反而失败）。会扩张的枚举（风控动作全集、图片厂商、模型 `llmKind` / `effectiveSource` 等）漂移 MUST 由该哨兵检出。修正镜像时 MUST 同批更新真值快照断言，MUST NOT 只改期望值而不改镜像本体。

> 注：哨兵是**探测**手段（能连 live 云端时检出漂移），非崩溃防线。console 渲染侧对未知枚举值 MUST 独立容错回落（不 throw、不整页 white-screen、不静默空白），使离线 / 云端领先场景下未知值降级为可见的中性标签——两者互补。

#### Scenario: 版本接口回传 live 枚举与结构指纹

- **WHEN** 前端请求 `GET /api/version`
- **THEN** 响应含面板契约版本、live 的风控状态 / 档位 / 告警分级 / 风控动作全集 / 图片厂商枚举值，以及面板角色 / 模型配置枚举（`llmKind` / `effectiveSource` / `personaSource` / `thinkingMode`）与关键 DTO 字段集合指纹，供 console 端断言其镜像副本

#### Scenario: 风控动作全集含私信回复动作

- **WHEN** 云端已实装入站私信回复动作
- **THEN** `/api/version` 暴露的风控动作全集含 `dm_reply`
- **AND** console 镜像的动作集、中文文案映射键集、徽标色映射键集三者均含 `dm_reply` 且互相相等
- **AND** console 内手写的配额动作 wire 类型副本亦含 `dm_reply`

#### Scenario: 哨兵对 live 真值断言、检出动作集漂移

- **WHEN** 云端新增一个风控动作而 console 镜像未同步
- **THEN** console 的漂移哨兵测试在对 live `/api/version` 断言时失败，指出缺失的动作值
