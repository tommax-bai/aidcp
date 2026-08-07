# 交接 · 命令词汇改造（批 1–4 已落，批 5 是下一棒；批 7 新立）（2026-08-07）

> **给接手 session**：本文只承载**会随会话消失的东西**——裁定、工序、坑、待决。
> 已成规格与文档的只给指针，不重抄。上一份交接（`handoff-2026-08-06-command-vocabulary-batches.md`）
> 的批 4 开工须知已被本轮执行完毕并大幅修正，**以本文为准**。
>
> ⚠️ 凡本文写「已核」的只代表 2026-08-07。fleet 高度活跃，接手第一件事自己重核。

---

## 0. 一句话现状

命令语言的**宪法**（六条语法）+ **蓝图**（46 条 / 七批）已成规格；**批 1–4 全链落地并归档**
（协议 96 → 103，登记表 44 → 52）。**下一棒 = 批 5（互动对象化）**，它动的是全协议最危险的一处同步点。
唯一横在路上的是**出包**：dev 云端已说新词汇，旧客户端 fail-closed 拒收 ⇒ **dev 车队浏览停摆至装机**。

---

## 1. 权威产物指针（先读这些，不读旧对话）

| 产物 | 位置 |
| --- | --- |
| **命令语法 + 蓝图（七批逐条处置与状态）** | `docs/edge-command-grammar.md`（§6.2 逐条、§6.3 批次表：批 1/4 已标 ✅） |
| 语法规格（7 要求） | `openspec/specs/edge-command-grammar/spec.md` |
| 编址分层尺子（判「归哪层」用它） | `docs/edge-addressing-layers.md` |
| 批 4 归档（实装细节全在其 tasks.md §8 实录） | `openspec/changes/archive/2026-08-07-platformize-browse-vocabulary/` |
| 批 1–3 归档 | `openspec/changes/archive/2026-08-06-{drop-dead-cloud-edge-commands, recategorize-nonpage-commands, add-state-observation-command}/` |
| 真机簇 148 / 149 / 152 | `docs/real-machine-acceptance-backlog.md`（全部等同一次出包） |

**当前命令总账（以两份 protocol.ts 的 `MessageType` 穷举为准，文档计数会滞后）**：
103 消息类型 / 其中 52 条是云端可下发命令。浏览 22（xhs 14 + fb 8）、互动 5、视频号 IM 10、
发布 1（承 12 原子）、观察与身份 3、宿主环境编排 11。

---

## 2. 用户裁定（全部定案，MUST NOT 重议）

沿用上一份的 1–5 条（核心目标＝CLI 层清晰；平台进命令名＝编法 A；迁移直接切换无兼容层；
「确认不了」当发了；新增浏览器操作先过六条语法），**本轮新增/修正**：

6. **打包不是设计障碍，但打包动作只由用户显式触发**（长期授权 2026-07-08）——
   代码收尾到 commit/push/部署 dev 为止，**出包要等用户开口**。批 4 已提请，未获触发前不得自行打包。
7. **批 7（非平台域词汇收口）已立项**（2026-08-07 用户点出「这些名字不规范」）：
   蓝图 §6.2 新增小节写清四类不齐 + 两条**明确不做**（`ping`/`pong` 传输惯例豁免、`plan.response` 随 v1 死）。

---

## 3. 本轮建立/坐实的工序（照用，别重新发明）

- **双仓锁步落地**（批 4 实跑一遍，有效）：各 worktree rebase → 全量 + `gate:native` → **成对 ff push**
  （`git push origin <branch>:master` ×2，中间不跑闸）→ 立即 `scripts/protocol-parity` +
  `scripts/operation-registry-parity` 复验 → 部署 → 清 worktree。
- **改协议名的连锁清单（批 4 实测全套，批 5/6 会再遇到）**：
  ① 两份 `protocol.ts`（类型 + PayloadMap + 文内 prose）；② 两份操作登记表（**漏改 ⇒ 出口/入口闸判
  `operation_unclassified` 静默拒发，只有一行 warn**）；③ edge `edge-client.ts` 主动命令白名单
  if-链（**typecheck 抓不到**）；④ `command-diagnostics.ts` 三张结构；⑤ TS mapper（信封→kind、动作名表）；
  ⑥ 引擎 `command-manifest.json`（`edgeTypes[]`）→ **重建重钉 capabilityDigest 五位点**，
  其中 `src/electron/native-page-engine-artifact.cjs` 是**生产常量，漏了是启动硬失败**；
  ⑦ 云端 `command-bridge` 组合表 + `handler.ts` 归一表键 + 各直发点；⑧ 两份 protocol-contract 计数断言。
- **变异验证 MUST 先 commit 再变异**（旧坑，本轮未再踩）：实装 → 全绿 → commit → 变异 → 红 →
  `git checkout --` → **复跑确认回绿**。批 4 靠它抓出白名单断言盲区（删 `facebook.reels.scroll` 竟全绿）。
- **测试挂死先怀疑断言早抛**：本轮多次「超时」实为断言在清理句柄前抛出、服务端不关。
  另：macOS 无 `timeout` 命令；`npm test | tail` 会**把退出码换成 tail 的**——要真实退出码必须
  `npm test > file 2>&1; echo $?`（本轮曾据此误报过一次「全量通过」）。

---

## 4. 批 5 开工须知（下一棒的活，最危险的一批）

**范围**（蓝图 §6.2「互动平台化 + 按对象改名」5 条）：
`interaction.like` → `{p}.note.like` + `facebook.video.like`（按对象拆，视频已有独立概率策略）·
`interaction.collect` → `xiaohongshu.note.collect`（FB 无收藏）· `interaction.follow` → `{p}.user.follow`·
`interaction.comment` → `{p}.note.comment` · `interaction.like_comment` → `{p}.comment.like`。

**为什么它比批 4 危险**：批 4 只改了动作关联键映射表的**键**，值原样；
**批 5 必须动值**（`like`/`comment`/`comment_like`… 这些是云端角色的关联键）。那是 CLAUDE.md §2 点名的
**协议第 5 处同步点**：两侧各一张手抄表（edge `command-mapper.ts` 的 `actionNames` +
`src/facebook/facebook-session.ts` 的 `FB_COMMAND_ACTION_NAMES`；cloud `src/comm/handler.ts:126`
的 `LEGACY_ACTION_COMPLETION_ALIASES`），**字段两端都是裸 string、typecheck 抓不到**。
**错一条的后果不是报错，是角色永远等不到回执 + 调度器把它当未知失败动作、在详情页上下发 feed scroll**。

**开工前必须先做的两件事**：
1. **把动作关联键的消费面全量列出来**（批 4 探查已给出起点：cloud `handler.ts` 风控记账、
   `agents/*` 六处、`role-dispatcher` 约 20 处含 `noRecoverScroll` 集合、comment-agent 数处）。
   改值＝改这些比较的两边，**必须逐处配对改**，不能只改表。
2. **先给关联键设一道变异验证**：改坏映射表一条 → 必须有测试红。批 4 的教训是「不设就等于没有」。

**已就位的依赖**：平台段闸两端现役（批 4 转正）；bridge 已是 (action, platform[, surface]) 组合表，
加对象维只是扩表；`FACEBOOK_UNSUPPORTED_COMMANDS` 目前只剩 `interaction.collect` /
`interaction.like_comment` 两条共享名——**批 5 落地后该集合应归零删除**（批 4 已留注记）。

---

## 5. 批 6 / 批 7 备忘

- **批 6**：IM 族 `wechat.inbox.*`（10 条）· **发布平台段化**（`{p}.publish.command`，
  原子 kind 表分平台，**删载荷里的 `platform?` 可选字段**——它是全协议唯一「平台维度进载荷」的地方，
  且缺省静默当小红书，同时违反语法第 1、4 条）· `navigation.back` 与 `note.close` 定分工后平台段化
  （`note.close` 云端**零发送点**，回列表实际走 back）· `edge.task.*` → `task.*`。
- **批 7**（新立，蓝图 §6.2 有完整表）：验证码归一家（检测在 `risk.*`、协助在 `captcha.*` 是同一主题两个家）·
  应答命名三套约定并存（`.report` / `.observed` / 过去式）定一套 · `ui.snapshot` 名词形方向消歧 ·
  identity 两条平行化。**性质：纯内部词汇、不碰浏览热区，可与批 5/6 并行。**

---

## 6. 未收口的线头（按急缓）

1. **出包（唯一挡路项）**：dev 云端已发新名 ⇒ **车队浏览停摆至装机**。同一个包里积压：
   批 1–4 + 身份闸换血 + 问现状探针。真机簇 148/149/152 全等它。**用户开口才打。**
2. **api / content 两仓的 kernel pin 落后**（实测：api `v0.1.1`、content `v0.1.0`、automation `v0.1.2`）。
   批 4 因传输豁免名单点名旧 `note.close` 出了 kernel v0.1.2；两仓未升 ⇒ 其出口闸在副本 unknown 时
   对新名 `{p}.note.close` 不豁免。**它们不推浏览命令，故非阻塞，但升 pin 时要知道这是为什么。**
   （§8.2 口径：落后最新 tag 只报告不拦。）
3. **`state.read` 零触发方**：通道已通（`RoleDispatcher.askEdgeState()`），何时问 / 问完怎么改航向
   ＝**阶段四（观测决策上移）的开篇**，尚无人接。真机验收前需临时脚本手动调用。
4. **阶段三（动作/检查拆分）**产品前置已齐（裁定 4），排在词汇批后。
5. **已钉成棘轮的已知缺口**：`interaction.reply.send` 留痕却不受页面身份闸约束（API 路径），
   测试写死豁免集合「恰好这一条」；要不要给 API 写路径设独立身份闸＝产品裁决，**别静默扩豁免**。
6. **kernel 准入机器闸换家未完成**（invert-split-fact-source 5.7 递延项）：再收 kernel 成员前
   要先在 kernel 仓补准入测试。批 4 往 kernel 加东西时**没有**触发该缺口（只改了既有名单）。

---

## 7. 本轮弯路（别重走）

- ~~「批 1 遗留的 `browse_next`/`browse_scroll` 一并删」~~——`browse_scroll` 是**首帖探测的引擎内部载体**
  （`facebook/runtime.rs` 构造），删了断 FB 群评论链。**动引擎「死代码」前先 grep 内部构造点。**
- ~~「改名不改计数」~~——交接文档预判 AC-PROTO-02 计数不变，实际 95→103（平台变体展开净 +8）。
- ~~「`page.scroll` 按 feed/search 两面拆」~~——实际**三面**（Reels 是真面，原靠 `targetSurface` 载荷区分）；
  **群不是面**（群内滚动是引擎内部分解）。**面枚举必须从云端发送点的 reason 取值实测，不能照文档注释。**
- 「全量套件通过」若来自 `npm test | tail`，**退出码不可信**（见 §3）。本轮据此误报过一次。
- 并行 change 会撞真机簇号（本轮批 4 与 blocking-overlay 同占 150，已改 152）：**登记前先 grep 最大簇号。**

---

## 8. 接手起手式

```bash
git -C /Users/baitianxing/codes/aidcp branch --show-current      # main
scripts/task-preflight                                            # 四 canonical 全默认分支
openspec list                                                     # 活跃 change
python3 scripts/protocol-parity && python3 scripts/operation-registry-parity   # 应为 52 条
git -C ../aidcp-edge log --oneline -3; git -C ../aidcp-automation log --oneline -3
```

开批 5：照批 4 的 change 形态（proposal/design/specs/tasks + 实录节），工序照 §3，
**开工前先做 §4 那两件事**。批 5 是协议热区串行批，**不与批 6 并行**；批 7 可并行。
