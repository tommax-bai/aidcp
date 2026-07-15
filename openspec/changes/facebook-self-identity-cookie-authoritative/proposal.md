# facebook-self-identity-cookie-authoritative — c_user cookie 为权威自我 id，feed 上他人链接不再误判冲突

## Why

`facebook-nickname-capture-timing` 把 FB 昵称采集时机对齐到「首批 feed 卡片」后，真机 CDP 取证（account `61591803599213`「Nancy Terry」，中文界面）暴露第二个更深的失败：**在真实 feed 上就地读身份直接 `ok:false` 报「候选冲突」**——3 次采样稳定复现：

- `c_user` cookie = `61591803599213`（登录态**权威**自我 id）、本人主页锚点在场（aria `Nancy Terry的时间线`）；
- 但 feed 上还有帖子作者/评论者的 `profile.php?id=` 链接（`100079765790323` / `100059775181406` / `100044193681253`）；
- `deriveFacebookIdentity` 把**所有** `profile.php?id=` 链接都当自我 id 候选，`unique.length > 1` → 判「candidates conflict」→ 整个读身份失败 → 昵称采集为空。

根因：**把「页面上出现的他人 profile 链接」误当成「自我 id 候选」**。旧的握手期读之所以常能成功，是因为它在贴页**瞬间**（feed 未渲染帖子）读，那时页面往往只有自我链接；新时机在 feed 已填充后读，他人链接必然在场 → 冲突高发。这是时机迁移暴露出来的既有脆弱点。

`c_user` 是登录态给出的**权威数字自我 id**（`readFacebookCookieUserId` 已保证唯一）。它在场时，自我 id 毫无歧义；页面上其他用户的链接与「自我 id 确立」无关，MUST NOT 触发冲突失败。

## What Changes

`deriveFacebookIdentity`（edge `src/facebook/identity.ts`）在**非本人主页页**（feed/home/群/详情等，`location` 无自我 profile id）分支改为：

- **c_user cookie 在场且合规 → 以其为权威自我 id**：`accountId = cookieUserId`，昵称按 **id 锚定**取（`avatarNameForId(anchors, cookieUserId)` + 就地头像/时间线后缀），页面上**其他用户的 profile 链接一律忽略、不再计入自我 id 候选、不再触发 conflict**。
- **仅在无 cookie 时**，才用 profile 链接确立 id——此时多候选才是真歧义、保留 `candidates conflict → 诚实失败`。
- 移除「cookie 与单个 profile 链接不一致即 mismatch 失败」——cookie 权威，昵称由 id 锚定保护（读到别人链接也绝不会把别人名字当自己）；最坏是昵称留空、id 仍取 cookie（正确）。

数字 id 仍来自 `c_user`（既有 `source: 'cookie'/'cookie+profile-link'` 语义不变）；本人主页页（`locationId` 在场）分支不变；就地、不导航、清洗、诚实留空全部不变。

## Impact

- Spec：`account-identity-resolution` — MODIFIED「Facebook identity reader returns stable platform id or fails honestly」：明确 c_user 权威 id 语义 + 「候选冲突」仅指自我 id 信号真歧义（有权威 cookie 时他人链接不算冲突）。
- Code：edge `src/facebook/identity.ts`（`deriveFacebookIdentity` 非本人主页分支）。
- edge-only；与 `facebook-nickname-aria-timeline-suffix`（时间线后缀）**共同**使真实 feed 上「Nancy Terry」这类中文号昵称就地可读。
- 真机验收并入 backlog 簇 42。
