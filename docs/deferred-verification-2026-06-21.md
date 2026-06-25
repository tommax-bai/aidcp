# Deferred verification — archived 2026-06-21 (verification owed)

四个 openspec change 于 **2026-06-21 在验证未完成的情况下被显式归档**（用户决定：先归档、验证后补）。
归档不代表已验证；以下验证债务**仍然成立**，归档目录见 `openspec/changes/archive/2026-06-21-*`。
补验完成后请在本文件勾掉对应项；全部清掉后可删本文件。

> ⚠️ 其中 `comment-interaction` 的安全红线（`AC-PUB-*` / `AC-RISK-*` / `AC-PROTO-*`）**尚未跑过**——
> 发评论链路在未跑通「未授权/超时不发评论」「被拒诚实跳过、终态单写」「两份 protocol.ts 不漂移」前，
> 视为**未经安全验证**，上真机/扩量前务必补齐。

## comment-interaction（发评论 + 审批）—— 整块验证未跑
- [ ] 6.1 cloud 单测：四角色脱 LLM / 脱风控可单测；评论支线终结都汇到"是否进主页评估"且只一次；失败/超时/拒绝不死锁
- [ ] 6.2 协议红线：`AC-PROTO-*`（计数 55、两份 protocol.ts 不漂移）、`AC-PUB-*`（未授权/超时不发评论）、`AC-RISK-*`（被拒诚实跳过、计数挂真回执、终态单写）
- [ ] 6.3 边缘：`executeComment` 后置校验如实回报（jsdom 桩 + 真机 smoke）；绝不静默假成功
- [ ] 6.4 已关注作者验收：主页被 `skip-profile-visit-if-followed` 跳过时评论仍正常、仍走"是否进主页评估"出口
- [ ] 6.5 `npm run test:acceptance` → `npm test` → `npm run typecheck`（edge + cloud 各自）

## interaction-appraiser-like-rebalance（点赞再平衡）
- [ ] 3.2 上线后用 `decide()` 日志对比改动前后 like/collect 比例，确认 D1/D2 实际生效（部署前基线：collect 22 / like 10 / pass 8 / both 0）

## captcha-restrict-and-interaction-gating（验证码限制门）
- [ ] 6.4 真机验证：人为触发一次验证码 → 云端置 `restricted` + 停下发 + 飞书卡（账号/机器/地址）+ DOM 清除后恢复。前置：edge 带 `AIDCP_ACCOUNT_ID`/`AIDCP_MACHINE_LABEL`/`AIDCP_REMOTE_ADDR` 启动

## follow-already-followed-truthful-report（已关注真实回报）
- [ ] 3.5（验证部分）真机观察一次 `already_followed` 如实上报 + 配额不扣

## notification-contact-registry（通知联系人名册）—— 已部署 ECS（06-25），真机校准/E2E 未补
代码级全绿（cloud 679/679+26/26、edge 326/326+11/11、console build；对抗评审 wiring+red-lines PASS）且**已部署上线**
（cloud 5118a0b/edge 521dff0/console 00bd821，迁移 0016 + 页面在 8088，healthcheck 全绿）。归档（2026-06-25）≠真机已验。
评论/@ 抽取沿用已校准选择器、上线即生效；点赞/关注两栏抽取为 best-effort、**未真机校准**。
- [ ] 8.3 真机校准：「赞和收藏」「新增关注」两栏真实行 DOM dump → 收口 `buildNotificationCategoryItemsJs` 选择器 + 主页ID 解析；验「同人同篇两评论 = 两行事件」（前置：本地 edge 跑新码 + 真实账号）
- [ ] 8.4 真机 E2E：绑定账号触发真实 评论/点赞/关注 → 联系人页对应账号出现该人、原因/昵称/时间正确、加标签不改互动次数
