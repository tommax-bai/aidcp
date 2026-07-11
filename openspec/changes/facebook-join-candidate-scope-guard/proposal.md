## Why

Facebook 加群的**观测腿**（`GROUP_JOIN_OBSERVE_JS`）与**点击腿**（`GROUP_JOIN_CLICK_JS`，`join-executor.ts`）**页面级**采集加入候选：只按标准区域角色排除顶栏/导航/侧栏（`closest('[role="banner"],[role="navigation"],[role="complementary"]')`），**不排除「发现更多小组」推荐栏**。真机取证（2026-07-11，Tianxing Bai 真号 env k1ei3dbi，pending 群 `groups/311384382278852`）坐实：推荐栏里**别的群**的加入按钮与目标群自身加入按钮**字面逐字相同**（`div[role=button]`「加入小组」，因界面语言随账号、非随群），且这些推荐栏候选**通过了现有区域排除**（推荐栏不带 banner/navigation/complementary 角色）。

点击腿取「文档序第一个 `join` 类节点」（`join-executor.ts:409-412`）。当目标群自身控件**不是** `join` 类时——例如账号已 pending（本群按钮「取消请求」，且「取消请求」当前不在 pending 词表，见 sibling change `facebook-join-pending-label-audit`）、已是成员、或群头 Join 钮晚渲染（真机实测约 7s，见 `fb-group-join-wait-render`）——文档序第一个 `join` 就落到**推荐栏里某个无关群**的加入按钮上，于是**加入一个云端从未裁定的群**（红线：冒进错目标 wrong-target）。后置校验随后在目标群上报失败、调度器重试，每次重试可能再多加一个推荐群——附带加群还不进成员账本。

这不是思辨风险：**现网今天就会发生**（不依赖任何未落地的 change）。根因是「候选采集/点击缺群自身作用域」，与语言无关。本 change（分层方案 P0，从记忆总览 `fb-cross-language-recognition-plan` 的「真正的 edge 侧活 = 候选区域 scoping」结论提级为规范）把候选**限定在目标群自身的 header/动作区**，把推荐栏与任何指向异群的候选排除在外，先灭红线。它同时是 L2（`facebook-join-actuation-decouple`）clickTarget 重定位所必需的**作用域前置**——L2 的字面相等匹配必须在本作用域内进行，否则同字面异群按钮照样被匹配。

## What Changes

- **点击腿作用域 = 目标群自身头部/动作区正向包含（承重、fail-closed；2026-07-12 评审订正）**：`GROUP_JOIN_CLICK_JS` 选取 `join` 节点时 MUST **只在目标群自身「头部/动作区」块内**取——该块 = 含群名主标题（`<h1>`/`[role="heading"][aria-level="1"]`）的头部/hero 容器（承载群名 + 群主 CTA）。候选默认**出域**，只有落在该块内才在域内（fail-closed）。**订正原因**：原设计用「排除指向异群的候选」这条**黑名单**，但真机 dump 证实推荐位「加入小组」钮是群名链接的**兄弟裸 `div`**、不带异群 `href` → 黑名单漏排 → 目标群 pending 时误点推荐群（红线仍在）。正向包含的失败态是安全侧（块取窄 → 漏认 → 诚实不点 + 重试），黑名单的失败态是红线侧（漏排 → 误点异群）。
- **corroborating 排除再收窄（非承重）**：在正向包含之上再叠两条排除——E1 候选被 `a[href]` 祖先（或自身 href）解析到 `/groups/<异于当前页 id>` 则排除；E2 落在「发现更多小组 / 查看推荐小组」推荐轮播容器内则排除。二者只会让作用域更窄、绝不放宽。
- **fail-closed 不回落页面级点击**：无法从 URL 解析目标群 id、或目标群头部块解析不出、或作用域内无 `join` 候选时，点击腿 MUST 诚实 `scope_unresolved` / `no_target_in_scope` / `clicked:false`，**绝不**回落到「页面级文档序第一个 join」（那正是误点推荐群的路径）。
- **观测腿标注作用域 + 成员信号收窄（不阻断上报）**：`GROUP_JOIN_OBSERVE_JS` 对每个候选附 `inTargetScope`（是否属目标群头部/动作区，同承重 + 排除判据），据此挑选 `mainCta`/`joinButton`——推荐栏候选不冒充群主 CTA；**`membershipSignals` 亦只在目标群头部块内读取**（现状 `signals.slice(0,8)` 是页面级，推荐位「已加入」会污染、致点后对错群假成功——红线1 尾巴，同根因）。观测腿仍如实上报全部候选（含推荐栏）供云端判断，不静默丢弃（守 L4 不 fail-closed 丢原文）。
- **自身区控件不可分类时诚实**：作用域内存在控件但既非 join 也非 member/pending 分类时，MUST 诚实回报（`unclassified` / `no_target`），**绝不**越出作用域另找 join 冒充成功。
- **不做（YAGNI）**：不建 N 语按钮字典；不给按钮上视觉；不改 pending/member 词表（那是 sibling change B）；不触协议、不动云端、不动 L3 后置校验结构。

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `facebook-group-join-resilience`: 新增「候选区域 scoping」要求——加入候选采集、点击与成员信号读取 MUST **正向包含**在目标群自身 header/动作区块内（含群名主标题的头部/hero 容器），候选默认出域、fail-closed；在此之上再叠 corroborating 排除（异群 `/groups/<异 id>` 链接、「发现更多小组」推荐轮播容器）；点击腿在无法定位目标群 id、头部块解析不出、或作用域内无 join 候选时 fail-closed 诚实回报、绝不回落页面级文档序首个 join；观测腿标注 `inTargetScope` 并据此挑选群主 CTA、收窄成员信号，仍如实全量上报候选。

## Impact

- 代码（**edge-only，无协议、无云端**）：
  - edge `src/facebook/join-executor.ts`：`GROUP_JOIN_OBSERVE_JS`（候选采集加 `inTargetScope`、群主 CTA 挑选 + 成员信号读取按作用域收窄）、`GROUP_JOIN_CLICK_JS`（`join` 选取改**正向包含目标群头部块** + fail-closed 不回落页面级）；作用域判据（目标群 id 从 `location.pathname` 解析、群名主标题祖先块正向包含承重、异群 `a[href]` 群 id 比对 + 「发现更多小组」轮播容器结构排除作 corroborating）。
  - 测试：edge 单测——推荐栏异群 join 不被点（红线，含**兄弟裸 `div` 无异群链接**的推荐位 join）、目标 pending/member 时作用域内无 join → 诚实不点、目标可加入群正常点、目标群 id/头部块解析失败 → fail-closed、群主 CTA/成员信号不取推荐栏候选。
- 部署：edge master land（edge-only，无 ECS/cloud 部署；本地 `typecheck` + `test` + `test:acceptance`）。
- 真机验收（落 backlog，不阻塞码级）：**实装前先做一次确认探针（硬前置）**——真机捕获目标群头部块结构（群名 `<h1>` 祖先链、目标自身 Join 与推荐位 join 相对该块的位置），坐实「正向包含」框住目标自身 Join 且推荐位 join 落块外；再捕获推荐栏 join `href`/祖先群链接为 E1/E2 定档；核 pending/member/晚渲染三态下作用域内不误点、可加入群正常。头部块祖先判据 + E2 容器选择器**校准后方 land**（fail-closed 判据不可凭猜）。归入 FB 加群真机簇。
- 依赖：无新增。与 sibling `facebook-join-pending-label-audit`（B）互补但独立——A 单独即让 pending 场景 fail-safe（推荐位 join 不在目标群头部块内 → 作用域内无 join → 不点）；B 修正状态上报准确性。与 L2（`facebook-join-actuation-decouple`）是**前置**：L2 clickTarget 匹配须在本作用域内进行。
