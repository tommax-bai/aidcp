# console-panel-api spec delta — console-panel-config-enum-fingerprint

## MODIFIED Requirements

### Requirement: enum 漂移哨兵——`/api/version` 暴露 live 枚举值

`GET /api/version` SHALL 返回面板 API 契约版本**与** live 枚举值及关键 DTO 字段集合的结构指纹，作为前端 `aidcp-console` 的漂移哨兵。这些枚举值 MUST 与云端实现同一套 live 真值。

指纹暴露的枚举集合 SHALL 至少包含两类：

1. **风控 / 告警 / 厂商类**：风控状态 / 档位 / 告警分级 / **风控动作全集** / **图片生成厂商**。
2. **面板角色 / 模型配置类**：**模型类型 `llmKind`（含 `vision` 视觉角色）/ 生效模型来源 `effectiveSource` / 人设来源 `personaSource` / 思考模式 `thinkingMode`**。此类枚举被 console 直接用作 `{text,color}` 徽标映射的键，其漂移会令未同步的 console 出现「键缺失」——故 MUST 纳入哨兵。

云端侧这些枚举 MUST 有一份权威 runtime 全集（`as const` 数组）并以 type-level 断言强制其与对应类型全集严格一致（漏 / 多成员均编译失败，对齐 `PANEL_ACCOUNT_FIELDS` / protocol.ts 穷举范式），`/api/version` 从该权威全集导出、而非硬编码副本。

console 端的漂移哨兵测试 MUST 对 `/api/version` 暴露的 live 真值断言，MUST NOT 以「写死的本地副本对副本」方式恒绿——后者无法检出漂移（甚至会在有人修正镜像时反而失败）。会扩张的枚举（风控动作全集、图片厂商、模型 `llmKind` / `effectiveSource` 等）漂移 MUST 由该哨兵检出。

> 注：哨兵是**探测**手段（能连 live 云端时检出漂移），非崩溃防线。console 渲染侧对未知枚举值 MUST 独立容错回落（不 throw、不整页 white-screen），使离线 / 云端领先场景下未知值降级为可见的中性标签而非崩溃——两者互补。

#### Scenario: 版本接口回传 live 枚举与结构指纹
- **WHEN** 请求 `GET /api/version`
- **THEN** 响应含面板契约版本、live 的风控状态 / 档位 / 告警分级 / 风控动作全集 / 图片厂商枚举值，以及面板角色 / 模型配置枚举（`llmKind` / `effectiveSource` / `personaSource` / `thinkingMode`）与关键 DTO 字段集合指纹，供 console 端断言其镜像副本

#### Scenario: 哨兵对 live 真值断言、检出动作集漂移
- **WHEN** 云端风控动作集合从 6 扩到 7（新增评论赞），而 console 镜像未同步
- **THEN** console 漂移哨兵测试对 `/api/version` live 真值比对失败（红），而非因「副本对副本」恒绿而漏检

#### Scenario: 哨兵检出模型配置枚举漂移
- **WHEN** 云端角色目录新增一个 `llmKind:'vision'` / `effectiveSource:'vision'` 的角色（配置枚举全集扩张），而 console 镜像未同步
- **THEN** `/api/version` 的 `enums.llmKind` / `enums.effectiveSource` live 全集含 `vision`，console 漂移哨兵测试比对其镜像副本失败（红），在部署前暴露漂移；即便漏检，console 渲染侧亦以中性标签容错、不整页崩溃
