# Tasks

## 1. aidcp-cloud — 提交前失败分档

- [x] 1.1 `src/publish-agent/command-sequencer.ts`：终局值由五档增至**六档**，逐档注释与实际接住的情形对齐。
  <!-- aidcp-cloud 84d7276 六档而非提案设想的「拆成两个」——原因见 1.2 -->
- [x] 1.2 末位无条件 `return 'failed_before_submit'` 改为两级分流。
  <!-- aidcp-cloud 84d7276 **提案前提被实装推翻**：提案称走到该档时提交点「确定」未跨过。不成立——
       `submitted` 只在拿到 ok:true 时置真，故「提交指令已推送、随后回执超时/边缘断连」这一格两个判据
       都为假却**未证明那一下没按下去**。照提案做即一条双发路径。改为第一级判据＝提交指令是否已推出
       （`submitPushed`，置于推送前一格、复用既有不可逆边界标记 onFirstSideEffect），推过了走
       `failed_page_state_unknown`（处置逐字沿用旧行为）。控制仓 proposal/spec 已同步修正（96de54d5）。 -->
- [x] 1.3 结构性与可恢复两集合互斥且对提交前原因全集穷尽。
  <!-- aidcp-cloud 84d7276 断言 AC-PREDISPATCH-1 按**导出的集合引用**断言，非手抄字面量。
       结构性表的准入线写成判据而非名单：只收「单稿自身属性」，且 MUST NOT 收任何「多次尝试累计而成」的原因。 -->
- [x] 1.4 `all_images_failed` 归**可恢复**档（复核时改判）。
  <!-- aidcp-cloud 84d7276 初版按提案放进结构性表，复核推翻：它由逐张上传失败累计而来（单张超时/异常
       各自被丢弃并继续），全失败的典型成因在图源/上传通道侧（已知 OSS 匿名读 403 即此类），
       按「重来有没有可能不同」当场判——显然有。K=0 早停的直接返回同步改为可恢复档。 -->

## 2. aidcp-cloud — 下发段按分档处置

- [x] 2.1 新增可恢复档分支，对齐 `preempted` 样板（保持待审、保留授权、素材归还、事件驱动重投）。
  <!-- aidcp-cloud 84d7276 -->
- [x] 2.2 `settleFacebookMedia` 档位映射同步（参数类型改为 outcome 联合类型、逐档具名）。
  <!-- aidcp-cloud 84d7276 -->
- [x] 2.3 重投上限（默认 2，env `AIDCP_PUBLISH_DEFER_REDISPATCH_MAX`），计数与被抢占重投分开。
  <!-- aidcp-cloud 84d7276 恢复预算只由本档失败消费 -->
- [x] 2.4 熔断计数排除零副作用两档。
  <!-- aidcp-cloud 84d7276 两档豁免理由**不同**且不得混为一谈：可恢复档不烧稿；结构性档确实烧稿，
       但其成员都是单稿自身属性、停整批 drain 救不了任何一稿。spec delta 已按此重写（控制仓 96de54d5）。 -->
- [x] 2.5 三个阈值旋钮显式回落 + 告警（复核时追加）。
  <!-- aidcp-cloud 84d7276 `Math.max(1, NaN) === NaN` ⇒ env 抄错则熔断永不开火＝一道安全闸静默失效。
       按加闸准入表：概率低 × 后果不可逆且对外可见 ⇒ 该修。行为变更仅限 env 畸形这一格。 -->
- [x] 2.6 飞书通知链末尾的真兜底桶改为显式分支（顺手修的活的静默假消息）。
  <!-- aidcp-cloud 84d7276 原实现把**任何**未识别的 notice kind 渲染成「🟢 发布熔断解除」 -->

## 3. aidcp-cloud — 测试

- [x] 3.1 提交前抖动 → 保持待审 + 授权保留 + 素材归还 + 熔断不变 + 触发重投。<!-- aidcp-cloud 84d7276 -->
- [x] 3.2 重投耗尽 → `failed` 且文案为「重试 N 次未成」。<!-- aidcp-cloud 84d7276 -->
- [x] 3.3 未识别提交前原因 → 走可恢复档 + 日志带原始串。<!-- aidcp-cloud 84d7276 -->
- [x] 3.4 回归断言：`submitted_unconfirmed` / `yield_timeout` 处置逐字未变。<!-- aidcp-cloud 84d7276 -->
- [x] 3.5 三个验证命令全过。
  <!-- aidcp-cloud 84d7276 test:acceptance 193/193（AC-PUB-* 全绿）；npm test 4189 中 4178 pass /
       0 fail / 11 skipped（既有真机 gated）；typecheck exit 0。land-change 在 rebase 后复跑同样全过。 -->
- [x] 3.6 变异验证：每条变异都能定位到具体哪条用例转红。
  <!-- aidcp-cloud 84d7276 六次变异——拆掉提交推送闸→AC-PREDISPATCH-5/6；可恢复档计熔断→「连撞多次仍不熔断」；
       两个预算合并→「恢复预算只由本档消费」；结构性表漏一条→AC-PREDISPATCH-8；
       all_images_failed 挪回结构性→AC-MEDIA-DEGRADE + AC-PREDISPATCH-8；
       阈值换回 Math.max(1,…)→「熔断永不开火」那条。全部回退后复跑全绿。 -->

## 4. 登记：实装中发现、但不在本 change 范围的缺陷

> 归档会把本目录挪进 `archive/`，之后没人会翻到这里——**所以这两条必须在归档前另有去处**。
> 归档时须确认它们已进入各自的落点（协议那条进动协议的 change；素材那条进发布素材相关的 change 或 backlog）。

- [ ] 4.1 **协议文件里有一处失效注释**：`src/comm/protocol.ts` 提到已被拆掉的 `failed_before_submit`。
      该文件须与边缘侧逐字一致、且是并行 session 的热点文件，**不为一行注释制造漂移**——
      留给下一次动协议时一并改。
- [ ] 4.2 **页面状态未知档把素材归还而非隔离**（沿用旧行为，本次未改）：该档意味着提交**可能已经按下**，
      而归还等于允许另一条草稿取用同一组图。真按下去了的话，同一组图会在平台上出现两次。
      改它需要一并想清楚「可能已用」这个中间态怎么记，超出本 change 范围。

## 5. 交付

- [x] 5.1 `openspec validate defer-transient-publish-predispatch-failures --strict` exit 0。
- [x] 5.2 提交推送。
  <!-- aidcp-cloud master 84d7276（经 scripts/land-change 在 rebase 后 ff 合入并复跑全量）；
       控制仓 main ffd39ff9（提案）+ 96de54d5（两处前提修正）。 -->
- [x] 5.3 部署 dev 并核验。
  <!-- 2026-08-04 deployed —— **部署路线与 CLAUDE.md §5 的既有描述不同，务必看这段。**

       ① **dev 已于 2026-08-04 切换为派生三服务，单体 `aidcp-cloud.service` 已停用**（保留为回滚路）。
          本 change 改的两个文件属主为 automation ⇒ 现役进程是 `aidcp-automation`，
          部署位 `/opt/aidcp/automation`（**不是** `/opt/aidcp/cloud`）。
       ② **一条已过期的记载差点导致假部署**：change `fix-cloud-multi-service-deploy-script` 的 tasks 2.3
          写着「三个 unit 都从 /opt/aidcp/cloud/src/server.ts 以不同 AIDCP_SERVICE 启动」。那是该脚本
          的形态，已被本日切换取代。实测三个 unit 的 WorkingDirectory 分别是 /opt/aidcp/{api,automation,content}。
          照该记载操作＝同步到无人运行的目录 + 重启已停用的服务 + 以为部署成功。
       ③ 派生仓同步：`scripts/sync-split-repos --apply --repo aidcp-automation` 写入 3 个文件
          （两个改动文件 + preemption.ts 的一行注释同步），全部来自本 change，无夹带；
          提交推送 `aidcp-automation` master `8c7db6e`。**注**：CLAUDE.md §8.1 写的 `--check` 参数
          在脚本里不存在（实为默认 dry-run + `--apply`），文档已漂。
       ④ 安全序列：备份 `/opt/aidcp/automation.bak.20260804-151405.tar.gz`（1.8M）+ `.env.bak.20260804-151405`
          → rsync（--exclude .env/node_modules/.git，不带 --delete）→ 本地与远端 publish-dispatcher.ts
          sha256 前 16 位一致 `b6d0b623ca042722`、.env 完好 → **stop-then-start**（写者锁不变量禁止滚动）。
       ⑤ 健康核验：`aidcp-automation` active、新 pid 1199556、NRestarts=0；8787（边-云）与 8094（内部）
          由新 pid 持有；api/content 未受影响（旧 pid 保持）；单体仍 inactive（回滚路完好）；
          isales 4 个服务未受影响。schema 门 enforce/通过、同步读就绪度 ready、业务入口已放行。
       ⑥ **写者锁交接干净**：旧 pid 1181761 于 15:14:42 报告丢锁并 fail-closed 停止下发新互动命令，
          新 pid 1199556 于 15:14:43 持有。全程只有一个持有者。
       ⑦ 上线核实：部署位文件里新分档命中 15 处、`all_images_failed` 4 处；残留的 2 处
          `failed_before_submit` 经逐行核对均为解释历史的注释，活代码无旧值。
       ⑧ `/opt/aidcp/automation/.deploy-sha` 记为 `8c7db6ecb576c0d2ae00dd4d26cdc678f321903c`
          （此前三个派生部署位均无此文件）。 -->
- [ ] 5.4 真机验收项已登记 `docs/real-machine-acceptance-backlog.md` 簇 3（三条：可恢复档重投真能走完 /
      素材归还窗口是否被抢 / 重投耗尽的飞书文案）。**这三条未验之前，MUST NOT 把本 change 读成「已在真机验证」。**
