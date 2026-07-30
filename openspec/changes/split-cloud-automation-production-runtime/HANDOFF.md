# 交接 · change `split-cloud-automation-production-runtime`

> 生成于 **2026-07-30 01:00**，pin 在 `aidcp-cloud@93d339b`。
> **⚠️ 已有增补：见 §0.5（2026-07-30 上午，`aidcp-cloud@e790e47`）——本文 §4.1 与 §6 第一步已过时。**
> **给接手 session 用：从头读到尾，按本文执行。**
>
> 本文里所有数字都是**当场跑出来的**，不是估算。但 fleet 活跃、数字会滞后——
> §0 的命令请自己重跑一遍，**以你跑出来的为准**。
>
> **⚠️ 本文最重要的一节是 §4「已 land 但没做完的」。** 那些是台账上写着「已做」、
> 但实际只完成了一半的项。不先读那一节，你很可能在一个假的绿色上面继续盖楼。

---

## 0. 接手第一件事（约 5 分钟）

```bash
cd /Users/baitianxing/codes/aidcp

# ① 起手自检：四个 canonical checkout 必须都停在默认分支（CLAUDE.md §7 铁律）
git branch --show-current                      # 必须 main
for r in aidcp-cloud aidcp-api aidcp-automation aidcp-content aidcp-kernel aidcp-transport; do
  printf "%-18s %-10s %s\n" "$r" "$(git -C ../$r rev-parse --short HEAD)" "$(git -C ../$r branch --show-current)"
done                                            # 六个都必须是 master

# ② 六仓源码 / 迁移 / pin 三项对账（只读）
./scripts/sync-split-repos                      # 只读对账；预期噪声见下方四条

# ③ 边界门禁
cd ../aidcp-cloud && npm run test:acceptance 2>&1 | grep "AC-BOUND metrics"

# ④ 台账（这是本 change 真正的进度尺）
python3 -c "import json;print(json.load(open('boundaries/composition-root-independent-blockers.json'))['summary'])"
python3 -c "import json;print(json.load(open('../aidcp-automation/boundaries/composition-root-independent-blockers.json'))['summary'])"

# ⑤ change 进度
cd ../aidcp && openspec validate split-cloud-automation-production-runtime --strict
```

**当前实测期望值（2026-07-30 16:00 更新到第三批之后；本文正文里 01:00 那版已作废）：**

```
cloud=843bac6  kernel=0a0a94e  transport=c7db33e
api=a28d134    automation=70addd5  content=747c128   （六仓 master，全部已推送、工作区干净）

AC-BOUND metrics {"sourceFiles":533,"ownershipEntries":533,"crossBoundaryEdges":0,
                  "involvingContent":0,"exemptionEntries":0,"frozenTotal":0,"delta":0,"unplanned":0}
cloud 台账 54 条   automation 台账 13 条    ← 门是 13 条，不是 14（1.7b 裁定撤了一条）
tasks.md 53/104
dev 部署 = 843bac6（迁移 0099 已 apply；REQUIRED_SCHEMA_VERSION 仍是 0097，刻意的，见 §0.5）
```

**fleet 活跃，这几个数还是会滞后——以你自己跑出来的为准。**

`crossBoundaryEdges` **不是 0** ⇒ 有人新增了跨服务耦合，先查清楚再往下走（棘轮只许下降）。

**对账输出里这四类是预期噪声，不是回归**（省下一次误排查）：
① 「组装根不同 2」会打印**三次**（每个业务仓一次，共 6 条 `⊘`）——组装根按设计从不同步；
② 自动化仓另有一条 `⊙ src/automation-composition-root.ts（派生仓私有组装根，只登记不覆盖）`；
③ 输出头部的「迁移残留 13 条」；
④ 因此末行**必然**是「存在差异。」——那句话在当前设计下永远会出现。

---

## 0.5 ⚠️ 本文写完之后又落了一批（2026-07-30 上午，`aidcp-cloud@e790e47`）

**先读这一节，否则你会去重做已经关掉的坑、或照着一条已被推翻的前提干活。**

已落（两个提交，都在 `aidcp-cloud` master 上，**dev 尚未部署、派生仓尚未同步**）：

| | 内容 | 状态 |
| --- | --- | --- |
| `5323ee5` | **§4.1 已关闭**：7 条委托路由迁到信封 + Bearer 形态；业务拒绝的 `name` / `status` 经附加位过线并按补集判据还原 | ✅ 变异实测过 |
| `5323ee5` | **裁定文档步骤 0-a 已修**：分号批子命令 id 的分隔符由 `:` 改 `-`，机械判据落在用例 18 | ✅ 变异实测过 |
| `e790e47` | **裁定文档 J 条已修**：委托异常改按结构化守卫分流，「未送达 / 结果未知」不再被画成「你的话没说清楚」 | ✅ 两条用例覆盖 |

验证：cloud typecheck 0、acceptance 174/174、全量 3913 pass / 0 fail（基线 3900，+13 恰等于新增用例数）；
`crossBoundaryEdges` / 豁免仍为 0。**台账两份一条没少（55 / 14），这是对的**——本批全是搭桥。

### 三条会改变你下一步动作的实测事实

1. **§6「第二步」的步骤 0-b 靶子是死代码 —— 已由用户 2026-07-30 裁定并执行：以论证消掉台账、契约留着。**
   **台账因此第一次真的少了一条：cloud 55→54、automation 14→13**（详见 tasks.md 1.7b）。
   撤的理由不是「接好了」，是**这条欠账记在了错的条目上**——api 模式下这两条能力真正的失败走
   委托通道，由 `feishu-operator-natural-language-delegate` 承接（那条仍在）。能力仍被覆盖，少的只是重复计数。
   **⇒ 你的门现在是 13 条，不是 14 条。** 原始论证如下：
   `/publish`、`/comment` 在生产里**永远走委托分支**——统一命令面把 `delegate` 声明成必填、组装根恒注入
   一个函数（缺服务时是函数**内部**抛，不是不给函数），所以 `CommandRouter` 那个三元的另一支不可达；
   而面板那份动作面里**没有** publish / comment。⇒ 两个手动指令端口今天**没有任何活的 api 侧调用方**。
   给它们补消息 id 透传 + 接线，等于新增一处「看着接好了、其实永不触发」的假绿。
   两条出路（都行，但**必须显式选**）：以论证消掉那条台账，或裁定这两条命令应绕开委托路径直发。

2. **写幂等台账的下一个迁移号是 `0099`，不是 `0080`**（详见 tasks.md 1.5a）。
   裁定文档援引的 `0079_risk_command_outcome` 是**判例**不是队尾——现有 97 个迁移、数字序最大是 `0098`，
   且 0079 那张表本身已被 0080 扩过一次（真实形状是 0079+0080）。
   耦合单元是**四处**：新迁移 + `KNOWN_MAX_SCHEMA_VERSION`（有测试钉死它等于 migrations/ 最大版本）
   + 该常量上方那段逐迁移追加的裁定 JSDoc（那是事实上的登记面）+ `table-ownership.json` 追一条 owner=automation。
   另：**`AC-OWN-06`（跨属主表读）无豁免通道**，api 侧回读这张表只能经内部 API。

3. **「不许在客户端补默认 `status`」这条不变量的守卫，不在端到端那两条用例上。**
   实测：把还原改成「缺 status 就补 400」，用例 5（409）与 6（422）**照样绿**——那两条路径服务端确实带了字段。
   真正抓住它的是**还原判据的单测**与**传输错误透传那条用例**。
   谁日后以「409/422 已经覆盖了」为由删掉那个单测，这条闸就无声消失。

### 又一批：接收方 + 幂等台账已落（2026-07-30 16:00，`aidcp-cloud@843bac6`）

**§6「第二步」的步骤 1 已完成。** 新的六仓基线在下面那个代码块里，**别再用 `e790e47` 那行**。

| 落地物 | 位置 |
| --- | --- |
| 迁移 0099（幂等台账表，属主 automation） | `migrations/0099_operator_command_receipt.sql` |
| 台账（PG 实现 + 测试用内存实现） | `src/delegated-task/operator-command-ledger.ts` |
| 唯一接收方（自由文本 + 调度启停） | `src/delegated-task/operator-command-receiver.ts` |
| 契约用例 19 条里的 17 条 | 见 tasks.md 1.5 |

**dev 已部署并跑过迁移**（`migrate status` 确认待应用恰好 1 条 → `migrate up` → 重启）。
schema 门逐属主全通过，`operator_command_receipt` 只在 automation 库在场。

### 四条会影响你下一步的实测事实

1. **`REQUIRED_SCHEMA_VERSION` 还停在 0097，是刻意的**——接收方还没接进任何进程。
   **接线那一批 MUST 同时**抬 REQUIRED、在部署序列里**重启之前**跑 `npm run migrate up`、并对 ol 补同一步。
   漏了会怎样已实测：门是 segA 第一句、裸 await、无 try/catch ⇒ 抛出即 exit 1 ⇒ systemd
   `Restart=on-failure`/`RestartSec=5`、无告警 ⇒ **每 5 秒静默重启的崩溃循环**。「behind」档**无豁免通道**。
   **补迁移只能用 `npm run migrate up`**：`scripts/run-migration.ts` 执行 SQL 但不写账本，
   用它补完表在库里、门照样判 behind，现场看着「表明明在」——最费时间的一种排查。

2. **`sync-split-repos` 对迁移文件只报不改**：新迁移要手工拷进属主仓（对账会报「缺 1 条」）。

3. **派生仓的 `boundaries/*.json` 手抄件又咬了一次**（0.7c 第二次兑现）。这次是 automation 那份
   `table-ownership.json` 缺新表。**但这次漂移是响亮的**（迁移属主检查当场红），
   与上次 `ownership-rules.json` 漂 88 行那次的**静默**不同——这条区分影响 0.7c 的优先级，此前没记。

4. **接下来是步骤 2 起**：四组路由的服务端注册 + 客户端接到接收方与内部客户端（`operator-command-http.ts`
   已就绪、只用不改），然后放宽取数聚合口的类型，最后在组装根把四个接线点全改指同一个口
   （**`src/server.ts` 是热点，必须等它让出来**）。

### 上一批的收尾（已闭合）

- **派生仓同步 + pin 链 ✅**：按 §5.2 顺序全跑完。**六仓新的对齐基线**（§0 那段期望值请按这行核，
  不要再用 `93d339b` 那行）：

  ```
  cloud=843bac6  kernel=0a0a94e  transport=c7db33e
  api=a28d134    automation=70addd5  content=747c128      （六仓 master，已推送、工作区干净）
  测试 cloud 3932 / api 473 / automation 1926 / content 439 / kernel 59 / transport 36，全 0 fail
  AC-BOUND crossBoundaryEdges 0 · exemptionEntries 0 · frozenTotal 0 · sourceFiles 533
  台账 cloud 54 / automation 13   ← 1.7b 裁定撤条那次减的，本批未再减（本批是搭桥）
  dev 部署 = 843bac6（含迁移 0099 已 apply）
  ```

- **dev 部署 ✅ 第五批 `e790e47`**（仍是单体形态）：备份 `cloud.bak.20260730-113238.tar.gz`；
  健康检查全过（三个属主库各自 `select 1` 全通、飞书长连接已建立、8787/8090/8091 在监听、重启后错误 0）；
  isales 四服务全程未触碰。**现网真正变的只有那处飞书渲染分流。** ol 未部署、用户未提。
  另：本批 cloud 侧 `package.json` 零变更（pin 抬的是三个派生仓），故 ECS 上没动 `node_modules`。

---

## 1. 这个 change 在解决什么

`aidcp-cloud` 拆成三个业务仓（接口 / 自动化 / 内容）+ 两个共享包。
**跨服务耦合早已归零**（96 → 0，前序 change 完成）。剩下的主交付物是「三个仓各写自己的启动入口」：

- **接口仓、内容仓**：已有真手写入口。
- **自动化仓**：入口至今是**有意 fail-closed 的壳**——读完配置就抛「未就绪」，
  因为它欠的东西有一张 **14 条的清单**（`aidcp-automation/boundaries/composition-root-independent-blockers.json`
  + `src/automation-composition-root.ts` 里那个同名常量，两者 deepEqual 有断言看着）。

**这个 change 就是承接那 14 条的**（用户 2026-07-29 拍板；此前 12 条标着 `closingChange: 'future'`、无人承接）。

**清单不清零，就不能把入口从 fail-closed 切成真启动。** 这是硬顺序，不是流程洁癖。

---

## 2. 进度（2026-07-30 01:00）

> **⚠️ 下表是 01:00 的快照。当前是 53/104**（第 1 段已推进到 11/19，见 §0.5 两批）。
> 段内明细请跑 `openspec status --change split-cloud-automation-production-runtime`，别照抄本表。

| 段 | 完成（01:00 快照） | 内容 |
| --- | --- | --- |
| 0. 准入与三个岔口裁决 | **37/58** | 开工前把有争议的判断钉死 |
| 1. 四条运营指令通道 | **4/11** → 现 **11/19** | 指令从接口侧送到自动化侧 |
| 2. 内容侧属主授权 | **4/10** | 自动化隔着进程用内容库 |
| 3. 自动化真启动入口 | **0/6** | ← 主交付物 |
| 4. 台账清零与门禁 | **0/5** | 清零 + 焊死不可倒退 |
| 5. 派生对账、验收、收尾 | **1/7** | 六仓对齐、部署、归档 |

**已部署 dev 六批**（**全是单体形态**）：`b66c022` → `9ae8e1d` → `1b36b74` → `93d339b`
→ `e790e47` → `843bac6`。每批都走安全序列（备份 → rsync →〔本批多一步：`migrate up`〕→ 重启
→ 健康检查），六次都零错误、同机 isales 全程未碰。**ol 一次没动**（用户没提线上）。

**⚠️ 分层验收口径（tasks.md 5.3，别混）**：
契约测试证明路由与客户端形状；**dev 单体部署只证明「现网零回归」**；
**三进程真跑属批次 5，本 change 一次都没证明过，也不声称。**

---

## 3. 那 14 条清单 —— 逐条现状（这是真正的门）

自动化侧台账 14 条，分三组。**今晚给不少条搭了桥，但一条都没撤**——
撤条目要有「本进程真的在用它」这个事实，客户端建出来了不算。

### ① 四条运营指令（送不进去）· 对应第 1 段

| id | 现状 |
| --- | --- |
| `feishu-operator-natural-language-delegate` | 契约已写（kernel 窄口 + 传输三件套），**未接线** |
| `feishu-operator-publish-comment` | 同上 |
| `feishu-operator-delegated-card-actions` | 同上 |
| `feishu-operator-dispatch-start-stop` | 同上；组装根占位桩已撤（1.4a） |

**1.4d 已裁定**（详见本目录 `delegated-task-channel-adjudication.md`）：
「两条通道二选一」是**伪二选一**——两者方法集**零重叠**。要收口的是**传输纪律**（统一到信封 + 鉴权 + 服务端注入执行目标）
与**注入点**（**四个**接线点全改，不是记载的三个；接口仓里还有第五处直连）。

**⚠️ 接线前必须先解决一个缺陷**（该文档 §3 步骤 0-a）：
飞书分号批命令给每条子命令编的消息 id 用冒号拼接，而冒号正是幂等键的分段分隔符、
合法性检查明确拒绝含它的分段 ⇒ 键算出来是 null ⇒ 按契约必须拒发 ⇒
**每一条分号批里的委托 / 发帖 / 评论都会被拒发，而且拒得「有道理」，最难查。**

### ② 九条内容库授权（拿不到东西）· 对应第 2 段

| id | 现状 |
| --- | --- |
| `content-concept-write-authority` | 契约 + 路由已注册 + 客户端已建；**缺生产消费者** |
| `content-curated-write-authority` | 同上 |
| `content-facebook-publish-media-authority` | 契约已写；**路由未注册、未接线** |
| `content-token-usage-authority` | 契约已写；**路由未注册、未接线** |
| `content-textcard-transcription-authority` | 能力二态端口已写；**未接线** |
| `content-role-factories` | 待岔口 B 落地（tasks 2.5） |
| `content-generic-llm-authority` | 待岔口 A 落地（tasks 2.5） |
| `content-reply-generation-authority` | 未开工（tasks 2.6） |
| `content-publish-rejection-evidence-authority` | **⚠️ 14 条里唯一一条此前无人承接**，已补 tasks 2.9 |

### ③ 一条组装 · 对应第 3 段

`automation-production-runtime-composition-unwired` —— 就是那个空壳入口本身。

**顺序是硬的**：①② 不清完，③ 写不了。第 3 段 0/6 不是拖延，是前置没到。

**⚠️ 而且「tasks.md 全做完」不等于「台账能清零」。** 上表那条驳回证据授权此前**没有任何 task 承接**
（我一度误以为它属于传递性检查那条，实测不属于），已补 tasks 2.9。
**清零的门是台账那 14 条，不是 tasks.md 的条数**——两者不是同一把尺，别拿后者当进度终点。

---

## 4. ⚠️ 已 land 但**没做完**的（先读这一节）

这些项在 tasks.md 里标了 `[x]`，但**只完成了一半**。台账注释里都写了限定，但很容易被跳过。

### 4.1 六处错误识别点：迁移做了，**跨进程仍然认不出来** — ✅ **已于 2026-07-30 关闭（`5323ee5`），本节留作背景**

- **做了什么**：三个文件六个调用点，从「按原型判断错误类型」改成结构化守卫。
- **没做什么**：**内部传输的错误编码只保「码 + 文案」，把「类型名」和「HTTP 状态」丢在那一跳**，
  而守卫判的正是类型名 ⇒ **真跨进程时那六处仍然恒 false**。
- **后果**（与 kernel 注释里预言的一字不差）：版本冲突退化成普通错误提示且不再回刷新卡、
  接口侧的 409 / 422 一律塌成 500、后台控制台发起的委托任务同样塌成泛化 500。
- **为什么今天不炸**：单体不过那一跳。
- **补法**：`delegated-task-channel-adjudication.md` §2.5 —— 服务端把丢掉的两个字段塞进传输错误的
  附加位，客户端用 kernel 里**已经写好但零消费**的**补集判据**还原。
  **HTTP 状态 MUST 由服务端带过来，MUST NOT 在客户端补默认 400**（补 400 会把 409/422 一并压平；
  那个错误类的 `status` 默认值恰好就是 400，所以「补默认」看着人畜无害）。
- **落点已经定死，不用再找**（`src/transport/internal-http.ts` 的错误编码函数）：
  - **第一分支**（仅对传输层自己的错误类）**保**附加位；
  - **第二分支**（「带字符串错误码的任意抛出物」——委托那个错误走的正是这条）**只回码 + 文案，连附加位一起丢**。
  ⇒ 补法必须由服务端**主动包一层传输层错误类**再塞附加位，**不能指望现成路径**
  （405 / 404 / 401 / 400 那几条走的另一个简易出口也不带附加位）。
- **顺手一起做完**：`src/transport/delegated-task-http.ts` 那 7 个客户端方法**全是裸调用、零错误处理，
  且用的是不带鉴权的那个出口**——所以 1.7①（无信封无鉴权）与 1.7②（守卫恒 false）
  是**同一个文件里的同一次改动**，分两轮做是白费一遍。
- **教训**：同一个坑我在内容侧两个端口的文档里写过（「只写『不用原型判断』是不够的」），
  **却没在委托这一族关上**。两处只堵了一处。

### 4.2 内容侧端口的守卫也有同一层要求，别以为端口文档写了就等于做了

`concept-pool-port.ts` / `curated-selection-port.ts` 的文件头明写：
传输适配层 **MUST** 先按码还原、再重新抛出；**还原不出返回 `null` 时 MUST NOT 套默认原因**。
`content-authority-http.ts` 做到了。**新写传输三件套时照它办，别照端口文档的字面意思办。**

### 4.3 内容侧监听上还剩一处口径分裂

老的裸形态精选路由（无鉴权、无信封、无目标校验）与新的精选召回路由**同进程并存**。
路径不冲突，但同一个域两套鉴权口径。登记在 `CONTENT_AUTHORITY_WIRING_DEBT` 第 6 条。

### 4.4 派生仓自己那份归属规则表是**手抄件**、不在同步范围内

- 自动化仓那份与事实源已差 **88 行**，且**早就**漏了两条裁定。
- **为什么一直没人发现**：平时跑的检查读的是**已生成**的产物，正好把窟窿盖住；
  只有跑「刷新归属」才当场抛。
- 今晚按事实源补齐了这三处，**但结构问题没动**（tasks 0.7c）：
  要么让同步脚本把规则表也纳入对账，要么让派生仓不再自持规则表。

### 4.5 两处已经长在派生仓里的不诚实写法，**下一步接线别照抄**

- 接口仓手写入口里：状态灯硬回 `false`（把「不知道」答成「停着」）。
- 同一处：幂等键里塞随机数 ⇒ 每次重试新一个 ⇒ 幂等键形同虚设。
- 都还没上生产（那三个进程在 dev 上根本没有 systemd 单元）。
- 出处**分开的**：`delegated-task-channel-adjudication.md` §3 步骤 0-b 只点名了**随机数那处**；
  状态灯硬回「停着」那处在同一份文档的 **§5 第 K 条**。

### 4.6 1.7③ 的范围要缩：**是三条不是四条**

调度启停改的是**进程内的一个布尔**。给它持久幂等台账，会让重启后一次真实启动被判「重复」
并回放陈旧事实——**那是编造**。4a 的边缘恢复接收方有逐字同形的判例：状态是进程内的，台账就该是进程内的。

### 4.8 ⚠️ 自动化那份台账派生器是**永久手写分叉，而且零机械信号**

这条最阴，因为它**直接戳在「台账是机械派生所以诚实」这个主张上**。

两份同路径、同导出名的台账派生器（中控侧 1916 行 / 自动化侧 1792 行）：
自动化那份首行带 `// aidcp:test-owner=derived`，而同步脚本把带这个标记的文件**从两侧同时减掉**
（期望集减掉它、实际集也减掉它）⇒ **既不会被覆盖，也永远不会被报成漂移**。

**后果**：本批在中控侧对探针做的所有改进（标识符使用类探针、接缝过滤放宽、更正后的注释）
**一条都到不了自动化那份**，而且**没有任何东西会提醒你**。
自动化那 14 条台账是它算出来的——所以那份台账「机械派生」的程度，取决于这个分叉有多旧。

**接手动作**：动中控侧派生器时，**当场决定**自动化那份要不要同改；
若不同改，在两份文件里都写明「本分叉刻意存在，理由是 X」。tasks.md 里那条（第二个 `0.3g`）已勾，
但勾的是「记下来了」，不是「解决了」。

### 4.7 其余已登记的小项

- `0.3g` —— 标识符使用类探针不在接缝过滤范围内，实测有 2/11 落在死分支；本轮如实未处理（要处理需另行裁定，那会真的删证据行）。
- `0.3h` —— 另一个接缝过滤器仍是老式字符串正则，量词与新判据不同，混用会改变输出。
- `0.5g` —— 缺席的真正上游在角色调度器，刻意延后（理由已写在台账里）。
- `0.6i` 遗留 —— 精选库不可用错误的守卫**刻意只按名字判、不要求原因码**：要求它会让守卫对「跑着旧版本的对面」恒 false。
- `0.6j` 已修 —— 传输目录的规则描述曾把「必须有 SQL」写成了准入条件（那只是第一批成员的形态）。

---

## 5. 工作纪律（今晚踩出来的，别重踩）

### 5.1 land 前**逐仓**扫 worktree 脏状态

一个任务的改动可能落在**多个仓的 worktree** 里。今晚 0.3f 的改动同时落在 cloud 与 automation 两个 worktree，
cloud 那半提交了、automation 那半**留在工作区没提交**，而 automation 的分支已经合进主干推出去了。

**这种漏不会报错**：两份台账各自自洽、测试照绿，只是自动化的欠账表里多留了一条不属于它的债——
而两份台账**本来就允许不同**（问的是不同的问题），所以没有任何机械手段会比对它们。

```bash
CH=split-cloud-automation-production-runtime      # 这行不是占位符，照抄可用
for r in aidcp-cloud aidcp-automation aidcp-api aidcp-content aidcp-kernel aidcp-transport; do
  d=../$r.wt/$CH; [ -d "$d" ] || continue
  printf "%-20s dirty=%-3s behind=%s\n" "$r.wt" \
    "$(git -C $d status --short | wc -l | tr -d ' ')" \
    "$(git -C $d rev-list --count HEAD..origin/master 2>/dev/null)"
done   # dirty 非空即停
```

**顺带查 `behind`，§5.1 原来只教了查脏**：2026-07-30 实测六个 worktree 全部 clean，
但**五个落后于各自 master**（自动化 −1、内容 −1、接口 −4、kernel −5、transport −5，只有中控仓 worktree 等于 master）。
直接在落后的 worktree 上开工，等于**从过期基底重新派生**，而且下面 §5.2 那条抬 pin 的链条
会按过期的 kernel / transport 头去算。开工前先 `git fetch && git rebase origin/master`。

### 5.2 同步顺序：**先把 src 和测试全同步完，再抬 pin**

```bash
./scripts/sync-split-repos --apply --prune        # ① src（--prune 才会删搬走的旧副本）
./scripts/sync-split-repos --apply --tests        # ② 测试（不删，「多出」要人工删）
# ③ 再按 kernel → transport → 三个业务仓 抬 pin
```

**为什么**：`--tests` 那趟**也会给 kernel 派测试文件**。我是在三个业务仓 pin 已经抬完之后才跑的，
kernel 头一动，transport 与三个业务仓的 pin 全部作废，整条链重抬一遍。

**另外**：`--prune` 与 `--tests` **互斥**（脚本硬拦，理由是派生私有测试必须显式保留）。
派生仓私有的测试要加 `// aidcp:test-owner=derived` 标记，否则会被判「多出」。

### 5.3 pin 是**派生事实**，漂了不报错

三个业务仓 + transport 的 kernel pin **MUST 恒等于** kernel master 头。
装到旧 sha **不报错、编译照过**，跑的却是过期契约。`sync-split-repos` 会对账，**每次都看一眼**。

**`npm install` 的绕法是「装不上时才用」，不是 MUST**：本机 `~/.npmrc` 把 `@types` 域指向内网 registry，
历史上曾因此装不上（memory `split-repos-npm-install-blocker`）。**2026-07-30 实测那个 registry 是通的**，
默认配置能完整解析。真装不上时再加 `--userconfig /dev/null`——
**别把一个正常环境当坏环境处理**。

**另一件容易误判成事故的事**：自动化仓**不消费** `aidcp-transport` 包，它自持 `src/transport/` 下 50 个文件，
其中 39 个与共享包重合（接口仓 / 内容仓走包引入，自动化仓走相对路径）。
**这是同步脚本的设计**——成员在归属清单里仍标自动化，只是同时复制进包供三家共用；
对账输出里那句「未 pin aidcp-transport」也是脚本自己的设计文案。
**不是** CLAUDE §8.4 点名的「复制成两份、两端路径悄悄对不上」那种事故。

### 5.4 别高估 typecheck（实测，两轮变异）

把整条路由注册删掉，typecheck **会**红——但红的是「入参解析器成了孤儿」这个副产物，
**一旦解析器被两条路由共用，这个信号就消失**。
而**真实的滑手形态**（注册时手写一遍路径、不用共享常量）**typecheck 完全绿**，只有测试当场红。
这就是「路径常量只能有一份」的全部理由。

### 5.5 行号会漂，台账注释**只写符号名**

今晚每一路都报告了行号漂移（最多差 65~71 行）。cloud 的组装根尤其——
并行 session 在写它的时候，行号在你读的过程中就变了。
**定位按符号名，行号只作导航并标 sha。**

### 5.6 部署纪律

只从主 checkout 的默认分支目标提交 `git archive` 出干净快照部署，**绝不从 worktree 部署**。
安全序列：命名 target → 测试通过 → ECS 先备份 → rsync（排除 `.env` / `node_modules` / `.git`）→ 重启 → 健康检查 → 失败即回滚。
**绝不碰同机 isales**（四个独立服务）。**ol 必须用户明确要求且走发布分支。**

---

## 6. 下一步怎么走（顺序是硬的）

### ~~第一步 · 关掉 §4.1~~ — ✅ **已完成（`5323ee5`）**，验收信号两条都过，另见 §0.5 第 3 条

### 第二步 · 第 1 段接线（closes 四条台账）

按 `delegated-task-channel-adjudication.md` §3 的六步走。**步骤 0 的状态已变**：
0-a（分号批分隔符撞车）**已修**；0-b（手动发帖/评论稳定键）**靶子是死代码，须先重新裁定**——见 §0.5 第 1 条。
⇒ 现在真正的起点是**步骤 1：automation 侧那个唯一的接收方 + 幂等台账**（迁移号见 §0.5 第 2 条）。
该文档 §4 给了 19 条契约用例，每条注明「它红的时候在说什么」。
幂等台账形状照 `0079_risk_command_outcome` 的判例，含崩溃窗口那一格的裁定
（读到进行中态 MUST 回「结果未知」，既不判重复也不重跑）。

### 第三步 · 第 2 段剩下的（closes 九条台账）

- 先落两个岔口的裁决（tasks 2.5：模型调用出口、四个角色工厂）。
- 发帖素材 + 用量记账两组：契约已在，**注册路由 + 自动化侧接线**。
  用量那条要注意端口是「提交已合并的增量」而不是逐条上报——属主今天**没有**这个方法，
  content 接线时补方法或交适配对象（与精选库那条同形）。
- tasks 2.7 的传递性检查：**特别点名 optional 参数**，那是静默缺席的主要来源。

### 第四步 · 第 3 段：自动化真入口

组装根骨架已相当完整（属主池、接口客户端、指令接收方、同步读镜像、内部服务端都在），
缺的是 `main()` 与就绪闸。**就绪闸照接口仓那份的形状办**（design.md §4 有模板：
监听先起、业务入口靠标志位 + 去重 promise、定时器 unref）。

### 第五步 · 第 4 段：清零 + 门禁

台账两份同批收缩 → 入口从 fail-closed 切真启动 → `boundaries:refresh` 逐条对账 → acceptance 红线全过。

### 第六步 · 第 5 段：收尾

六仓对账、dev 部署、真机项登记 backlog、归档。

**⚠️ 「簇 60」在 `docs/real-machine-acceptance-backlog.md` 里出现两次，别登错**：
要登的是**文件头部 2026-07-26 那个说明块「簇 60『云端拆仓 Phase 0–4 的真机验收』」**；
文件里另有一个正式标题段 `## 簇 60 — 桌面客户端 mac 签名+公证包`，grep「簇 60」会**先撞它**。
（该文件当前最大簇号是 121。）

### 然后才是**批次 5**（不在本 change 内）

**三个进程在 dev 上真跑起来。** 至今没开工。
今晚四次部署全是单体形态，**一次都没证明三进程能跑**。

---

## 7. 文档索引

| 文档 | 用途 |
| --- | --- |
| `openspec/changes/split-cloud-automation-production-runtime/tasks.md` | 任务台账（97 条 + 大量 `<!-- -->` 裁定记录）。**注意它不是「能否收工」的事实源**——那把尺是自动化侧那 14 条清单 |
| 同目录 `design.md` | 三个岔口、就绪闸模板、Phase 0 勘察结论 |
| 同目录 `delegated-task-channel-adjudication.md` | 1.4d 裁定 + 1.3/1.5 落地步骤 + 19 条契约用例。**⚠️ 它的行号 pin 在 `aidcp-cloud@1b36b74`，不是本文的 `93d339b`**——那份文档通篇是行号，解析前先 `git show 1b36b74:<path>`，或直接按符号名定位（同批符号已漂 31~53 行） |
| `docs/cloud-service-decomposition-proposal.md` §4.7 / §7.2.1 | **归属的唯一事实源** |
| `docs/cloud-cross-service-coupling-resolution.md` | 耦合处置执行清单 |
| `docs/cloud-composition-root-trisection.md` §0.0 | 组装根三等分进度卡 |
| `docs/cloud-split-next-session-handoff.md` §0.1/§0.2 | 拆仓项目整体交接（比本文范围更大） |
| `CLAUDE.md` §8 | 拆仓期间一律 OVERRIDE 的不变量（事实源 / 编辑纪律 / 消边判据 / 准入 / 红线形态） |

---

## 8. 一句人话

拆仓分两半：**把纠缠解开**、和**让第三个进程真能启动**。第一半早就做完了。
现在卡在第二半，卡点很明确——自动化那个进程欠的东西有一张 14 条的清单，
清单不清零就不能声称它能独立跑。

**这一批做的全是给那 14 条搭桥，桥搭了不少，但一条都还没拆掉。**
台账那 14 条一条没少，就是这件事最诚实的度量——它是从源码派生出来的，
不会因为我们做了很多工作就自己变小。

**但连这句话都要打个折**（§4.8）：算出那 14 条的派生器，自动化侧那份是**手写分叉**、
不会被同步、也不会被报成漂移。所以「机械派生所以诚实」的成立程度，取决于那个分叉有多旧。

**接手时最该警惕的不是「还没做的」，是「看着做完了其实只做了一半的」（§4）。**
