# Native 引擎迁移修复 — 交接

> 状态时间：**2026-07-29**。接手时先按下面「起手校验」跑一遍，**正文里的所有计数都是快照、会滞后**。
> 本文档面向「换一个 session 从零接手这批工作」的场景，不是设计文档。上位背景见
> `openspec/changes/restore-native-*/proposal.md` 与各自的 `oracle.md`。

---

## 1. 这批工作是什么

2026-07-22~23 把 `aidcp-edge` 的页面自动化从 TypeScript 迁到 Rust Native Page Engine。迁移的等价性判据定在
**命令信封**（消息名 + 参数形状）上，而真正的行为契约在状态机、时间预算、后置校验里——这些不在那张消息表上，
于是整体蒸发。小红书侧约 11200 行 TS 被 290 行页内脚本取代，没有任何机制提示少了什么。

复盘用了两条独立路径交叉核实（正向扫来源 + 机制反推），产出 6 个承接 change。本批工作就是把它们实装。

**为什么问题一边倒集中在 Facebook**：边缘侧唯一一行逐命令回执诊断被「仅 Facebook」的判断包着，小红书跑完整轮
浏览闭环，日志里只有启动与失败两行。**没证据 → 没人发现 → 没 change → 翻记录也翻不到。** 这是自我强化的盲区：
Facebook 侧十几个提交修回，小红书侧零个修复 change，且小红书真机验收从迁移到现在**一次都没做过**。

---

## 2. 起手校验（先跑，别信正文数字）

```bash
cd /Users/baitianxing/codes/aidcp
openspec list | grep -E "restore-native|harden-native|enforce-native"

git -C /Users/baitianxing/codes/aidcp branch --show-current        # 必须是 main
git -C /Users/baitianxing/codes/aidcp-edge branch --show-current   # 必须是 master
git -C /Users/baitianxing/codes/aidcp-edge log --oneline -1        # 期望含本批 10 个提交的头
```

Rust 工具链**不在默认 PATH**，跑 cargo 前先：

```bash
export PATH="$HOME/.rustup/toolchains/1.97.1-aarch64-apple-darwin/bin:$PATH"
```

边缘仓全套门禁（本机唯一真门禁，见 §6）：

```bash
cd /Users/baitianxing/codes/aidcp-edge
npm run typecheck && npm run test:acceptance && npm test && npm run gate:native && npm run build:dist
```

---

## 3. 已落地的状态

**edge master = `a05bee9`**，本批 10 个提交已 rebase 到最新主干并 ff 合入、已推送。**未部署、未出安装包、未做任何真机写动作。**

按提交时间倒序：

| sha | 内容 |
| --- | --- |
| `a05bee9` | 引擎运行时契约：声明变成断言 |
| `7b8d556` | 小红书会话守卫：接通阻断监测与提交窗口 |
| `811edf2` | 删除恒假短路的宿主装配 |
| `4a2c8d4` | 重建指针原语与定位三闸 |
| `b550f1e` | 小红书动作诚实：如实回报发生了什么 |
| `cda524a` | 产物门禁：让泄漏与陈旧两道闸变真 |
| `7c532c8` | Facebook 残余对齐 |
| `5989018` `d21f6a8` `5e18af1` | 失败优先的表征用例 + 评论/开帖两条 critical 修复 |

**门禁实测（合并后跑的）**：全量 **2697 例 / 2696 绿 / 0 红 / 1 跳过**；验收红线 30/30；类型检查通过；
Rust 门禁（格式 + 静态检查 `-D warnings` + 测试）通过；生产剪枝通过（可达 77 / 移除 68 / 页面规则分片守卫 11）。

**change 进度快照（会滞后，以 `openspec list` 为准）**

| change | 进度 |
| --- | --- |
| `restore-native-xiaohongshu-action-honesty` | 37/61 |
| `restore-native-facebook-residual-parity` | 37/70 |
| `harden-native-engine-runtime-contracts` | 30/60 |
| `restore-native-xiaohongshu-session-guards` | 24/50 |
| `enforce-native-engine-artifact-gates` | 23/55 |
| `restore-native-actuation-humanization-and-locating` | **13/74** ← 缺口最大 |

---

## 4. 下一步：第四波

**关键前提**：宿主装配入口（`src/main.ts`）与引擎主入口（`native/page-engine/src/engine.rs`）现在都腾出来了，
上一波所有被迫压后的活，卡的就是它们。

### 4.1 会话守卫收尾 — `restore-native-xiaohongshu-session-guards` §3 + §5

- §3 验证码协助键入取证（3.1–3.6）：现在 `inputMode` 是**按请求推断**的，不是按实际派发。
  下发了文本却一个字符都没打进去时，回执仍会标成"点击并键入"。要补结构化取证（焦点分级 / 清空三态 /
  实际派发字符数 / 回读三态 / 是否已提交），并让 `inputMode` 只在**确有字符派发**时为 `click_type`。
  红线：中途被抢占或超预算时，字符数必须是实际派发数、**不得回退到请求文本长度**，且不得执行提交。
- §5 运行期身份持续校验（5.1–5.5）：长跑会话在两次启动之间换号或掉登录，现在发现不了。
  5.5 的重立链顺序是硬约束：停周期观测 → 停浏览 → **在途发布诚实判失败（MUST 在关连接之前，否则失败回执发不出去）**
  → 断开云端 → **先导航回消费端首页再读身份** → 读不出即停在无身份态、**绝不回落默认账号（红线）** → 换云端会话重连 → 重设基线 → 重启。
- **5.6 是【阻塞 · 待人裁定】**，不要开工。

主要落点：`src/main.ts`，另需 `native/page-engine/src/engine.rs` 的验证码回执结构体扩容。

### 4.2 拟人化 — `restore-native-actuation-humanization-and-locating` §4 + §8

这是缺口最大也最要害的一条：

- **§4 云端下发的时长根本没人消费**。云端算好的「动作前犹豫」与「离页停留」一路解析进结构体就没了，
  Rust 侧零读取点。节奏这一层现在整个是死的。
  4.3 有个反例陷阱：**不得对云端已下发的值二次乘风控档位**（退役的 Facebook 会话就是这么双乘的，别照抄）。
- **§8 小红书写动作没接上已有的拟人原语**。Rust 侧已经有与退役实现参数逐项一致的逐字输入原语与惯性滚轮原语，
  小红书路径完全没接线——现在还是"一次性把值写进去 + 手动派发合成事件"。
  接线方式：在引擎的小红书分发里**新增命令特化分支**截走命令，**不改页面规则那份**（引擎侧截走后其分支不可达，
  删除由单写区属主处置）。
  8.3 有条真机教训：正文换行必须拆成**独立的裸回车按键**，文本写入一律不带回车符，每次回车后做有界归尾确认——
  否则会留下逐渐积累的文末尾字。

主要落点：`native/page-engine/src/engine.rs`、`input.rs`、`src/native-page-engine/browse-session.ts`。

### 4.3 并行安排

4.1 与 4.2 都要动引擎主入口，**必须串行或分 worktree 后串行集成**。
建议：4.1 走 `src/main.ts` 为主，4.2 走引擎侧为主，两者对 `engine.rs` 的改动分区（验证码回执 vs 小红书分发），
集成时先 fetch + rebase 再合。

### 4.4 再往后

- 运行时契约剩余：重连时重新解析端点（`engine.rs`）、会话结束收尾移进 `finally`（`browse-session.ts`）、
  身份证据判据**接线到真实附着路径**（见 §5 的「别误读」）。
- 产物门禁 + 命令清单那 14 条声明修正：**必须同一个提交**（清单摘要被构建契约测试反向绑定到 Electron 侧的期望常量，
  改一边会让打包校验带着对不上的摘要出门）。
- 控制仓收口 → 真机验收项登记 → **cloud 分支**（用户 2026-07-28 定：先做完 edge）。

---

## 5. 绝不能误读成"已完成"的几件事

这批工作反复踩的就是「看着有、其实没通电」。下面每条都要按原样理解：

1. **端点身份证据判据已落成但未接线。** 判据与失败语义写在端点选择模块里、有单测覆盖，
   但**没有接到真实附着路径**——那需要引擎分发层 + 宿主传入的分身身份。**MUST NOT 当成已生效的防护。**
   在它接线之前，同机多环境并行时端口被回收复用，仍可能附着到别的环境的浏览器上。

2. **锚点暂存区结构就位但在生产上可证为空。** 当前每个定位器都是编译进二进制的固定选择器，没有任何不确定来源，
   所以暂存区永远收不到东西。有一条测试专门把这件事钉死，**防止被读成"定位自愈已恢复"**。

3. **周期观测的宿主订阅未接线。** 会话侧的暂停 / 恢复能力已实现且幂等，但订阅"执行器连接不可恢复 / 重连"的那一半
   在宿主装配文件里，本批没接。未接线前，连接死掉后探针仍会按节拍空轮询。

4. **提交窗口预算表同时是准入白名单。** 不在表里的标签会被判成契约违规并否决窗口，而拿不到窗口的写入不派发。
   引擎新增一处窗口却漏改宿主那张表，后果**不是"少一层保护"，而是那处写入全部拒发**（回执诚实，但功能停摆）。
   本批的 `7b8d556`（接窗口）与 `a05bee9`（加标签）**必须同批部署，单独回滚任一个都会让小红书写入停摆**。

5. **小红书评论点赞仍无提交前阻断复检。** 提交前闸只接了点赞 / 收藏 / 关注 / 评论提交四条。
   补法：在引擎侧那张受闸动作名映射里补一条。

6. **会话启动的首次扫描不经停手闸。** 它不走云端命令入口、也没有可回执的信封。
   后果是会话启动瞬间若正停在登录墙上会多滚一次；首个周期探针之后的所有命令都受闸。

7. **`facebook-consent-structural-detect` 这个 change 指向的实装文件已经没人引用了。**
   `src/facebook/consent.ts` 还在仓里，但 `src/` 内除自身外零引用；切换后真正生效的同意条探测在页面规则里。
   该 change 起草于切换之前，**照原文实装等于加固一段永不运行的代码**。已在其 `tasks.md` 顶部写了必读订正。

---

## 6. CI 已上主干，但它跑不起来

`aidcp-edge` 新增了 `.github/workflows/checks.yml`（push / PR 触发，跑 TypeScript 门禁 + Rust 格式 / 静态检查 / 测试）。
它是随本批合并进主干的，**而且确实被触发了**。

**但每一次 run 都在 3~5 秒 failure，原因是 GitHub 账号计费被拒**
（"recent account payments have failed or your spending limit needs to be increased"）。这是账号级的，
任何 runner 都起不来——仓里原有的出包流水线同样在失败。

**在计费恢复之前，边缘仓唯一真门禁是本机手动跑的那几条**，而大家合并用的统一脚本 `scripts/land-change`
至今**一行 Rust 都不跑**。近两万行 Rust 与全部构建脚本仍然不在任何自动流程里。

**别把"CI 已配好"当成已覆盖。** 计费恢复后要做两件事：① 确认工作流真能跑完并通过；
② 再决定本机门禁要不要按需接进合并脚本（用户已同意"持续集成先上主干"，第二步待定）。

---

## 7. 两条已裁定 + 三条待裁定

### 已裁定（用户 2026-07-29）

- **同意条歧义：维持"认不准就停手"。** 曾提出按 DOM 包含关系先去重再判歧义（依据：候选采集含带标签的普通容器，
  嵌套时同一个按钮会被数两遍）——**未被采纳**，因为那只是读代码推出的假设、从未在真机上观察到。
  已承接为真机观察项（`facebook-consent-structural-detect` 任务 3.3.1）：真机上真碰到"认不准"时先 dump 一次 DOM 坐实，
  **取证前不得改判据**。
- **持续集成先上主干。** 已做（见 §6）。

### 待裁定（阻塞对应任务，不要绕过）

- `restore-native-xiaohongshu-session-guards` **5.6**：身份翻转 / 重连后"重注入连接级节奏快照"这一步在 Native 形态下归谁。
  未裁定前 5.5 的那一步既无法实现也无法声明不做。
- `restore-native-actuation-humanization-and-locating` **7.16**：锚点暂存区的前提在新引擎里不成立（无任何非确定性锚点来源），
  裁定"保留空结构 / 改判据 / 暂不做"之前不得开工、也不得按已实现勾掉。
- 同 change **7.17**：可换的页面来源与执行层两个接口在迁移中消失，相关任务的验证方式取决于裁定结果。

---

## 8. 这批工作反复踩到的坑（接手务必知道）

### 8.1 夹具红了，先问"它编码的是旧行为还是实现有问题"

本批至少四次遇到：测试变红不是因为实现坏了，而是因为**夹具把被修掉的缺陷形态写死成了断言**。

- 三条 Facebook 用例把点击写死成"恰好三个鼠标事件"。多帧轨迹是十九次移动 + 按下 + 抬起。
  照它改实现 = 把"瞬移再点"这个机器特征原样种回去。已改为断言形状不变量（必须逐帧、按下抬起各一次且成对、
  落点在有界抖动内），helper 是 `assert_humanized_single_click`。
- 一条小红书用例的点赞控件不在互动栏结构内——正是新代码要拒绝的情形。改夹具为真机结构。

### 8.2 死码会把检查喂绿——**已发生三次**

- 一条按源码文本计数的检查要求某入口守卫恰好出现 2 次，失败文案写着"被移除的路由不得再出现"，
  而那 2 次里有 1 次就在恒假死码里。
- 一条新用例断言"两条页面命令路由的抑制分支都会回执"，第二条同样在死码里——
  也就是说**当初那半个修复落在了永不运行的代码上**。
- 一条平台驱动测试断言小红书驱动必须引用退役的浮层监测体模块。照它改会把退役模块拖回生产产物——
  实测那个无调用点的工厂成员正因值导入让四个退役模块一直随安装包发出（生产可达 81→77）。

**判据**：否定式的检查（"某某不得出现"）尤其危险，它可能正被它要禁止的东西维持在绿色。

### 8.3 并行编辑同一工作区 = 静默覆盖

同一个 worktree 里两个 agent 改同一个文件会互相覆盖，git 不会替你合并未提交的改动。
本批的做法是**给每条流一份互不重叠的文件白名单**，撞到别人文件的任务一律记进"待办"而不是硬改，集成时串行补。

### 8.4 集成拖得越久越贵

分叉 6 个提交、才两天，就有 **6 个文件冲突**，全在最热的路径上（引擎主入口 / 宿主会话 / 宿主装配 /
FB 信息流与短视频 / 页面规则分片 / 共享测试夹具）。这类文件冲突解错**不会报错，只会静默丢一块行为**。
**解冲突必须按行为对齐，不能按文本凑**——本批两处典型：

- 短视频：主干加了轴向导航，本流换了滚轮手势 → 合成"保留轴向结构 + 里面的滚轮换成手势"，不是二选一。
- 恒假死码：主干正好在里面改过东西 → 照删，它本来就不执行。

### 8.5 页面规则不是 Node 环境

`native/page-engine/src/*.js` 与 `facebook-router/*.js` 是构建期异或混淆后编进二进制、运行时注入页面执行的。
不能用 TypeScript、不能 import、不能依赖 Node API。改完需重新构建才生效。

**另外**：所谓"规则已加密"只挡扫读级别——异或密钥在已构建产物里直接搜得到。别基于错误前提把更敏感的东西塞进这条通道。

---

## 9. 开发方式：换回一个 change 一个 worktree

用户 2026-07-29 同意从"六个 change 挤一条分支"换回项目本来的规范（`docs/parallel-dev-worktrees.md`、`CLAUDE.md` §7）：
**一个 session = 一个 change = 一条分支 = 一个 worktree，四者同名**，worktree 放 `../<repo>.wt/<change-name>`。

理由就是 §8.4 亲眼看到的。worktree 分不掉冲突，但它让冲突**在合并时暴露**，而不是在共用工作区里被悄悄覆盖。

**但要清楚**：剩下的几条 change 仍然共用引擎主入口那几个热文件，所以**集成必须串行**，
worktree 只是让每次冲突小一点、看得见。

分支 `native-migration-repair` 已合入主干、使命结束，其 worktree
（`/Users/baitianxing/codes/aidcp-edge.wt/native-migration-repair`）可以清掉。

---

## 10. 硬约束（照抄自 `CLAUDE.md`，别在这批工作里破例）

- **四个 canonical checkout 的分支指针永远停在各自默认分支**（`aidcp`=`main`，edge / cloud / console=`master`）。
  要分支隔离就另开 worktree。**绝不在 canonical checkout 里 checkout feature 或 release 分支。**
- **部署只从主 checkout 的 eligible ref 走，绝不从任何 worktree 部署。** 本批全程未部署。
- **`ol` 部署只有用户明确要求才做**，且必须从发布分支。`dev` 是默认目标。
- **桌面安装包默认不打。** 只有用户明确要求"打安装包 / 出包 / 发版"时才执行。
  edge 代码改动的默认收尾只到提交 / 推送。
- **force-push / 非 fast-forward / 推到非默认 protected 分支仍需先确认。**
  （本批为 rebase 后同步特性分支做过一次带 lease 的 force-push，已向用户报备。）
- **文档 / 提交 / tasks.md 里不写任何密码、token、私钥内容**，只记路径、服务位置、命令用法、配置读取方式。
- **红线**：MUST NOT 静默假成功；失败判定必须是结构性的；按实测回报不得回报请求值；
  「读不到」与「没有」是两态，不得压成一态。

---

## 11. 相关文档

- 6 个 change：`openspec/changes/restore-native-xiaohongshu-action-honesty/`、`restore-native-xiaohongshu-session-guards/`、
  `restore-native-actuation-humanization-and-locating/`、`harden-native-engine-runtime-contracts/`、
  `enforce-native-engine-artifact-gates/`、`restore-native-facebook-residual-parity/`
  —— 其中四个带 `oracle.md`（退役 TypeScript 实现的逐条摘录，含"不可照抄"的告警），**实装前先读**。
- 真机验收项：`docs/real-machine-acceptance-backlog.md`
- 并行开发操作手册：`docs/parallel-dev-worktrees.md`
- 部署口径：`docs/deployment-environments.md`
