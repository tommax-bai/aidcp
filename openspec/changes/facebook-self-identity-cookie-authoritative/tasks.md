# Tasks — facebook-self-identity-cookie-authoritative

## 1. aidcp-edge — c_user 权威 id、feed 他人链接不判冲突

- [x] 1.1 `src/facebook/identity.ts` `deriveFacebookIdentity`：非本人主页分支改为「c_user cookie 在场即权威自我 id、id 锚定取昵称、忽略他人 profile 链接」；`candidates conflict` 仅在无 cookie 时保留；移除 cookie/单链接 mismatch 失败。本人主页分支、id 派生、就地/不导航不变。<!-- edge 600b9de -->
- [x] 1.2 edge 测试：真机复现用例——cookie=self + feed 上多个他人 `profile.php?id=` 链接 + 本人锚点 aria「Nancy Terry的时间线」→ `ok:true, accountId=self, displayName="Nancy Terry"`（不再 conflict）；无 cookie 多候选仍 conflict；cookie 与他人单链接不一致 → 取 cookie id + 昵称 id 锚定（不误判、不写他人名）。<!-- edge 600b9de test/facebook/identity.test.ts -->
- [x] 1.3 既有 identity 测试同步（原「mismatched c_user and profile link fails honestly」按新权威语义改写）；`npm run test:acceptance` → `npm test`(1428) → `npm run typecheck` 全绿。<!-- edge 600b9de -->

## 2. aidcp（控制仓）— spec / 校验 / 归档

- [x] 2.1 spec delta：`account-identity-resolution` MODIFIED「Facebook identity reader…」——c_user 权威 + 冲突仅指自我 id 真歧义。<!-- aidcp <sha> -->
- [x] 2.2 `openspec validate facebook-self-identity-cookie-authoritative --strict` 通过。<!-- aidcp <sha> -->
- [x] 2.3 edge 重建 dist（build:dist）→ **CDP live 复核**：对运营机真机 running browser 跑新 dist 的 `readFacebookIdentity` → `ok:true accountId=61591803599213 displayName="Nancy Terry"`（真实 feed、他人链接在场也不再 conflict）。运营重启 edge 后云端首批 feed 采集即写库。<!-- 2026-07-15 rebuilt+live-verified -->
- [x] 2.4 真机验收登记 backlog 簇 42；archive。<!-- aidcp <sha> -->
