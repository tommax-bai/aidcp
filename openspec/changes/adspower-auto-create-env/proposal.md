## Why

运营要给每个小红书号在 AdsPower 里配一套「有区分度但真实」的指纹环境，现在全靠人手在 AdsPower UI 里逐字段点十几个旋钮——其中好几个是陷阱（`device_memory=6` 非 2 的幂即伪造信号、跨 OS 字体混装、`webgl` 模式互斥、软渲染），**运营最大的痛点就是怕自己配错**，且配错在创建时看不出来、上工后才被平台连坐。本 change 把「造指纹」从人手收走，改由客户端按验证过的规则一键创建，并诚实区分「配置层已就绪」与「运行时实测已就绪」，不把没验证的环境伪装成能投产。

本 change 是对已归档决策 `2026-07-01-adspower-desktop-env-picker` **D4「面板不做 `user/create`、创建交给 AdsPower」** 的显式反转：当时判断创建留给 AdsPower UI 更简单，但实践暴露「人手配指纹易错且错在暗处」是核心风险，故收回创建、由程序守住正确性。旧 Non-Goal 相应软化为「不自动化代理供给与登录」（见下）。

## What Changes

- **「创建环境」按钮从「拉起 AdsPower 让人手动建号」升级为「程序化一键创建一个指纹环境」**：`src/electron/main.cjs` 现有 `openAdsClient()` 外链行为改为经 AdsPower 本地 API `user/create` 建号（当前 `#ads-create` → `ads:openCreate` → 外链，`renderer.js:397`）。
- **指纹最大化委托 AdsPower 生成，aidcp 侧不逐字段手搓**：只做三件事——① 挑「这是台什么机器」（OS/整机模板，OS 为第一锁定字段）；② 一层薄静态护栏（禁 `device_memory=6`、只允 2 的幂封顶 8、`webgl` 模式不自相取消、`webrtc=proxy`、字体不跨 OS、时区/语言 based-on-IP、关闭「每次启动重随机指纹」）；③ 提交前「声明 OS == UA OS == 字体 OS == renderer 家族 OS」四者一致断言，不符**诚实拒建**。
- **诚实区分创建态与就绪态（不静默假成功红线）**：`user/list` 是配置层、非实测出口 IP（`ads-local-api.cjs:159`），创建只保证「配置层自洽 + 取值合法 + 有区分度 + 稳定」，状态显式命名「仅配置层 / 未验证 / 不可投产」，**绝不把 `create` 回 id 当已就绪**。
- **创建后一次性运行时自检 → 置就绪**：因已确定客户端不做多开、一次只处理一个环境，可开一次分身、经 CDP 实测（真实出口 IP、`renderer` 非软渲染 SwiftShader、WebRTC 不漏真机 IP、时区↔IP、跨分身 Canvas/WebGL/Audio 哈希与 renderer 字符串去重）后才置 `verifyState=ready`。
- **投产硬闸**：`verifyState` 是启动路径的代码级硬前置，未过**诚实拒绝启动**（复用 `pluggable-browser-provider` 已有「失败诚实停手、绝不回落 self」同款闸，`browser-provider.ts:131`），不是纯咨询字段。
- **账号↔分身绑定闭环**：台账每条预填 `intendedAccountLabel`；登录握手时边缘回写真实 accountId 并比对，不一致诚实告警、不投产；`ads_profile_id` + `machine_label` 进握手载荷落库（走 `accounts-master-data` 已有自愈 `ALTER ... ADD COLUMN IF NOT EXISTS` 惯例，`account-store.ts:44/47` 有范例），与本 change 同批交付、不推迟。
- **代理软提示、非硬闸**：没配代理时给提醒，但**照样允许创建、绝不强制**；环境列表把「无代理」状态如实显示（`ads-local-api.cjs:167` 已能读 `no_proxy`），只为不把无代理号伪装成已配好、不拦任何操作。
- **写能力落点守红线**：新增只写 `user/create`/`group/create` 的 AdsPower 写客户端，用硬编码 allowlist，任何 `browser/start|stop|active` 路径在该客户端内直接抛错 + 回归断言（浏览器生命周期仍是核心子进程单写）；复用同一条 1req/s 节流，本机核心子进程活跃时不并发跑批量写。
- **幂等与凭据安全**：write-ahead 台账（发 `create` 前写 pending、回 id 补齐、原子写）+ 显式 reconcile 对账（标 `untracked-orphan`/`stale`）+ 主进程单飞互斥 + 渲染层点击即 disable；AdsPower API key / 代理账密**绝不明文落盘**、只内存持有，日志层脱敏、禁 stringify 整个请求体。
- **规模与观测挂钩**：一次创建规模 N 的上限与「能看见号被平台盯上 + 后台逐账号可观测」能力挂钩，观测未就绪时 **N 收敛到 2–3**，不把「一键上十号」当默认。
- **BREAKING（对旧 spec）**：反转 `adspower-desktop-env-picker` 的 D4 Non-Goal「面板不做 `user/create`」。

## Capabilities

### New Capabilities
- `adspower-environment-provisioning`: 客户端经 AdsPower 本地 API 程序化创建一个指纹环境——委托生成 + 薄静态护栏 + OS 四者一致断言 + 硬编码 allowlist 写客户端 + write-ahead 台账/reconcile/单飞互斥 + 凭据不落盘 + 代理软提示 + `intendedAccountLabel` 绑定意图 + MUST NOT 程序化 `user/delete`。
- `environment-readiness-verification`: 创建后一次性运行时自检（开一次分身经 CDP 实测出口 IP / 非软渲染 / WebRTC 不漏 / 时区↔IP / 跨分身指纹去重）置 `verifyState`，并把 `verifyState` 通过做成启动路径的代码级硬前置（未过诚实拒绝投产）。

### Modified Capabilities
- `adspower-desktop-env-picker`: 「创建环境」从外链拉起 AdsPower 改为程序化创建；反转 D4 Non-Goal；界面如实呈现环境就绪态（仅配置层 / 未验证 / 已就绪）与「无代理」标注；创建时可预填 `intendedAccountLabel`。
- `accounts-master-data`: 账号主数据新增持久化 `ads_profile_id` 与激活 `machine_label`（现为死列），经握手载荷落库、走已有自愈 ALTER 惯例，建立账号↔分身↔机器可审计对应。

## Impact

- **aidcp-edge**（主体）：`src/electron/` 新增写客户端（与只读 `ads-local-api.cjs` 分离）、指纹模板/护栏/断言、台账（write-ahead + 原子写 + reconcile）、创建后自检、`preload.cjs`/主进程 IPC 新增创建与自检通道、`renderer/` 按钮 UI 钩子；边缘核心在登录握手载荷带 `ads_profile_id`/`machine_label` 并回写比对 `intendedAccountLabel`；启动路径（`pluggable-browser-provider` / `launch-multinode` 组装槽位）读 `verifyState` 硬闸。保持无构建链（纯 HTML/CSS/JS）。
- **aidcp-cloud**（轻触）：`account-store` 自愈 ALTER 加 `ads_profile_id`，激活 `machine_label`；握手落库带这两字段。不改协议 v2、不改风控状态机、不改风控终态单写。
- **协作串行**：与活跃 change `edge-companion-ui`（17/22，正在「全重排」`renderer/` 三件套）碰同一批文件——本 change 的**按钮 UI 钩子标记串行、在 `edge-companion-ui` 落地后 rebase 到其新 UI 上**；非 UI 部分（写客户端 / 模板 / 台账 / 自检 / 云端加列）可先行。
- **明确非目标（不做）**：客户端多开/同机多任务并发（一次一个环境，单实例锁 `main.cjs:454` 不动，批量运行走 CLI 另议）；代理供给自动化（代理人手配、软提示）；小红书登录自动化（人手扫码是必经闸）；行为拟人 / 时序去相关（云端事）；fleet 级可观测（放开规模的前置、另立）；程序化 `user/delete`（红线，孤儿只暴露引导人工删）。
- **下码前置（阻塞护栏细节）**：对真实 AdsPower 打一次 `user/create` 实测——`device_memory=6` 是被静默接受还是纠正、`webgl='3'` 时同传 `webgl_config` 是否被吞及随机池是否受 OS 约束——据此定护栏与 webgl 模式取舍。
