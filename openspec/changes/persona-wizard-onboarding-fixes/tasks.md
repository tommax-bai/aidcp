## 1. 协议：ui.snapshot 加 personaBound（热点单写，先做、动前确认无并发协议 change）

<!-- 全部 21 子任务实装完成：cloud 8160d0e（协议 personaBound + ui-snapshot 下发 + server 装配 + handler 输入校验；AC-PROTO-10；全量 1642 绿）/ edge b37f491（协议同步 + ui-event 行 + main.cjs 映射 + 三态 onboarding + 垂类/兴趣自由文本 + 删互动组；AC-PROTO-10；全量 756 绿）。docs/protocol.md §3 补 personaBound 字段（§2 计数不变仍 65）。 -->

- [x] 1.1 两份 `src/comm/protocol.ts`（edge + cloud）**逐字一致**给 `UiSnapshotPayload` 加可选 `personaBound?: boolean`（带注释：已绑人设信号，仅 true 时下发）；**不新增 MessageType**（穷举计数不变）
- [x] 1.2 两份 `test/acceptance/protocol-contract.test.ts` 加 ui.snapshot personaBound 往返断言（镜像一致）；AC-PROTO-02 计数**仍 65**（不改）
- [x] 1.3 `docs/protocol.md` §3 `ui.snapshot` 载荷补 `personaBound?` 字段说明（**§2 计数不变、不改**）

## 2. aidcp-cloud — 下发信号 + 输入校验

- [x] 2.1 `src/comm/ui-snapshot.ts`：`UiSnapshotDeps` 加 `isPersonaBound(accountId): boolean`；`pushHelloSnapshot` 解析后**仅在 true 时**把 `personaBound` 并入 payload（守「全空不发包」——为 true 时正常发）
- [x] 2.2 `src/server.ts`：把 personaStore（`isPersonaBound`/`getForAccount`）接进 UiSnapshotService deps
- [x] 2.3 `src/comm/handler.ts`：`onPersonaGenerate` 对 `keywordSelections` 补轻量输入校验（单项长度上限 + 条数上限），超限诚实回 `persona_invalid`/`input_too_large`，绝不原样喂 prompt
- [x] 2.4 cloud 回归：ui.snapshot 带 personaBound（已绑）/ 不带（未绑）、输入超限被拒；`npm run test:acceptance` + `npm test` + `npm run typecheck`

## 3. aidcp-edge — 三态渲染 + 输入模型 + gate 引导

- [x] 3.1 `src/comm/protocol.ts` 与 cloud 同步（属任务 1）
- [x] 3.2 `main.cjs` + `preload.cjs`：ui.snapshot 消费处读 `personaBound`，转发给 renderer（随现有 ui.snapshot→status/activity 通道，或新增一个字段）
- [x] 3.3 `renderer.js`：消费 `personaBound` 置徽标 + 切 onboarding 三态（已绑→「已设置」摘要跳过向导 / 未绑+未连云→引导先启动登录 / 未绑+已连云→启用）；徽标不再永远停「未设置」
- [x] 3.4 `renderer.js` `updatePersonaGate`：gate 判据**不变**，hint 拆两前置（`auth!=='logged in'`→提示扫码登录 / `cloud!=='connected'`→提示等待连云）+ 指向「启动」CTA
- [x] 3.5 `index.html` + `renderer.js`：垂类加「自定义」自由文本项；兴趣改「少量高频标签多选 + 自由文本框」；**删除 4 个互动偏好开关**；`collectPersonaKeywords` 把自由文本并入 `keywordSelections`
- [x] 3.6 edge 回归：三态切换正确、已绑账号显示已设置、自定义垂类/自由兴趣进 keywordSelections、删互动组后无残留引用；`npm test` + `npm run typecheck` + `node --check` renderer/main.cjs/preload

## 4. 集成与真机 backlog

- [x] 4.1 两仓 AC-PROTO 往返断言过；两仓全量 + typecheck 过
- [x] 4.2 `docs/real-machine-acceptance-backlog.md` 登记真机项：已绑老号显示已设置跳过向导、未登录/未连云分态引导、自定义垂类+自由兴趣产更具体 seed_keywords、删互动组后生成正常
