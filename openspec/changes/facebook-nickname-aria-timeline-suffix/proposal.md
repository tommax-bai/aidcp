# facebook-nickname-aria-timeline-suffix — FB 本人锚点 aria 后缀扩到「时间线」

## Why

`facebook-nickname-capture-timing`（2026-07-15 归档）把 FB 昵称采集时机对齐小红书后，真机实测一个中文界面 FB 号（`61591803599213`「Nancy Terry」）仍读空。CDP 就地取证根因（debug port 直连 live page 扫描）：

- 本人 profile 锚点确实存在、`href=profile.php?id=61591803599213`（id 与账号匹配）、`aria-label="Nancy Terry的时间线"`；
- 但取名规则 `extractNameFromAvatarAria` 只认**头像**后缀（`的头像` / `的大头像` / `的大頭貼` / `'s profile picture/photo/avatar`），**不认「的时间线」**（timeline）后缀 → 名字在、id 对、却被判空。

即：中文界面下**个人主页链接**的无障碍标签是「<名>的时间线」而非「<名>的头像」，落在识别集之外。这是**读法覆盖面**缺口（登记于 backlog 簇 42「换语言/变体号读法短板」），非时机问题——时机修复已验证正常触发（云端日志 `profile_open direct` 每次启动都发）。

## What Changes

把本人锚点 aria 的可识别**自链后缀集**从「仅头像」扩到「头像 + 时间线」：

- `AVATAR_ARIA_SUFFIX_RE` 增补 `的时间线`（zh-CN）、`的時間線`（zh-TW）、`'s timeline`（en）三个后缀。
- id 锚定不变（只认 href 数字 id === 本账号 id 的锚点），故绝不误采他人；就地、不导航、清洗拒垃圾、读不到诚实留空——全部不变。
- 仅 edge `src/facebook/identity.ts` 一处正则；纯读法健壮性，不动数字 id 派生、不动时机、不动协议。

## Impact

- Spec：`facebook-identity` — MODIFIED「Facebook 昵称就地读取」要求：可识别后缀从「头像」扩到「头像 / 时间线」自链后缀。
- Code：edge `src/facebook/identity.ts`（`AVATAR_ARIA_SUFFIX_RE` + 注释/函数名口径）。
- edge-only（无 ECS 部署）；运营机重建 edge 后对中文界面 FB 号即时生效。
- 真机验收并入 backlog 簇 42（已 flagged 的读法短板本项落地）。
