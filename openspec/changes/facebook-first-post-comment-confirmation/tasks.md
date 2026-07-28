# Tasks

## 1. aidcp-cloud — 自动路径不再跳过评论确认

- [x] 1.1 去掉 `src/server.ts` 规则模式 `triggerFacebookRuleJoinContact` 里写死的 `fastReturnToFeed: true`，使自动加群+联系评论走完整就地确认生命周期。 <!-- aidcp-cloud 5b61f81 -->
- [x] 1.2 补回归断言 `test/acceptance/facebook-automatic-comment-verifies.test.ts`（AC-FB-FASTRETURN）：自动触发闭包不含 `fastReturnToFeed: true`，手动路径仍透传。 <!-- aidcp-cloud 5b61f81 -->
- [x] 1.3 `npm run test:acceptance`（156 绿）→ `npm test`（3753 绿 / 0 失败）→ `npm run typecheck` 全过。 <!-- aidcp-cloud 5b61f81 -->

## 2. aidcp-edge — 评论确认按 provenance 判定

- [x] 2.1 `facebook-router/50-comment.js` 服务器 id 判据改为「非空、非客户端占位」，兼容 base64 与纯数字两种真机形态（helper `isServerCommentId` / `hasServerCommentId` 落在 `00-shared.js`）。 <!-- aidcp-edge 3207561 -->
- [x] 2.2 `facebook-router/90-dispatch.js` 就地校验判据改用同一 helper，两处口径逐字一致。 <!-- aidcp-edge 3207561 -->
- [x] 2.3 `src/facebook/comment-executor.ts` 的 `FB_SERVER_COMMENT_ID_RE` / `isServerFacebookCommentId` / 注入页内的 `serverId()` 同步（含裸 UUID 拒绝）。 <!-- aidcp-edge 3207561 -->
- [x] 2.4 补真机形态回归：纯数字 id 判确认、`client:<uuid>` 与裸 UUID 不确认、待审徽章仍否决。 <!-- aidcp-edge 3207561 -->
- [x] 2.5 `npm run test:acceptance`（30 绿）→ `npm test`（2515 / 2514 绿 0 失败）→ `npm run typecheck` 全过。 <!-- aidcp-edge 3207561 -->
- [x] 2.6 **超出原计划的两条同源修复**（真机取证顺带炸出，见 design.md §3）：
      ① 本人身份判据补 `/groups/<gid>/user/<uid>/` 链接形态——群 feed 里作者就是这种链接，
      不补则「这条是不是我发的」恒判否，后面的 id / 控件判据根本没机会跑（遗留 TS 路径本来就认，native 移植时丢了）；
      ② 新增「在飞否决」：行上出现「发布中 / đang đăng / posting」时不确认，抵消放宽 id 判据带来的 over-confirm 面。 <!-- aidcp-edge 3207561 -->
- [x] 2.7 **滚动位移/到底判据改读真正在滚的元素**（`20-feed.js feedProbe`）：群页水合期文档不可滚
      （`scrollHeight === innerHeight`、`scrollY === 0`），真滚动条在 feed 祖先 div 上；照读窗口坐标
      ⇒ `moved` 恒 false、`near_bottom` 恒 true，引擎从第一次探测就以为 feed 已到底。窗口正常滚动时行为不变。 <!-- aidcp-edge 3207561 -->

## 3. 部署与生效

- [x] 3.1 cloud 部署 dev：备份 `cloud.bak.20260728-1522.tar.gz` + `.env.bak` → rsync `src/` → restart →
      healthcheck 全过（active / 8787 + 8090 监听 / 飞书长连接已建立 / PG 锚点缓存与风控注册表就绪）；
      ECS 标志物 `fastReturnToFeed: true`=0、新注释=1。 <!-- 2026-07-28 deployed -->
- [ ] 3.2 edge 改动**须重新打包桌面客户端**才在运营机生效（当前运营机跑的是 0.3.25，构建于 2026-07-28 02:50）。
      按 CLAUDE.md §6 打包属用户显式触发动作，本 change 不含出包。

## 4. 验收（待真机）

- [ ] 4.1 出包并让运营机升级后，规则模式自动加群+首帖评论一次，`facebook_comment_audit` 出现非
      `verification_ambiguous` 的确认态；对照 FB 活动日志核对确实上墙。
- [ ] 4.2 复核确认时延：真机实测服务器 id 在 Enter 后约 4.3s 出现，现行 9s 确认窗口足够。
- [ ] 4.3 复核水合期不再误判「feed 已到底」（对照 `facebook_group_join_audit` / 首帖 `no_candidates` 频次）。

## 5. 后续（本 change 不做，见 design.md §5）

- [ ] 5.1 评论模板"每行一条 vs 整段广告"语义需产品决策（整段自带电话，会撞联系方式校验）。
- [ ] 5.2 首帖绑定证据漂移（实测 Enter 后 5.774s 即变）。
- [ ] 5.3 同群多个加群按钮应按群 id 归一后再判唯一。
- [ ] 5.4 可信点击前先把目标滚进视口再取坐标（实测编辑器 y≈1731 而视口高 803）。
- [ ] 5.5 拆分 `verification_ambiguous`：「没看」与「看了没看见」应是两个 reason。
- [ ] 5.6 被租约丢弃的命令应有回执或可观测计数（现为静默丢弃、云端空等）。
