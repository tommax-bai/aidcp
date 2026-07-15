# Tasks

## 1. Contract and state

- [x] 1.1 定义首作一次性展示、专属 20 条投影、精选命中与既有发布确认衔接的 OpenSpec 契约。
- [x] 1.2 在 Cloud 增加账号级首作状态持久化与幂等迁移，并覆盖首次建立、重复绑定、原子认领、失败释放和完成状态测试。
- [x] 1.3 同步 Edge/Cloud 协议类型与 `docs/protocol.md`：人设持久化回执和首作运行投影均为可选、向后兼容字段。

## 2. Cloud orchestration

- [x] 2.1 首次人设持久化成功时建立首作状态；更新、重复绑定或存储不可用时不宣称首次引导。
- [x] 2.2 非空源内容进入精选池后原子触发既有参照创作管线；评论不触发，重复事件不重复生成。
- [x] 2.3 管线进入待审/草稿/已发布后完成首作状态；容量拒绝、失败、跳过或超时诚实释放供后续重试。
- [x] 2.4 在 `ui.snapshot.dailyUsage` 中仅为活跃首作状态下发从开始时间累计的真实浏览数与展示目标 20。

## 3. Edge experience

- [x] 3.1 将既有人设完成成长卡落地为设计稿三步说明、预期文案和“开始找灵感” CTA，保持现有 560px 浮层与旧版庆祝吉祥物。
- [x] 3.2 弱撒花与吉祥物只播放一次缩放动效，支持 reduced motion，不摆动、不漂浮、不循环。
- [x] 3.3 CTA 关闭弹窗并复用现有启动/恢复链路；更新已有人设不展示完成引导。
- [x] 3.4 主运行价值卡仅在首作状态活跃时展示专属 `/20` 进度与“看趋势 / 找匹配 / 开始创作”，普通运行继续展示真实今日计划。

## 4. Verification and closeout

- [x] 4.1 补充 Edge `fleet-console`、`ui-logic` 和相关 DOM 测试。
- [x] 4.2 补充 Cloud 状态、协议、精选触发和参照创作接线测试。
- [x] 4.3 运行 Edge/Cloud 定向测试、相关完整测试、typecheck 与 `openspec validate persona-first-post-onboarding --strict`。
- [x] 4.4 记录各仓库提交与验证结果，提交、快进合并并推送默认分支；Cloud 从干净 master 部署 dev 并完成健康检查，Edge 不打安装包。

## Completion record

- Edge `43d1e86` 已快进合并并推送 `master`；全量 `npm test` 1347/1347、相关 Electron/运行投影测试 91/91、`npm run typecheck` 通过。按交付边界未构建或发布桌面安装包。
- Cloud `f4bfc89` 已快进合并并推送 `master`；全量 `npm test` 2104/2104、首作相关 84/84 与 `npm run typecheck` 通过。
- 2026-07-15 从 Cloud `master@f4bfc89` 的干净 `git archive` 快照部署 `dev`；备份为 `/opt/aidcp/cloud.bak.20260715-cta-first-post.tar.gz` 与 `/opt/aidcp/cloud/.env.bak.20260715-cta-first-post`。
- dev 核验：`aidcp-cloud.service` active、`NRestarts=0`，8787/8090/8088 监听，8090 与 8088 `/api/health` 均返回 `{"ok":true}`，8787 HTTP 探针为预期 426，PostgreSQL `first_post_onboarding` 表已建立，关键文件 SHA-256 与提交快照一致，飞书 `WSClient onReady`。
- 未用真实新账号消耗“一生一次”首作状态，也未执行真实对外发布；桌面肉眼与真实精选→待审稿验收登记到 `docs/real-machine-acceptance-backlog.md` 簇 84。
