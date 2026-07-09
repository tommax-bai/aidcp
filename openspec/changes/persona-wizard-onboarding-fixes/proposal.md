## Why

建号自助人设 v1（change `edge-persona-keyword-generation`）上 dev 后，运营/客户真机反馈 5 个问题：① 已绑人设的老号在客户端仍显示「未设置」；② 垂类不能手输长尾；③ 兴趣标签与垂类无关、太笼统；④ 互动偏好选项令人迷惑；⑤「生成人设」按钮灰置无法点。

坐实根因后分三类：**1 个真 bug**（#1：云端有 `isPersonaBound` 权威判据但从不下发边缘，徽标只能停在本地默认「未设置」）、**1 个引导缺口**（#5：gate 是正确的 fail-closed——无 core=无 WS=无账号，点了也发不出去、放宽即静默假成功；但没引导用户先「启动登录」）、**3 个输入设计问题**（#2/#3/#4）。本变更做**薄快修**：修 bug + 消困惑 + 删死输入 + 让兴趣更具体，**不做**未验证的提质改动（behavior_guidelines 生成等，后置另议）。

## What Changes

- **新增 `personaBound` 下行信号**：`UiSnapshotPayload` 加可选 `personaBound?: boolean`，云端在 hello 快照（`pushHelloSnapshot`）解析 `isPersonaBound(accountId)` 顺带下发（**只在 true 时下发**，避免改动「全空不发包」语义）。协议**只加可选字段、不新增消息类型**（`MessageType` 穷举不变、AC-PROTO 计数仍 65、不碰 command-bridge / onMessage 白名单）；两份 `protocol.ts` 逐字同步 + 两份 AC-PROTO 往返镜像加断言 + `docs/protocol.md` 载荷表补字段（**计数不变**）。
- **onboarding 三态**（边缘据 `personaBound` × 连接态渲染）：已绑 → 显示「已设置」摘要、**跳过**关键词→生成→确认；未绑+未连云 → 引导「先启动、扫码登录」并**分别**提示卡在「未登录」还是「未连云」；未绑+已连云 → 启用向导。**生成 gate 判据 `auth==='logged in' && cloud==='connected'` 不变**（红线：不放宽、不绕过握手）。
- **垂类支持自定义输入**：保留 10 项枚举快捷选 + 末尾「自定义」自由文本；服务端对 `keywordSelections` 补轻量输入校验（单项长度上限 + 条数上限），当前 `handler` 原样透传进 prompt 存在弱注入面，随手输一起补（纵深防御、低严重度：accountId 取握手绑定值、影响面为用户自己的人设、产物经 `loadSoulFromValue` 结构复验）。
- **兴趣改「标签 + 自由文本混合」**：保留少量高频兴趣标签做快捷多选 + 自由文本框承接长尾。更具体的兴趣输入让生成器展开出更有领域纵深、跨账号更不雷同的 `seed_keywords`（零维护，优于「垂类→子标签联动词库」——后者只覆盖常见垂类、抛弃自定义垂类的长尾、且维护负担重）。
- **删除 4 个互动偏好开关**：v1 生成器只产 identity + interests、**不产 behavior_guidelines**，互动勾选进了 prompt 但对产物零影响——删掉这个「映射不到任何输出」的迷惑输入（不收集无法兑现的输入）。

### 明确不做（后置 / 另议，非本变更）

- `behavior_guidelines` 生成（让性格真影响点赞/收藏/评论倾向）：现有硬编码兜底是调优过的已知good，从粗糙选项派生可能更空泛 + 抬高失败率（4 子字段须全出、缺一即校验失败）；「行为全坍缩」被夸大（appraiser prompt 仍带完整差异化 identity+interests）。留待有 A/B 证据表明兜底是瓶颈、且能从完整人设派生时再建。
- 结构化多维 payload、「一句话补充」自由文本、草稿边缘编辑（console 已有全字段编辑）。

## Capabilities

### New Capabilities
<!-- 无新能力；本变更修改现有 persona-keyword-generation spec 的要求 + 新增 onboarding 状态要求。 -->

### Modified Capabilities
- `persona-keyword-generation`: ① 新增「云端下发已绑人设信号 + 边缘 onboarding 三态」要求；② 修改「关键词向导输入模型」要求（垂类枚举+自定义、兴趣标签+自由文本、移除互动偏好维度）；③ 新增「生成 gate 不放宽但引导透明」要求。

## Impact

- **aidcp-cloud**：`src/comm/protocol.ts`（`UiSnapshotPayload` 加 `personaBound?`）、`src/comm/ui-snapshot.ts`（`pushHelloSnapshot` 解析下发 + `UiSnapshotDeps` 加 `isPersonaBound`）、`src/server.ts`（把 personaStore 接进 UiSnapshotService）、`src/comm/handler.ts`（`keywordSelections` 轻量输入校验）、`test/acceptance/protocol-contract.test.ts`（往返断言）。
- **aidcp-edge**：`src/comm/protocol.ts`（与 cloud 逐字同步）、`src/electron/renderer/index.html`（垂类自定义、兴趣标签+自由文本、删互动组、onboarding 三态骨架）、`src/electron/renderer/renderer.js`（消费 `personaBound` 置徽标/切三态、gate hint 拆两前置 + CTA、垂类/兴趣采集含自由文本）、`src/electron/main.cjs` + `preload.cjs`（ui.snapshot 读 `personaBound` 转发 renderer）、`test/acceptance/protocol-contract.test.ts`（往返断言）。
- **docs**：`docs/protocol.md` §3 `ui.snapshot` 载荷补 `personaBound` 字段（**§2 计数不变**）。
- **热点单写文件（须串行、动前确认无并发协议 change）**：两份 `protocol.ts`（只加一个可选字段）。edge renderer 与活跃 change `edge-multi-environment-fleet` 可能同区，集成前 fetch 核对。
- **不涉及**：新增 MessageType、command-bridge、onMessage 白名单、风控、发布链、behavior_guidelines/生成器 prompt（后置）。
