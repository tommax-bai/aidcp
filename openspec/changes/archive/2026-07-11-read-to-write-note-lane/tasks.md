# Tasks: 发布与评论创作状态切换

## 1. OpenSpec 与设计

- [x] 1.1 修正 `read-to-write-note-lane` spec delta：移除“阅读后强参照自动触发写笔记”语义，改为 Electron 状态投影、后台洗稿文案和列宽约束。
- [x] 1.2 运行 `openspec validate read-to-write-note-lane --strict`。
  <!-- 2026-07-05: passed locally on control repo. -->

## 2. aidcp-cloud

- [x] 2.1 删除阅读后自动写作机会角色、LLM prompt 目录项、server 注入和集成测试。
- [x] 2.2 移除 `read_reference` 来源码；后台参照创作继续使用既有 `manual_reference`。
- [x] 2.3 跑发布参照链相关测试与 typecheck。
  <!-- aidcp-cloud 3abdc66: npx tsx --test "test/**/*.test.ts" passed 1320/1320 after rebase; npm run typecheck passed. -->

## 3. aidcp-edge

- [x] 3.1 发布稿件旧整页路径与原子发布指令均向 Electron 投影 `写笔记` loop stage。
- [x] 3.2 阅读页 `interaction.comment` 与评论真实成功向 Electron 投影 `评论创作` loop stage，失败不计数。
- [x] 3.3 Electron 渲染层新增 `写笔记` / `评论创作` 状态标签，仍保持单点亮。
- [x] 3.4 跑 Electron UI event/renderer 相关测试与 typecheck。
  <!-- aidcp-edge 7328d56 (includes a0a6254): Electron/UI targeted tests passed 70/70; npm run typecheck passed; npm run electron:build:win produced AIDCP Setup 0.2.2.exe; GitHub Actions run 28723776507 built mac DMGs successfully. -->

## 4. aidcp-console

- [x] 4.1 精选内容池 `create-post` 动作按钮、确认框、成功/失败提示和测试文案改为 `洗稿`。
- [x] 4.2 `纳入原因` 与 `更新时刻` 列收窄且不折行，`操作` 列放宽避免按钮溢出。
- [x] 4.3 跑精选内容池测试、typecheck 与 build。
  <!-- aidcp-console 8947af4: npm test passed 39 + 1 skipped; npm run build passed after updating downloads.ts to 0.2.2. -->

## 5. 发布

- [x] 5.1 提交并推送 cloud / edge / console / OpenSpec 变更。
  <!-- pushed: aidcp-cloud 3abdc66 -> master; aidcp-edge a0a6254 -> master; aidcp-console 8947af4 -> master. Edge master later advanced to 7328d56 and installers were rebuilt from that current master head. OpenSpec change is committed from control repo with this task record. -->
- [x] 5.2 按默认分支干净快照部署 cloud 与 console；edge 产物按桌面发布流程处理或记录未发布原因。
  <!-- cloud deployed from origin/master 3abdc66 at 20260705-075611; backup /opt/aidcp/cloud.bak.20260705-075611.tar.gz and env backup /opt/aidcp/cloud.env.bak.20260705-075611; aidcp-cloud.service active, 8787/8090 listening, /api/health ok, PG cache and Feishu WSClient ready in journal. -->
  <!-- console deployed from dist for 8947af4 at 20260705-075646; backup /opt/aidcp/console.bak.20260705-075646.tar.gz; 8088 root and /api/health ok. -->
  <!-- edge desktop 0.2.2 installers rebuilt from aidcp-edge 7328d56 and uploaded to /opt/aidcp/downloads/: AIDCP-0.2.2-arm64.dmg (95410923), AIDCP-0.2.2.dmg (101468790), AIDCP Setup 0.2.2.exe (78498410); all returned HTTP 200 via 127.0.0.1:8088/downloads. -->
