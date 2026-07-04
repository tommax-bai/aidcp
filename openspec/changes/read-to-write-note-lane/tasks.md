# Tasks: 阅读后写笔记旁路

## 1. OpenSpec 与设计

- [x] 1.1 新增 `read-to-write-note-lane` spec delta，明确 Feed / 阅读 / 写笔记互斥切换、触发态语义和返回续刷约束。
- [x] 1.2 运行 `openspec validate read-to-write-note-lane --strict`。

## 2. aidcp-cloud

- [x] 2.1 在阅读完成后的决策链中增加创作机会判定；普通笔记不触发，强参照笔记才触发写笔记旁路。
- [x] 2.2 复用发布调度器的参照创作输入，将当前笔记装配为 `referenceNote`，并保留人设、非照抄和 AC-PUB 人审约束。
- [x] 2.3 发布链 busy、缺人设、缺标题/正文、依赖不可用时返回稳定拒因并继续浏览，不排队假装成功。
- [x] 2.4 触发成功后不阻塞返回 feed；生成草稿/人审/发布终态仍走既有发布链回执。
- [x] 2.5 覆盖单测与浏览闭环集成测试：触发、skip、busy、失败和返回续刷。
<!-- aidcp-cloud: commit 5cd2eda pushed to origin/master. Validation: npm run test:acceptance passed (44 passed, 1 AIDCP_E2E-gated skipped); npx tsx --test "test/**/*.test.ts" passed (1319 tests); npm run typecheck passed. -->

## 3. aidcp-console

- [x] 3.1 让精选/阅读场景里的写笔记入口从阅读详情或明确创作按钮唤起，避免 Feed、阅读、写笔记三个主场景同屏堆叠。
- [x] 3.2 成功提示只表达“已触发生成/请去人审”，拒绝提示映射稳定原因码，终态仍由发布记录/人审卡呈现。
- [x] 3.3 覆盖页面测试：列表点击进入详情、详情触发写笔记、拒绝不染绿、取消/完成后回到原场景。
<!-- aidcp-console: commit 55968e7 pushed to origin/master. Validation: npm test passed (36 passed, 1 skipped); npm run typecheck passed; npm run build passed from a clean git snapshot (Vite large chunk warning only). -->

## 4. 验证

- [x] 4.1 cloud 相关测试与 typecheck。
- [x] 4.2 console 相关测试与 build/typecheck。
- [x] 4.3 若实现过程中触及 edge 或协议，补跑对应 edge 测试、acceptance 与协议漂移验证。（未触及 edge / 协议）
<!-- deploy: ECS 121.89.85.150 at 20260704-220620. Backed up /opt/aidcp/cloud, /opt/aidcp/cloud/.env, and /opt/aidcp/console; deployed cloud 5cd2eda and console dist 55968e7 from clean git snapshots. Health: aidcp-cloud active; ports 8787, 8090, and 8088 listening; console HTTP 200; PG select 1; Feishu WSClient onReady. isales services were not touched. -->
