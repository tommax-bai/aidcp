# Tasks

> 本 change **仅动 aidcp-edge**：只改 `src/facebook/identity.ts`（+ 对应单测）。不改协议、不改云端、不改数据库。昵称一旦就地读到即经既有 hello 通道 + 云端"仅库内为空时落库"落地。
> 热点提醒：本 change 不碰两份 `protocol.ts` / `command-bridge` / 角色注册 / 风控状态机；与并发 FB 相关 change（`facebook-scheduled-comment` 等）文件不重叠。

## 1. aidcp-edge — 就地扫描增采头像标签

- [x] 1.1 `FACEBOOK_IDENTITY_SCAN_JS`：在既有 profile 锚点收集处，额外为每个锚点采 `aria-label`（结构 `profileAnchors: [{href, ariaLabel}]`），并纳入 `/me` 自链锚点；**不改** `profileHrefs` 的选择器/上限与数字 id 派生输入（零改 id 逻辑）<!-- aidcp-edge ae86cc9 profileHrefs 仍只收 profile.php?id=/people、/me 只进 profileAnchors -->
- [x] 1.2 `FacebookIdentitySignals` 增可选字段 `profileAnchors?: Array<{href; ariaLabel}>`；`normalizeFacebookIdentitySignals` 透传（防脏输入）<!-- aidcp-edge ae86cc9 -->

## 2. aidcp-edge — 昵称派生改就地 id 锚定

- [x] 2.1 新增纯函数 `extractNameFromAvatarAria(aria)`：仅当含已知头像后缀（`的头像`/`的大头像`/`的大頭貼`/`'s profile picture|avatar|photo`）时剥离后缀取名，否则返回 null；结果过 `cleanFacebookDisplayName`<!-- aidcp-edge ae86cc9 -->
- [x] 2.2 新增纯函数 `avatarNameForId(profileAnchors, accountId)`：取 `href` 数字 id === accountId 或 `href` 为 `/me` 的锚点，返回首个非空 `extractNameFromAvatarAria`<!-- aidcp-edge ae86cc9 isSelfProfileHref: id 匹配 or /me -->
- [x] 2.3 `deriveFacebookIdentity` 按上下文选名：本人主页页（locationId 分支）候选 `[avatarName, h1, ogTitle, title, menuDisplayName]`；**非本人主页**（cookie / profile-link 分支）候选仅 `[avatarName, menuDisplayName]`——MUST NOT 用 title/og/h1；数字 id 派生与 mismatch/conflict 分支逐字不变<!-- aidcp-edge ae86cc9 nameForId(accountId,onOwnProfile) -->
- [x] 2.4 `cleanFacebookDisplayName` 收紧：先剥前导 `(N) ` 未读数前缀再判；通用词集合补 `你的个人主页 / your profile / 账户控制选项和设置 / account controls and settings`<!-- aidcp-edge ae86cc9 -->

## 3. aidcp-edge — 删 /me 跳转、改就地有界重试

- [x] 3.1 `readFacebookIdentity` 删除整段 `/me` `Page.navigate` 兜底（含 allowNavigate/navigateTimeoutMs 取名分支）；改为**按次数上界**就地轮询（读 cookie 一次 → 循环 scan+derive）：derive.ok 且有昵称即返回；ok 无昵称记为 best、继续等昵称；始终不导航<!-- aidcp-edge ae86cc9 -->
- [x] 3.2 循环用**迭代次数**限界（`ceil(hydrateTimeoutMs/interval)+1`，不用 `now()` 递减，防注入恒定时钟死循环）；耗尽后有 best 即返回（id + 空昵称），否则返回最后失败原因<!-- aidcp-edge ae86cc9 -->
- [x] 3.3 日志：昵称就地留空时打诚实说明（不再跳 /me）；绝不打 cookie 值<!-- aidcp-edge ae86cc9 -->

## 4. aidcp-edge — 测试

- [x] 4.1 `deriveFacebookIdentity`：新增①id 锚定头像标签读出昵称、②非本人主页页 `title=(4) Facebook`/群名 → 昵称留空、③本人主页页 title 仍可作昵称（保留既有断言）<!-- aidcp-edge ae86cc9 -->
- [x] 4.2 `cleanFacebookDisplayName`：新增 `(4) Facebook`→null、`你的个人主页`→null；保留既有断言<!-- aidcp-edge ae86cc9 -->
- [x] 4.3 `extractNameFromAvatarAria` / `avatarNameForId`：后缀剥离、无后缀返回 null、id 不匹配返回 null、`/me` 自链命中<!-- aidcp-edge ae86cc9 -->
- [x] 4.4 **改写** 原 `/me` 探针相关两测为新就地行为：断言**无** `Page.navigate` 调用；有 id 无昵称时留空且 ok；就地读到头像标签昵称即返回<!-- aidcp-edge ae86cc9 -->
- [x] 4.5 全绿：`npm run typecheck` + `npm test`（931 pass）+ `npm run test:acceptance`（16 pass，安全红线不回归）<!-- aidcp-edge ae86cc9 -->

## 5. 集成 / 部署 / 收尾

- [x] 5.1 `scripts/land-change aidcp-edge facebook-nickname-inplace-read`（rebase 最新 master、跑 typecheck+acceptance 再 ff）<!-- aidcp-edge f59f650..ae86cc9 pushed origin/master + 主checkout ff -->
- [x] 5.2 dev 生效路径：edge-only、无云端产物；云端"握手 hello 昵称仅库内为空时落库"已在 dev live。主 checkout 已 ff 到 ae86cc9；**运营机需重建/重跑 edge（当前跑打包版 /Applications/AIDCP.app）才生效**<!-- aidcp-edge ae86cc9；打包版需 rebuild 或从源跑更新后 edge -->
- [ ] 5.3 真机复验：现有 FB 测试号启动后昵称就地读到并经 hello 落库（dev `accounts.nickname` 非空）、无 `(N) Facebook` 垃圾 — 见 docs/real-machine-acceptance-backlog.md（需运营机重建 edge 后核）
- [x] 5.4 `openspec validate facebook-nickname-inplace-read --strict`（valid）→ archive<!-- 归档见 openspec/changes/archive/ -->
