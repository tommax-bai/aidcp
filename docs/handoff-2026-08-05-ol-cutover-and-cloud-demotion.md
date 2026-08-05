# 交接：OL 已切三服务 + cloud 转为整图验证仓（2026-08-05 04:30–15:10）

> **新 session 从这份看起。**
> 上一份 `handoff-2026-08-04-draft-refinement-wired-all-deps-done.md` 写的事都已完成，
> 它现在只作背景（那些坑仍然有效）。再往前的只用于追溯。

---

## ⚠️ 0. 接手第一件事：OL 上 `scroll` 长期 100% 失败

**这是当前唯一一条正在持续损失价值的事，比本文其余全部都要紧。**

| 时段 | scroll 回执 |
| --- | --- |
| 08-04 全天 | 2868 次，**成功 0** |
| 08-05 切流前（单体） | 1092 次，**成功 0** |
| 08-05 切流后（派生自动化） | 同样全 false |

同期 `like` 64 次成功、`follow` 13 次成功 —— **只有滚动这一条，两天零成功**。

**切流前后比例完全一致 ⇒ 不是切流引入的**，是一条至少存在两天、无人报障的既有故障。
浏览是整条自动化的地基，它不动等于账号在空转。

```bash
# 复现（OL；把 key/host 换成 dev 的可对照）
ssh -i ~/codes/ol-0722.pem root@123.56.253.183 \
  'journalctl -u aidcp-automation --since "-3 hours" --no-pager \
   | grep -oE "action.completed: [a-z_]+ ok=(true|false)" | sort | uniq -c | sort -rn'
```

**我没有诊断它，只摆了事实。** 相关线索：日志里出现过
`Facebook Reels fallback 收到终止失败 native_effect_ambiguous → 释放`；
仓里有三条在做的相关 change（`restore-native-facebook-residual-parity` /
`harden-native-engine-runtime-contracts` / `enforce-native-engine-artifact-gates`）；
记忆里有 [[fb-feed-never-scrolls-down]]。**动手前先读代码确认缺陷还在**，登记比代码旧。

---

## 1. 现状与接手动作

**dev 与 OL 现在是同一形态**：都跑 api / automation / content 三个派生服务，单体停并 disable。

```bash
# ① 两个环境各跑一次（key/host 换一下即可）
ssh -i ~/codes/ol-0722.pem root@123.56.253.183 \
  'for s in api automation content; do printf "%-12s %s NRestarts=%s\n" "$s" \
     "$(systemctl is-active aidcp-$s)" "$(systemctl show aidcp-$s -p NRestarts --value)"; done;
   printf "cloud        %s/%s\n" "$(systemctl is-active aidcp-cloud)" "$(systemctl is-enabled aidcp-cloud)";
   ss -ltn | grep -cE ":8787|:809[0-4]";
   T=$(grep -m1 "^AIDCP_AUTOMATION_INTERNAL_TOKEN=" /opt/aidcp/automation/.env | cut -d= -f2-);
   curl -s -X POST -H "Authorization: Bearer $T" -H "Content-Type: application/json" -d "{}" \
     http://127.0.0.1:8094/internal/automation/sync-read/readiness'

# ② 六仓对账（硬要求）
scripts/sync-split-repos

# ③ 跨仓边界普查（本批新增）
scripts/boundary-census
```

**15:00 实测**：两边三服务 active、NRestarts=0、六端口全在、就绪 `ready` `blockers=[]`、
单体 `inactive/disabled`；OL 上边缘 10 条连接、6 个账号在跑；同步读中继已追平。

**各仓 head**（fleet 高度活跃，这些数字随时会被别的 session 推进——以 `git log` 为准）：
`aidcp@30a581bc` / `aidcp-cloud@79a4121` / `aidcp-kernel@030d805` / `aidcp-transport@f4b1e2c` /
`aidcp-api@e09079b` / `aidcp-automation@ce7a292` / `aidcp-content@33b8ecb`。

**盘子**：活跃 change 22 · 已归档 565 · 已合并 spec 193。

---

## 2. 这一段做完了什么

### 2.1 OL 切流（tasks 8.3a）

12:47–12:59，单体 → 三服务。发布分支 `release/20260805-ol-cutover`，
**刻意钉在 dev 上验过的基线**，不发主干头（建分支时主干刚被并发 session 推进 3 个我没验过的提交）。

切前勘察推翻两条前提，两条都会静默出事：
- **OL 的单体 env 与 dev 不是同一套键**（36 vs 53）。照抄 dev 的划分会丢掉 4 个 OL 独有键
  （schema 门放行位 / 养号爬坡回滚拉杆 / 飞书长连接开关 / OSS 内网标志）。改为**按代码逐键实读**。
- **OL 上没装 git**，而两个共享包是 git 依赖 ⇒ `npm install` 直接失败。dev 有，已装（环境 parity）。

边缘不是被我切断的：最后一条边缘指令在 12:03、紧接 5 条自发断连，到 12:47 停机之间零活动。
**切后两小时边缘自行重连**，端到端跑通。

### 2.2 清账与撤案

- **归档 28 个** ✓Complete 的 change（第六次分诊批）。活跃 49 → 21，spec 191 → 193，全库校验 214/214。
  真机项登记为 **backlog 簇 132**。
  ⚠ 那 28 个任务框全部勾满，却有 27 个从未登记真机项 —— **勾满 = 落地 + 部署，不等于验过**。
- **撤回 7 份零进度提案**（用户裁定「遇到 case 再处理」）。**分析先存档**再删：
  `docs/deferred-defect-proposals-2026-08-05.md`，含各自 file:line 与 git 出处。
  其中 6 份描述的是**已存在的缺陷**，1 份（账号归属被一次提交整个反转而无记录）是**记忆在流失**。

### 2.3 跨仓边界普查（`scripts/boundary-census`，本批新增）

补两处方向相反的结构性盲区：cloud 的整图门禁看不见派生仓私有件（api 5 / content 4 / automation 26）；
单仓门禁看不见跨仓边（而**跨属主读炸过两次线上**）。

**没有按原计划往两个仓各复制一份 1000 行扫描器** —— 因为 cloud 与 automation 那两份**已经漂开**，
复制只会变成四份互相漂。改成控制仓一处、跨仓看，判据全部从事实源读
（归属读各仓自己的规则、私有件名册读 `sync-split-repos`、边规则用真值表与 TS 原件双向核对）。

**第一次跑就抓到三件真的**：api 的边界规则比事实源少 1 条目录规则 + 77 条裁定；
一个私有组装根两处名册都没登记（`--prune` 会删它，而删掉的现形方式是慢启动限流静默失效）；
普查自己最初 11 条「悬空引用」全是没剥注释的假阳性。

四轮变异测试，**其中两轮抓出的是闸自身恒真**（自检比较的两个字符串在同一函数别处也出现）。

### 2.4 cloud 退役：结论是**降级，不是退役**

原估「128 个孤儿测试分家，3-5 个 session」——**实测推翻**。134 个里真正搬得动 **7 个**。

| 桶 | 分类阶段 | 真跑之后 |
| --- | --- | --- |
| 单一属主、可搬 | 18 | **7** |
| 跨 2+ 业务属主 | 97 | 97 |
| 整图 / 迁移 | 14 | **24** |
| 只测单体组装 | 5 | 5 |

分类看错的 10 个错法值得记：**import 只碰一个属主，正文却把别的属主源文件当数据读**
（`readFile(join(ROOT,'src/config',name))` 这类），基于 import 的分类器天生看不见，搬过去当场 ENOENT。
另一类是 schema 用例：需要**全部 108 条迁移**在一处，单仓只有自己那份（69/57/20）。

⇒ **跨属主不是分类偏差，是这套测试的本质**。完整分析见
`docs/cloud-retirement-blockers-2026-08-05.md`。**终局形态 = cloud 不再可部署，
继续当事实源 + 整图验证仓、永不部署。**

---

## 3. 收尾清单（按建议顺序）

### 先做：查 scroll（§0）

### A 组 —— 小、独立、走哪条路都要做

1. **把「aidcp-cloud 永不部署」写成规则**（`CLAUDE.md` §8，OVERRIDE 级）。
   现在只是「两个环境都 disabled」这个事实状态，**不是约束** —— 下一个人重新 enable 它不会撞到任何东西。
2. **合并两份漂开的边界扫描器**（cloud 与 automation 各一份 `boundary-scan.ts`，实测已不同）。
3. **共享包测试归位**：cloud 里还压着 kernel 10 / transport 10 个用例，它们有明确去处。
4. **记忆补两条**：跨仓普查的存在与判据；cloud 降级而非退役的结论。

### B 组 —— 当前 change 剩的核心，需要时间不需要写代码

5. **观察期**（tasks 7.1–7.4）：让三服务跑一段，**如实记录周期任务醒了几次、每次判定是什么**。
   唯一能发现「进程活着但什么都没干」的办法。**MUST NOT 用「进程一直活着」给任何一条划勾。**
6. **逐条从调用方那侧真打跨进程路由**（6.2）。
7. **更新 backlog 簇 60**（8.2）→ **归档当前 change**（8.4）。

### C 组 —— 只有用户能做

8. 在客户端上真点一遍（慢启动 / 今日进展 / 发布队列 / 收件箱 / **稿件精修**）。
   现在边缘真的连着，这条比之前更有意义。

---

## 4. 别再犯的（本段我犯过的）

- **转述的「对面拿不到 / 还没接」不能当结论。** 我照抄了一段过期注释，据此向用户报了「下一拍要接那条中继」，
  一 grep 就推翻（它构造了、启动了、游标与队首逐位相等）。代价不是做错事，是**凭空造出一拍不存在的工作**。
- **闸自己会恒真。** 两次变异测试抓出的是闸的判据写松了（比较的字符串在别处也出现）。
  **加闸之后必须变异测试，且要看「哪条用例抓住的」。**
- **估计要基于实测。** 「128 个测试分家 3-5 个 session」是照着分类数字估的，
  真跑之后只剩 7 个。**分类器看不见的东西，只有跑一遍才知道。**

---

## 5. 指针

| 东西 | 在哪 |
| --- | --- |
| OL 切流 / 镜像推进器根因 / 精修 | `openspec/changes/deploy-derived-services-to-dev/tasks.md` 8.3a / 8.8–8.10 |
| cloud 降级的完整论证 | `docs/cloud-retirement-blockers-2026-08-05.md` |
| 撤回的 7 份提案（含根因分析） | `docs/deferred-defect-proposals-2026-08-05.md` |
| 跨仓边界普查 | `scripts/boundary-census`（`--self-check` 只核规则） |
| 本批真机验收项 | `docs/real-machine-acceptance-backlog.md` 簇 132 |
| 上一段的全貌 | `docs/handoff-2026-08-04-draft-refinement-wired-all-deps-done.md` |
| 拆仓不变量 | `CLAUDE.md` §8（OVERRIDE 级） |
| 部署序列 | 属主域先起、接口域后起（content → automation → api） |
| OL 回滚 | 停三个 + `systemctl enable --now aidcp-cloud`；备份 `/opt/aidcp/cloud.bak.20260805-124740.pre-cutover.tar.gz` |
