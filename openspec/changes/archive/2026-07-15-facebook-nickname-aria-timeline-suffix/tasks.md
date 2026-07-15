# Tasks — facebook-nickname-aria-timeline-suffix

## 1. aidcp-edge — 扩本人锚点 aria 后缀集

- [x] 1.1 `src/facebook/identity.ts`：`AVATAR_ARIA_SUFFIX_RE` 增补 `的时间线` / `的時間線` / `'s timeline`；`extractNameFromAvatarAria` 及注释口径由「头像后缀」放宽为「头像 / 时间线等本人自链后缀」。id 锚定与其余（就地、不导航、清洗、诚实留空）不变。<!-- edge 776c0e8 -->
- [x] 1.2 edge 测试：`extractNameFromAvatarAria`/`deriveFacebookIdentity` 增中文时间线用例（`aria="Nancy Terry的时间线"`、href id === accountId → 读出「Nancy Terry」）；覆盖 zh-TW `的時間線` + en `'s timeline`；既有头像后缀用例保持绿。<!-- edge 776c0e8 test/facebook/identity.test.ts -->
- [x] 1.3 `npm run test:acceptance` → `npm test`(1426) → `npm run typecheck` 全绿。<!-- edge 776c0e8 -->

## 2. aidcp（控制仓）— spec / 校验 / 归档

- [x] 2.1 spec delta：`facebook-identity` MODIFIED「Facebook 昵称就地读取」——后缀集扩到头像/时间线。<!-- aidcp <sha> -->
- [x] 2.2 `openspec validate facebook-nickname-aria-timeline-suffix --strict` 通过。<!-- aidcp <sha> -->
- [x] 2.3 edge 重建 dist（build:dist）→ CDP live 复核就地读出「Nancy Terry」（与 `facebook-self-identity-cookie-authoritative` 合力，真机 readFacebookIdentity ok+Nancy Terry）。<!-- 2026-07-15 rebuilt+live-verified -->
- [x] 2.4 真机验收登记 backlog 簇 42；archive。<!-- aidcp <sha> -->
