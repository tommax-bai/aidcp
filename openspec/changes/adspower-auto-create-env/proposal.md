## Why

运营要给每个小红书号在 AdsPower 里配一套「有区分度但真实」的指纹环境，现在全靠人手在 AdsPower UI 里逐字段点十几个旋钮——其中好几个是陷阱（`device_memory=6` 非 2 的幂即伪造信号、跨 OS 字体混装、`webgl` 模式互斥、软渲染），**运营最大的痛点就是怕自己配错**，且配错在创建时看不出来、上工后才被平台连坐。本 change 把「造指纹」从人手收走，改由客户端按验证过的规则一键创建，并诚实区分「配置层已就绪」与「运行时实测已就绪」，不把没验证的环境伪装成能投产。

本 change 是对已归档决策 `2026-07-01-adspower-desktop-env-picker` **D4「面板不做 `user/create`、创建交给 AdsPower」** 的显式反转：当时判断创建留给 AdsPower UI 更简单，但实践暴露「人手配指纹易错且错在暗处」是核心风险，故收回创建、由程序守住正确性。旧 Non-Goal 相应软化为「不自动化代理供给与登录」（见下）。

## What Changes

- **「创建环境」按钮从「拉起 AdsPower 让人手动建号」升级为「程序化一键创建一个指纹环境」**：`src/electron/main.cjs` 现有 `openAdsClient()` 外链行为改为经 AdsPower 本地 API `user/create` 建号（当前 `#ads-create` → `ads:openCreate` → 外链，`renderer.js:397`）。
- **指纹最大化委托 AdsPower 生成，aidcp 侧不逐字段手搓**：只做三件事——① 挑「这是台什么机器」（OS/整机模板，OS 为第一锁定字段）；② 一层薄静态护栏（禁 `device_memory=6`、只允 2 的幂封顶 8、`webgl` 模式不自相取消、`webrtc=proxy`、字体不跨 OS、时区/语言 based-on-IP、关闭「每次启动重随机指纹」）；③ 提交前「声明 OS == UA OS == 字体 OS == renderer 家族 OS」四者一致断言，不符**诚实拒建**。
- **创建成功即如实呈现「已创建」，不自动判就绪**：`user/create` 回 id 即如实呈现「已创建」；是否可用由运维**登录时人工确认**。**不做**自动运行时自检 / 投产硬闸 / 就绪判定（小规模手动场景 YAGNI，见 Non-Goals）。
- **唯一运营提示 = 是否配了代理**：环境列表对每个环境显示代理配置状态，`no_proxy` / 空 → 「未配置代理」**纯提醒、不拦任何操作**；代理由运维手动在 AdsPower 侧配（本按钮不下发 / 不校验 / 不去重代理，`ads-local-api.cjs:167` 已能读 `no_proxy`）。
- **写能力落点守红线**：新增 AdsPower 写客户端，用硬编码 allowlist 放行 `user/create`/`group/create`/`user/delete`，任何 `browser/start|stop|active` 路径在该客户端内直接抛错 + 回归断言（浏览器生命周期仍是核心子进程单写）；复用同一条 1req/s 节流。
- **删除环境（新增）**：环境列表每行提供删除，**点两次确认**（第一次待确认态、第二次才删）、删前警示不可恢复（若已登录账号登录态一并丢失）；删除 MUST NOT 自动 / 批量 / ledger 驱动。同时**移除**「打开 AdsPower 新建环境」手动外链（创建已程序化）。
- **账本与凭据安全**：以 AdsPower `user/list` 为账本（专用分组 + `remark`，**不建本机台账**）+ 主进程单飞互斥 + 渲染层点击即 disable；AdsPower API key / 凭据**绝不明文落盘**、只内存持有，日志层脱敏、禁 stringify 整个请求体。
- **BREAKING（对旧 spec）**：反转 `adspower-desktop-env-picker` 的 D4 Non-Goal「面板不做 `user/create`」。

## Capabilities

### New Capabilities
- `adspower-environment-provisioning`: 客户端经 AdsPower 本地 API 程序化创建一个指纹环境——委托生成 + 薄静态护栏 + OS 四者一致断言 + 硬编码 allowlist 写客户端 + 以 `user/list` 为账本 / 单飞互斥（不建本机台账）+ 凭据不落盘 + `intendedAccountLabel` 写入分身 `remark` + MUST NOT 程序化 `user/delete`；创建**只标「未验证」、由运维登录时人工确认**（不做自动自检 / 投产硬闸 / 云端映射——见 Non-Goals）。

### Modified Capabilities
- `adspower-desktop-env-picker`: 「创建环境」从外链拉起 AdsPower 改为程序化创建；反转 D4 Non-Goal；界面如实呈现「已创建」+ **唯一提示「是否配置了代理」**（`no_proxy` / 空 → 纯提醒、不拦操作）。

## Impact

- **仅 aidcp-edge**：`src/electron/` 新增写客户端（与只读 `ads-local-api.cjs` 分离）、指纹模板/护栏/断言、创建编排（以 `user/list` 为账本 + `remark`，无本机台账）、`preload.cjs`/主进程 IPC 新增创建通道、`renderer/` 按钮 UI 钩子 + 「是否配代理」提示。保持无构建链（纯 HTML/CSS/JS）。**不改 aidcp-cloud、不改协议 v2、不改风控**。
- **协作串行**：与活跃 change `edge-companion-ui`（17/22，正在「全重排」`renderer/` 三件套）碰同一批文件——本 change 的**按钮 UI 钩子标记串行、在 `edge-companion-ui` 落地后 rebase 到其新 UI 上**；非 UI 部分（写客户端 / 指纹引擎 / 创建编排）可先行（已落 aidcp-edge）。
- **明确非目标（不做）**：客户端多开/同机多任务并发（一次一个环境，单实例锁 `main.cjs:454` 不动，批量运行走 CLI 另议）；代理供给/校验/去重自动化（代理人手配，仅一个「是否配代理」提示）；**创建后自动运行时自检 + 投产硬闸**（YAGNI，是否可用由运维登录时人工确认）；**云端 profile↔machine 映射 + 登录账号比对**（后台看板/规模化才需要，另立 change）；单次创建规模上限/观测挂钩；小红书登录自动化（人手扫码是必经闸）；行为拟人 / 时序去相关（云端事）；**自动 / 批量 `user/delete`**（红线：删除仅由界面逐个二次确认触发，绝不自动 / 批量 / ledger 驱动；浏览器生命周期 `browser/*` 仍禁）。
- **下码前置（已完成）**：对真实 AdsPower 实测（`aidcp-edge/scripts/adspower-fingerprint-probe.ts`，62b4b94）——`device_memory=6`→运行时读 4（护栏「只允 2 的幂」证实必要）、`webgl='2'` 逐字 honor config / `webgl='3'` 无视 config、不 pin OS 会随机分 OS（含 iPhone）故模板必须显式 pin OS；护栏与 webgl 取舍据此定案。
