# Tasks — fb-group-join-click-leg-reuse

> 纯边缘单文件行为收窄。云端零改动、协议零改动、DB 零改动。

## 1. aidcp-edge — click 腿复用已确立的目标页

- [x] 1.1 新增在位谓词 `isOnCanonicalGroupPage(currentUrl, canonicalUrl)`（`src/facebook/join-executor.ts`）：同 origin + pathname 恰为 `/groups/<id>`（容尾斜杠）；query/hash 不计；解析失败 / URL 取不到 → `false`。**MUST NOT** 用 `canonicalGroupUrl()` 归一 current URL（会把 `m.facebook.com` 与 `/about` 误判成在位——见 design.md D2）。 <!-- aidcp-edge 2f726ee isOnCanonicalGroupPage，导出供单测 -->
- [x] 1.2 `joinGroup` 开头的 `Page.navigate`（原 `:641`）从无条件改为条件：**仅当** `options.click === true` **且** 当前页在位 → 跳过 navigate + `settleMs`；其余一切情况（含 observe 腿、URL 读取失败）→ 照旧 navigate。**observe 腿 MUST 永远 navigate**（死锁论证见 design.md D1）。 <!-- aidcp-edge 2f726ee -->
- [x] 1.3 读当前 URL 用现成 `evalJson`（`src/browse/cdp-util.ts:54`）；**读失败 / 抛异常 MUST 吞掉并回落 navigate**，绝不让「优化探测」把加群整条弄失败。 <!-- aidcp-edge 2f726ee 偏离：catch 内补 rethrowIfTakeover——本文件既有铁律「接管 MUST 冒泡、绝不降级」，裸 catch 会把让位吞成一次多余整页加载 -->
- [x] 1.4 `observeUntilReady` / `preClickSettleMs` / 一切既有闸**位置与语义不变**（design.md D3/D4）。 <!-- aidcp-edge 2f726ee 未改动 -->

## 2. aidcp-edge — 测试

- [x] 2.1 谓词单测（`test/facebook/join-executor.test.ts`）：在位（裸址 / 尾斜杠 / 带 query / 带 hash）→ true；不在位（`m.facebook.com` 同群、`/about`、`/posts/…`、异群、非 FB 站、空串 / 畸形串）→ false。 <!-- aidcp-edge 2f726ee -->
- [x] 2.2 click 腿在位 → **零** `Page.navigate`、仍走就绪轮询、仍点击成功。 <!-- aidcp-edge 2f726ee -->
- [x] 2.3 **observe 腿即便在位也 MUST navigate**（防死锁的承重断言——这条一旦被"优化"掉即回归 design.md D1 的死锁）。 <!-- aidcp-edge 2f726ee 反死锁承重断言 -->
- [x] 2.4 click 腿不在位（当前页 = 首页 / 异群 / URL 读失败）→ 照旧 navigate。 <!-- aidcp-edge 2f726ee 另加：探测抛错→回落导航、探测遇接管→冒泡 -->
- [x] 2.5 回归：既有 join-executor 用例全绿（同意浮层 / 登录 / 验证码 / 问卷 / 待审 / already_member 矛盾守卫 / not_ready / no_button / 作用域）。 <!-- aidcp-edge 2f726ee join-executor 61/61（既有 55 条零回归） -->

## 3. 验证与收口

- [x] 3.1 `npm run typecheck` + `npm test`（edge） <!-- aidcp-edge 2f726ee typecheck 干净；test:acceptance 22/22；join-executor 61/61 -->
- [x] 3.2 land 回 edge `master`（rebase，非 ff 不 force） <!-- aidcp-edge 2f726ee ff 推送 origin/master，主 checkout 已同步 -->
- [x] 3.3 真机验收登记 `docs/real-machine-acceptance-backlog.md`（FB 加群共享真机环境簇）——桩测**验不了**「FB 真页 URL 在 observe 后是否被 FB 改写（如追加 `?ref=`）」，须真机确认复用真的命中而非每次回落 navigate <!-- 2026-07-16 登记为 backlog 82.12（FB 共享真机簇）；edge dist 未重建，运营机须重启客户端才验得到 -->
- [x] 3.4 `openspec validate fb-group-join-click-leg-reuse --strict` → archive

## 不做（YAGNI，见 design.md）

- 不跳过 `preClickSettleMs`（D4）
- 不跨调用缓存 DOM 句柄 / 坐标（跨导航必失效；本 change 让 click 腿不再跨导航，是 `facebook-join-actuation-decouple` 的**上游缓解**，不替代它）
- 不加 feature flag（优化的失败方向 = 今日行为，flag 纯冗余）
- 不动云端两段式 / 租约释放设计（那是对的）
