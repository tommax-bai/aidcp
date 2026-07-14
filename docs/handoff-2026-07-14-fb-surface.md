# Handoff 2026-07-14 — FB feed-inline「开关打开」+ C3 + C4

> 面向下一个 session。读完就能接着干，不用回溯本次对话。技术细节在 memory `fb-feed-inline-multiplatform-surface.md`；完整设计在 `~/.claude/plans/fb-fb-xhs-fb-xhs-fb-robust-narwhal.md`。

## TL;DR（30 秒）

- 本 session 落了三件事，**全部 LANDED cloud master + DEPLOYED dev + 健康检查全绿 + 各自多路对抗评审全 SAFE**：
  1. **开关打开**（C2 的云端接线 + 翻转）= `cloud 22dede9`（接线，休眠）+ `c04051e`（翻转）
  2. **C4** capability gates = `cloud 19b2e13`
  3. **C3 core** 词汇 + 门槛 = `cloud 695d5f3`
- **cloud master tip = `695d5f3`**（含以上全部）。ECS dev 跑的就是这个（FB `read_content='feed'`、C4 四能力词、C3 门槛均已在 ECS 核实）。
- canonical 四仓都在默认分支（aidcp=main，edge/cloud/console=master），**无孤儿 worktree**，工作区干净。
- **没有半截的编码任务**。下一步是**灰度真机验收** + **C3 残留（都 DEFERRED、已登记）** + **攒批归档**。

## 已完成（不要重做）

| change | sha (cloud master) | 一句话 | 部署 |
|---|---|---|---|
| 开关打开（C2 云端） | `22dede9` + `c04051e` | 补 C1b 漏接的命令侧（云端从不发 surface、dispatcher 不读 inline_targeting）→ `effectiveReadSurface()` 版本偏斜闸 + 翻 FB registry read/like=feed | dev ✅ |
| C4 | `19b2e13` | 4 能力词 + 角色注册闸（修了「AuthorEvaluator 是评论后返回 feed 的桥、不能砍」的方案错误前提） | dev ✅ |
| C3 core | `695d5f3` | 6 prompt 去「小红书/笔记/收藏」读 profile + 门槛平台化（修 FB 评论恒关 bug）+ deep-read 空正文启发式 | dev ✅ |

控制仓台账已回写：`openspec/changes/facebook-feed-inline-browse/tasks.md`（§7 云端接线块）、`.../platform-orchestration-capability-gates/tasks.md`、`.../platform-vocabulary-and-thresholds/tasks.md`（含 DEFERRED 清单）。

---

## 下个 session 该做什么（按优先级）

### 1. 灰度真机验收（最高价值；需真机 + 观测窗，不是纯写代码）

云端「就地读 + 就地赞」的指令**已经在发**，但**要不要真点由边缘客户端启动 env `AIDCP_FB_BROWSE_AUTO` 决定**（off/shadow/on）。且边缘必须是含 `bae3ad4` 的构建（声明 `inline_targeting`）才会真正收到 `surface:'feed'`——canonical `aidcp-edge` master 已含，本机 `electron:dev` 重启即生效。

**推荐顺序**（对齐 plan §8 stage 4→6，硬闸就是「先影子后真开」）：
1. **dev 边缘先 `AIDCP_FB_BROWSE_AUTO=shadow` 跑一轮**（用 tom 分组测试号，见 memory `real-machine-test-accounts`）。就地读会真跑、就地赞只观察不点。
2. **收云端仲裁数据**：影子见证（独立观测的 author/正文头/reaction/articleIndex）与选中卡是否 100% 一致；`no_target(stale)` 比例是否 <10%；`expand_no_effect` 率；导航次数是否归零；顺带采 P4 已赞态串。查 journalctl（cloud dev）关键字：`observedSurface 漂移` / `feed-surface 互动 no_target` / `拒记账` / `target_mismatch`。
3. **达标才切 `AIDCP_FB_BROWSE_AUTO=on` 真点赞**（硬前置：见证 100% 一致 + no_target<10%；P4 已过）。真开前把 FB like 从 edge 的 `RETRIABLE_INTERACTION_REASONS` 移除（避免对可能已赞的两段 toggle 二次点成撤销）——见 C2 tasks 7.4。
4. 把这些结果登记进 `docs/real-machine-acceptance-backlog.md` 的**簇 66（feed 连续性）/ 67（探针）/ 68（inline 读+就地赞）/ 69（C3 词汇/门槛）**——这几个簇号方案已定，backlog 里登记项还没建，需要补。

**回滚（不需重发桌面客户端）**：把 cloud `src/platform/registry.ts` FB `noteSurfaces.read_content`（和 `like`）改回 `'detail'` 重部署 dev；或边缘启动器 `AIDCP_FB_BROWSE_AUTO≠on`。

### 2. C3 残留（都 DEFERRED，C3 change 仍 ACTIVE）

按价值排序，都是独立小块：
- **1.3 heat-velocity 平台时间解析**：`src/hot-lead/heat-velocity.ts` 的 `parsePublishedHoursAgo` 现在全是小红书时间词（刚刚/分钟前/小时前/昨天/前天/天前）。FB 时间文案（"2h"/"Yesterday at…"/"3d"）会落 null 被当非 lead。要改签名加 platform 参 + 加 FB 词元 + 更新调用点。
- **2.1 / 2.2 comments[] 入撰写 + FB 撰写器合并**：`event-bus/types.ts` 的 `NoteDetailData` 加 `comments` 字段；浏览闭环撰写器（`comment-composer.ts`，现在给 `onPageComments` 传空 `[]`）消费；合并它与 `server.ts` 的 `facebookCompose`（后者已用 comments）为共享 helper。FB 图片帖常无正文，评论是撰写主要依据——这块能提升 FB 评论质量，但改动较重。
- **3.1 裸平台分支收口**：实测云端只 **3 处** `accountPlatform==='facebook'`（`role-dispatcher.ts:1611/1900/1921`，非提案说的 6——另 3 处已走 helper）；edge 2 处（`main.ts:1239/1247`）。纯 cleanliness。
- **4.1 门槛 spec MODIFIED delta**：**代码已落**（`695d5f3`），但 spec delta **必须等 `humanize-interaction-prompts` 归档后**对着 post-humanize 文本写（撞 `comment-interaction` 同名 header，否则归档会顶掉 humanize 的改动）。同时登记 spec↔code 门槛漂移（spec 1000/300 vs code 300/100/10000）。
- **5.1 contentTruncated**：条件性。C2 P1 实测就地读拿的是全文（textContent 捷径 / 点展开），暂无显式截断标志需求。灰度观测到截断再落。
- **follow-agent 的「获赞与收藏」措辞**：未做（FB 经 C4 `canVisitProfile` 结构不访主页 = 惰性）；接「访主页但不关注」类平台或做 profile 层词汇时再收。

### 3. 归档前置 + 攒批归档

- **归档依赖链**：`category-adaptive-images-and-judgment`(32/35) 先归 → `humanize-interaction-prompts`(22/23，只剩 9.4 archive) 才能归 → C3 的 4.1 spec delta 才能写 → C2/C3/C4 才可 archive。
- C2/C3/C4 **代码都 landed+deployed**，属「landed+deployed 攒批分诊清账」候选（见 memory `openspec-triage-and-realmachine-backlog` + `openspec-archive-batch-mechanics`）。归档前跑 `openspec validate <change> --strict`。C2 还挂着真机灰度（1 项）——真机项解耦进 backlog 后 change 本身可归。

---

## 关键坑 / 不变量（别破坏）

1. **版本偏斜闸是「就地读」安全的地基**：云端只对声明 `inline_targeting` 的边缘发 `surface:'feed'`（`effectiveReadSurface()` = registry read=feed **且** 边缘声明该能力）。老边端逐位等于今天。任何改 dispatcher 控制流（下发 surface / 循环闭合 back-vs-scroll / 评论迁移触发 / no_target 重扫 / observedSurface 审计）**必须读 `effectiveReadSurface()`，不读裸 `resolveReadSurface`**——否则「云端以为 feed、边缘却在 detail」的错乱会复现。
2. **read=feed 自动耦合评论两步迁移**：因 comment 留 detail，read≠comment ⇒ 触发已落地的 C1b 回执驱动迁移（navigate→确认 noteId 匹配→才 comment，fail-closed）。这是**正确且不可分**的（首页上没法评论，就地读就必须进详情才能评）。
3. **AuthorEvaluator / ProfileBrowser / FollowAgent 恒注册**（C4）：AuthorEvaluator 是评论后返回 feed 的桥、ProfileBrowser 在本人昵称采集路径旁、FollowAgent 的 profile.done 是主页子链返回信号。能力不支持时**抑制动作**（canVisitProfile / canFollow），**绝不砍注册**——砍了 FB 评论后 loop 会停摆到看门狗杀会话。只有 12 巡视角色 + ProfileOpener 可按能力关断。
4. **门槛「放宽收藏支 ≠ 无门槛」**：主 `likeCount>300` 恒保留。改门槛时守住这条。
5. **门槛修复放大 FB 评论**：FB 现对 300+ 赞正常热度帖评论（不再只万赞）。仍过人审（除非账号 `auto_approve`——见 memory `auto-approve-and-persona-unbind`，那是个无 kill-switch 的击穿口子）。dev only。
6. **部署纪律**：cloud 只从 canonical master 的干净 `git archive HEAD` 快照 rsync（本 session 全程如此），先 `--checksum --dry-run` 确认只自己的文件 differ（防并发部署 race 覆盖他人 hotfix）；backup→rsync（`--exclude .env/node_modules/.git`，**无 --delete**）→restart→healthcheck（active/NRestarts=0/8787/PG select 1/飞书长连接）。ECS 同机 isales 绝不碰。
7. **热点单写者**：`registry.ts` + `role-dispatcher.ts` 是 C2/C3/C4 都碰的热点——本 session 是**串行**做的（switch→C4→C3，每个 landed 才起下一个 worktree）。继续做 C3 残留时若他人并行动这两文件，串行集成 + rebase。

## 验证怎么跑

- cloud 本地：`cd ../aidcp-cloud && npm run test:acceptance && npm test && npm run typecheck`（本 session 末态：acceptance 50/50、full 2035/2035、typecheck 净）。
- dev 真机：`AIDCP_E2E=1 AIDCP_CLOUD_URL=ws://121.89.85.150:8787 npm test`（gated）。
- 部署目标探活：`scripts/deploy-target dev --check`。

## 参考

- memory：`fb-feed-inline-multiplatform-surface.md`（C0–C4 全景 + 本次三个落地 + 三个坑）、`real-machine-test-accounts`、`openspec-archive-batch-mechanics`、`auto-approve-and-persona-unbind`、`fb-feed-never-scrolls-down`。
- 设计：`~/.claude/plans/fb-fb-xhs-fb-xhs-fb-robust-narwhal.md`（+ agent 终稿同目录）。
- 探针 findings：`aidcp-edge docs/facebook-browse-and-like-loop-probe-findings.md`。
