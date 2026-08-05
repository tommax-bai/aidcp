# 交接：面板修复上 OL + 空库验证跑出结论（2026-08-05 15:10–21:00）

> **新 session 从这份看起。**
> 上一份 `handoff-2026-08-05-ol-cutover-and-cloud-demotion.md` 仍作背景，
> **但它的 §0 已被本段推翻并就地更正**（原文折叠保留）。再往前的只用于追溯。
>
> **待办清单不在本文里** —— 在 `docs/split-project-remaining-work-2026-08-05.md`，
> 那份每一条都实读过代码或真机。本文只讲「这一段发生了什么、别再踩什么」。

---

## 0. 接手第一件事：**没有正在损失价值的事，但有两条线上带伤**

上一份交接把「OL scroll 两天 100% 失败、账号空转」列为最高优先级。**那是误报，已更正。**
浏览一直满负荷在跑（同 6 小时账本记了 1703 次真实浏览 / 193 点赞 / 14 关注），
在睡的账号是**今日浏览额度用满**。误报根因是按回执的**布尔** `ok` 做汇总，
把三态里的「没能确认」压成了「失败」——**本仓红线「三态不得压成一态」这次压在了度量上，不在控制流上**。

真正带伤的是这两条（详见待办清单 §一）：

1. **OL 接口服务「一重启就再也起不来」**，今天靠放行位临时救回；结构问题未解。
   共库 + 一个**未完成 change** 的迁移已应用 ⇒ 所有不含该迁移的构建当场失去启动能力，**回滚也救不了**。
2. **`event_outbox` 一个主题只进不出**，约 1.6 万行/天。
   ⚠️ **已有 change 接手且挖得更深**：`bound-event-outbox-growth` ——
   根因不是我以为的「剪裁名单漏了一条」，是**「变没变」的判据里混进了时钟**
   （载荷带 `asOf: Date.now()` ⇒ 摘要每次必变 ⇒ 必发通知），
   而那条流在派生进程里内容**恒定为空**。**全库最大的数据生产者，报的是「这里什么都没有」。**
   → 别重复立项，去读那个 change。

---

## 1. 现状与接手动作

**dev 与 OL 形态一致**：都跑 api / automation / content 三个派生服务，单体停并 disable。
**OL 今天动过两次**（能力名修复 16:00、面板能力 16:30–17:00），两次都健康。

```bash
# 两个环境各跑一次（key/host 换一下）
ssh -i ~/codes/ol-0722.pem root@123.56.253.183 \
  'for s in api automation content; do printf "%-12s %s NRestarts=%s\n" "$s" \
     "$(systemctl is-active aidcp-$s)" "$(systemctl show aidcp-$s -p NRestarts --value)"; done;
   printf "cloud        %s/%s\n" "$(systemctl is-active aidcp-cloud)" "$(systemctl is-enabled aidcp-cloud)";
   ss -ltn | grep -oE ":(8787|809[0-4])" | sort -u | tr "\n" " "; echo'

scripts/sync-split-repos     # 六仓对账
scripts/boundary-census      # 跨仓边界普查
```

**各仓 head**（fleet 高度活跃，**必然**已经变了——以 `git log` 为准）：
`aidcp@64cb3565` / `aidcp-edge@cc6001c` / `aidcp-cloud@11bacad` / `aidcp-kernel@5aab64b` /
`aidcp-transport@7d10d2f` / `aidcp-api@5b11654` / `aidcp-automation@60f9022` / `aidcp-content@0cbb648`。

**今天新建的 OL 发布分支**（三仓同名 `release/20260805-ol-panel`，各自接在 OL 基线之上）。
`aidcp-automation` 还多一条 `release/20260805-ol-capability-names`（能力名修复那次）。
**回流已满足**：两次改动都先落主干、再 cherry-pick 到发布分支，主干不欠债。

**拆仓四个 change**：`deploy-derived-services-to-dev` 42/47 · `restore-panel-capability-wiring` 46/49 ·
`cloud-service-boundary-gates` 36/41 · `cloud-schema-migration-executor` 62/68。

---

## 2. 这一段做完了什么

### 2.1 修掉一条拆仓引入的真回归（dev + OL 都已上）

派生 automation **手抄边缘能力名、四个都漏了 `_v1` 后缀** ⇒ 四道版本偏斜闸对**所有**连接恒判「没有」
⇒ **新客户端被静默当成老客户端**（Reel 自动关注一次都没下发过、免导航身份读用不上）。
两侧都是裸 `string`，typecheck 一个字都不说。

**诊断链值得复用**：云端每条 Reel 都打「边缘没有 reel_follow 能力」，
而同一批日志里边缘回的原因串是**某日期之后才引入的** ⇒ 边缘构建必然更新 ⇒ 矛盾只能出在云端读名。
**不必拿到边缘就能判是哪一侧错。**

修法：改按协议常量比对 + 三条守卫用例（第三条专喂「漏后缀的错名」）。
**两轮变异测试并记了是哪条抓住的**：抄回短名两条同时红；改成「两种写法都认」只有第三条红
⇒ 第三条独立承重、不是重复。

⚠️ **行为验证仍未拿到**：复查那 5 分钟账号都在配额睡眠、评估器一次没跑，
「零告警」**分母是 0、不算证据**。等有账号带配额跑到 Reel 上才算真验过。

### 2.2 面板能力修复上 OL（三仓 22 个提交里只挑本 change 的）

上线前先坐实缺陷仍在：OL 实跑文件的 blob 哈希与「本 change 第一个提交之前」**逐位相同**。

**没发主干头**：主干已被并发 session 推前 13/6/17 个提交，
**非本 change 的那些属于 4 个尚未完成的 change**。三仓各开发布分支、cherry-pick，零冲突。
共享包 pin 一致；三仓 typecheck 0、acceptance 19/27/277 全绿。
**ECS 上必须重装两个共享包**（pin 变了，漏这步会跑着旧契约且不报错）。

结果：原先 503 的三条全部 200，另八条也 200。
`/api/captcha-assist/*` 仍 503 但回**具名** `upstream_route_missing`（该能力 OL 未开，与 dev 同形）。

### 2.3 「全新空库拉起」验证：**真跑了，没通过**

用户先问「迁移不是早完成了吗，为什么还要验」。**跑完的答案是：**
「迁移已应用」只对**现存的库**成立；这套迁移在全新环境上**第 30 条就断**。

`0030_panel_hardening_indexes` 一条横跨两个属主库
（`risk_counters`/`interaction_feed` 归 automation，`llm_token_usage` 归 content）
⇒ **物理上不可能在任何单一属主库里跑通**。`migrate status` 自报**13 条**迁移头部没属主声明、
被计入全部三个属主，每条都会在不该跑它的库里撞墙。

**顺带先撞上的另一条**：**三个派生仓的 `npm run migrate` 一条都跑不起来**
（`scripts/migrate.ts` 仍引用已搬进 kernel 包的文件，本机与 ECS 都不存在）
⇒ **今天唯一能跑迁移的仍是 `aidcp-cloud`，也就是刚被定为「永不部署」的那个仓。**

**环境**：本机 Homebrew PostgreSQL 16.14 临时集群，用完 stop + 整目录删。
**一根手指没碰 dev/OL** —— 那台的 pg_hba 是**按库名逐条列**的，加临时库得改共享认证配置，
而 isales 同机共用，不值得为一次性验证冒险。

### 2.4 观察期收官 + 台账按代码实核

- **观察期**（7.1/7.3/7.4）已收官。15 项基线里 11 项落点确认在跑，挖出两条「日志上看不出来」的：
  委托任务泵**起了但一句话不说**（「起了」与「没起」同形，靠查表反推）；`event_outbox` 那条。
- **四条「记载滞后」的台账项按代码实核后结案**（2.3 / 2.6 / 6.1 勾上）。
- **5.3 改判**：那 36 条角色 import **一条都不跨边界**（对应文件全在 automation 仓自己里），
  真跨边界的 4 条已由内容角色工厂注册表解决、豁免棘轮归零 ⇒ **不再需要那个独立 change**。
  正文里「43 条」是立项当日估计，其批注 2026-07-23 就改判成 4 条了，**正文没跟着改，又骗了一轮**。
- **`aidcp-cloud` 永不部署**已写成 `CLAUDE.md` §8.0 的 OVERRIDE 规则。
- **真人验证项已交接给用户**（用户 2026-08-05 声明持续验证中），
  两条 change 任务据此结案；**backlog 83 条一条没删**（登记表 ≠ 任务表）。

---

## 3. 别再犯的（本段我犯过的 / 差点犯的）

- **只按布尔成功率做汇总会凭空造出故障。** 上一份交接把最高优先级给了一件没在发生的事。
  判「某个动作是不是坏了」**先去问记账表**（记既成事实的地方），再看回执布尔；
  汇总回执**必须按 reason 分组**。
- **反过来也成立：分母是 0 的「零告警」不是证据。** 部署后「0 条能力缺失日志」看着像验过了，
  其实那 5 分钟评估器一次都没跑。
- **别只看「import 行数变少了」就判任务做完。** 差点据此把 `2.4` 勾上——
  实读发现两处只收窄了一处（另一处的 kernel 接口压根不存在），结论正好相反。
- **台账正文里的数字会骗人，而且是二次骗。** `5.3` 的「43 条」在批注里早改判成 4 条，
  正文没改 ⇒ 上一轮我照着它给用户建议了「把 36 条单独立项」，实核后是无用功。
  **引用任何数字前先看同条的批注。**
- **回滚不是万能出口。** OL 接口服务那次，备份里的旧构建同样起不来——
  部署前要问的不只是「能不能回滚」，还有「回滚到的那个东西现在还起得来吗」。

---

## 4. 指针

| 东西 | 在哪 |
| --- | --- |
| **待办清单（每条实读过）** | `docs/split-project-remaining-work-2026-08-05.md` |
| 空库验证的完整结论 | `cloud-schema-migration-executor` tasks 5.9 批注 |
| OL 面板上线 + 重启即死 | `restore-panel-capability-wiring` tasks 9.4a / 9.4b |
| 能力名修复 + 选项键差集普查 | `deploy-derived-services-to-dev` tasks 6.2b |
| scroll 误报的完整证据 | 同上 6.2c；交接文档 `…-ol-cutover-and-cloud-demotion.md` §0 |
| 观察期收官记录 | `deploy-derived-services-to-dev` tasks 7.1 第 2 条 |
| 消息表那条（已有人接手） | change `bound-event-outbox-growth` |
| 真机验收登记 | `docs/real-machine-acceptance-backlog.md` 簇 60 / 132（用户持续验证中） |
| 拆仓不变量 / cloud 永不部署 | `CLAUDE.md` §8（§8.0 为本段新增） |
| OL 回滚 | 停三个 + `systemctl enable --now aidcp-cloud`；
  备份 `/opt/aidcp/{api,automation,content}.bak.20260805-163822.pre-panel.tar.gz` |

---

## 5. 建议的下一步（细节见待办清单 §建议顺序）

1. **契约门默认值改 enforce + 记跑满天数** —— 条件早满足（两台环境变量都已是 enforce、
   线上覆盖证据 07-25、到今天 11 天），半小时；**今天 OL 那次事故刚好证明这道闸有用**。
2. **修派生仓的迁移 CLI** —— 它卡着「每批部署前先跑迁移检查」，
   还让「永不部署的仓」成了唯一能跑迁移的地方。
3. **补 13 条属主头 + 拆跨属主的** —— 补完再跑一次空库验证就能过。
4. 共库规则（未完成 change 的迁移不许上共库，或反过来同批推构建）。

前两个 change 补完各自剩下的代码项即可归档。
