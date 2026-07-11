# Handoff — Facebook 浏览 + 点赞（Change B）续做入口（2026-07-11）

> 面向接手的新 session。语言：正文中文，代码 / 命令 / 标识符英文（CLAUDE.md §6）。
> **这是「代码已全部落地、只剩真机 shadow 标定」的续做交接。读完即可续做。**
> 深背景（探针发现 / 设计原委 / 测试 harness 搭建过程）见姊妹文档 `docs/handoff-facebook-browse-like-2026-07-10.md`（本文档不重复）。

## 0. 一句话现状

**Change B（FB 浏览 + 点赞闭环）代码已 100% 实装 + 全绿 + `openspec validate --strict` 过 + 三仓 land + cloud 已部署 ol。默认关。** 唯一没做完的是 **task 8.2 真机 shadow**——被本机 AdsPower 起不了 CDP 浏览器挡住（基础设施问题，非代码），连带 **task 8.3 放真点赞** 与「已赞态确切标识标定」待做。

## 1. 落地台账（隔离分支 `feature/fb-full-integration`，三仓已 push origin）

| 仓 | worktree | tip commit | 状态 |
| --- | --- | --- | --- |
| 控制 aidcp | `../aidcp.wt/fb-full-integration` | `56dabe9` | tasks.md / handoff / backlog / probe-findings 齐 |
| edge | `../aidcp-edge.wt/fb-full-integration` | `4c9ce61` | `src/facebook/` 全新增，913 单测 + 16 acceptance + typecheck 干净 |
| cloud | `../aidcp-cloud.wt/fb-full-integration` | `b302251` | registry FB 加 browse/interact/join，1770 单测 + 47 acceptance + typecheck 干净；**已部署 ol** |

- 三仓均在 `feature/fb-full-integration`、与 `origin` 同步（无 ahead/behind）。
- **零改 `protocol.ts`**（复用既有平台中立消息，避让 `feed.refresh`）；`AC-PROTO-*` 仍绿。

## 2. 代码做了什么（edge `src/facebook/` 新增 + cloud registry 一处放行）

- `feed-reader.ts`：`role=feed` > `role=article` 扫卡 → 结构化 `page.cards`；跳虚拟化空壳（无 `h2/h3/h4 a` 作者链即未 hydrate）；`collect` 对 FB 恒 0（无收藏，诚实缺省，绝不伪造）。
- `post-reader.ts`：permalink → `role=dialog` 深读正文 + 顶评 + 反应 / 评论计数。
- `like-executor.ts`：帖级 `留下心情` toggle，**in-page `element.click()`**（坐标 `dispatchClick` 对 FB React div[role=button] 失效）；后置校验按钮真翻转才回 `ok`，否则诚实 `no_target`/`state_unchanged`，**绝不 `count||1`/假成功**；`ok:true` 才走云端 `RiskController.record`（PG），无边缘并行计数器；支持 shadow（记日志不执行）。
- `cta-labels.ts`：多语言反应词匹配 + **数字守卫**（见 §4 critical 坑）。
- `consent.ts`：从 master `d8a83ca` forward-port 的「允许 Cookie」同意浮层自动接受。
- `facebook-session.ts`：`FacebookBrowseSession` **独占单槽 browseHandler**（内含评论 / 加群 / note.open-by-url 委托，避免与旧 comment/join 抢槽）；三态 `AIDCP_FB_BROWSE_AUTO`（off/shadow/on）；每命令**恰一诚实回执**；有界超时放行链（hung CDP 不阻塞串行命令）。
- driver 声明 `browse`/`interact`（与 BrowseSession **原子同落**，`usesFacebookBrowseSession` 分支挂载，装配闸绝不把 xhs BrowseSession 误挂 FB）。
- cloud `platform/registry.ts`：FB 能力 `['comment']` → `['browse','comment','interact','join']`，一处放行 `canStartSession` 平台闸（数据驱动，非分支）。
- FB 验证码 / 软限流经 overlay-report-gate + WatcherSupervisor 上报云端（对抗性评审补的 major，否则 Change A 的 FB 限流退避 + 远程验证码协助失效）。

## 3. ol 部署已完成（2026-07-10，用户授权）

- 按 CLAUDE.md §5 安全序列：target 检查 → ECS 备份 `cloud.bak.20260710-235249.tar.gz`（19M）+ `.env.bak.20260710-235249` → git-archive 快照 rsync（exclude `.env`/`node_modules`/`.git`，无 `--delete`，registry-only 无新依赖）→ `systemctl restart aidcp-cloud.service`。
- **健康检查全过**：FB 能力已生效（registry `['browse','comment','interact','join']`）、服务 active、8787 在听、飞书长连接已建、panel API `127.0.0.1:8090` up、主库正常。
- **绝不碰同机 isales**（本次也没碰）。
- 已知无关旧问题：`llm_token_usage` retention 命中 `ECONNREFUSED 127.0.0.1:5432`（本地 token-usage PG 未起，与本 change 无关）。
- edge 是 edge-only（跑在运营机上的 FB 分支，无 ECS 部署）；**运营机需 pull FB 分支 + 重建才生效**。

## 4. Critical 坑（对抗性评审揪出，务必记住别回退）

FB 帖子动作栏有两个易混按钮：**反应计数汇总按钮**（`aria-label=赞` + 数字文案如「3,829」）与真正的**点赞 toggle**（`留下心情`，空文案）。初版 `reactState` 把计数按钮误判成「已赞」→ 凡有反应的帖子点赞全变 no-op + 假 `already_liked`（且 VERIFY 假 ok 是红线）。

**修法 = 数字守卫**（`/\d/` 排除有数字文案的计数按钮，同 feed-reader 的守卫）+ `fbText` 回落 `textContent`。已加 jsdom 回归：对真实动作栏（计数按钮在 toggle 之前）跑 in-page IIFE，证明选中 + 点击 + 校验的是 toggle 而非计数按钮。改 `like-executor.ts`/`cta-labels.ts` 时**别把这守卫改没了**。

## 5. 续做清单（按序，全部记在 tasks.md 8.2/8.3 + backlog 簇 44）

### 5.1 【卡点】跑通真机 shadow（task 8.2）
- **前置障碍**：2026-07-10 尝试时 AdsPower `browser/start` 返回**空 `debug_port`**（status Inactive，chrome_102 SunBrowser 内核不起 CDP 浏览器）→ edge 诚实失败于浏览器启动、无自愈回落（正确行为）。**这是本机 AdsPower 问题（需重启 AdsPower 桌面 app / 更新内核），不是代码缺陷**——之前探针能跑通说明 AdsPower app 卡了。
- **解锁后重试命令**：
  ```
  cd ../aidcp-edge.wt/fb-full-integration && \
  AIDCP_PLATFORM=facebook AIDCP_ADS_USER_ID=k1ehveal \
  AIDCP_CLOUD_URL=ws://123.56.253.183:8787 \
  AIDCP_FB_BROWSE_AUTO=shadow npm run start
  ```
- **观察目标**：`page.cards`（feed 结构化上报）/ `note.detail`（深读结构）是否正确；点赞在 shadow 下只记日志不执行、回执诚实。

### 5.2 标定「已赞」态确切 aria-label（唯一待确认）
- 在一个可弃的帖子上真点一次赞，抓**点赞前 / 后**的按钮 `aria-label` + 文案，钉死「已赞」toggle 的真值字符串（当前 VERIFY 接受「正向已赞信号」——`取消赞`/`Remove Like` 或 空文案→反应词——不确定时诚实 `state_unchanged`，绝不假成功）。
- 标定后收紧 `like-executor.ts` 的 VERIFY，把真值串写进 `cta-labels.ts` 的 `UNREACT_RE`/`REACTED_WORD_RE`。

### 5.3 放真点赞（task 8.3）
- shadow 观察通过后，`AIDCP_FB_BROWSE_AUTO=on`；配额靠 account-nurture 脊柱保守压制（Change A 已实装）。

### 5.4 【另案，deferred】FB IdentityWatcher
- 长跑 FB 会话中途登出目前无自愈（feed/post reader 每命令诚实回 `login_required`，靠云端看门狗 + 运营人工重启恢复）。这是 FB 侧既有缺口（评论 only 路径也没有），非红线（回执诚实、无假成功），且本闭环默认关 + shadow 先行 + 隔离期运营监督。
- 正解需 **FB-aware 身份自愈**（FB 登录墙确认，不是 xhs 的 `CdpLoginModalWatcher`），且有误报砸会话风险（见 memory `identity-watcher-false-positive-brick`）——**必须设计、不能赶**。留 backlog 簇 44。

## 6. 测试 harness（可复用，详见 memory `fb-integration-test-flow`）

- **测试账号**：`61591458584142`（Michelle Garcia），platform=facebook。**AdsPower 环境**：`k1ehveal`（group aidcp-创建，no_proxy，已注入 FB cookie 免登录，桌面 UA 已修）。
- **ol harness**：cloud 跑 `npx tsx src/server.ts`，`ws://123.56.253.183:8787`，`AIDCP_COLDSTART_RAMP=false`（测试账号回落 normal 档，comment/publish 不被 Day-1 压 0）；共用 dev 库，按 account_id 隔离；同机无 isales。
- **CDP 探针纪律**：真机导航要**拉开间隔**，连续 resize+navigate 会触发软阻断 / hydrate 失败假象。

## 7. 红线（改这块代码前必守）

- **PC UA + 强制宽窗**（用户定案，绝不用移动版 UA / 布局；FB 移动布局无 `role=feed`/`role=article`）。
- browse 能力翻转**必须与 BrowseSession 原子同落**。
- **零改 `protocol.ts`**。
- **后置校验防假成功**（点赞按钮真翻转才 `ok`，找不到即 `no_target`，绝不 `count||1`）。
- **点赞计数只经云端 `RiskController.record`（PG），无边缘计数器**；`collect` 对 FB 恒 0 缺省。
- 宽窄兼容 DOM-first（窄版兜底）；默认关 kill switch + shadow 先行。
- **热点单写者**：两份 `protocol.ts`、`command-bridge.ts` 动作映射、平台 registry、能力词表——并行时绝不同时碰。
- **FB 账号密码 / 2FA / cookie 属敏感值，绝不写仓库 / 文档 / 记忆 / commit**，只临时经 API/env 用。

## 8. 相关 change / 文档 / memory

- change：`facebook-browse-and-like-loop`（B，本文档）；tasks.md 见 `openspec/changes/facebook-browse-and-like-loop/tasks.md`；探针发现见同目录 `*-probe-findings.md`。
- 姊妹交接（深背景）：`docs/handoff-facebook-browse-like-2026-07-10.md`（探针发现 / 设计原委 / harness 搭建）。
- memory：`fb-browse-like-loop-landed`（本 change 落地档）、`fb-integration-test-flow`（ol 测试配方 + 账号）、`fb-test-env-desktop-ua-fix`（桌面 UA 前提）、`fb-full-integration-design`（三 change 隔离分支总纲）、`identity-watcher-false-positive-brick`（5.4 deferred 的风险背景）、`captcha-assist-enhancement-trio`（overlay 上报云端复用）。
