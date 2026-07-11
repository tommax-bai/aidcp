# Tasks

## 1. aidcp（中控）— 把已上线的 FB 昵称握手持久化契约归档到 facebook-identity

- [x] 1.1 从被删 change `facebook-scheduled-comment`（task 2.9，已废弃）恢复该需求，剔除已被 `facebook-nickname-inplace-read`（簇 42）取代的 `/me` 探针描述，改写为与现网一致的「就地读取 → hello 附带 → 云端仅库内空时写、既有不覆盖」契约，作为 `## ADDED Requirements` 挂进 `facebook-identity`。<!-- 实现早已上线、本 change 无新代码：edge 6d4cdca（hello accountNickname + 传播；其 /me 探针后被 ae86cc9 就地读取取代）+ cloud 8ab3199（平台校验后仅库内空时持久化），2026-07-09 部署 dev。契约文本从 979b892^ 的被删 delta 恢复并按现网校订。 -->
- [x] 1.2 `openspec validate facebook-nickname-handshake-persist --type change --strict` 通过。
- [x] 1.3 归档：delta 并入 `openspec/specs/facebook-identity/spec.md`。<!-- 无真机项：契约描述的行为 2026-07-09 已在 dev 上线并观察到（cloud 8ab3199 部署记录）；昵称就地读取的真机核见簇 42。 -->
