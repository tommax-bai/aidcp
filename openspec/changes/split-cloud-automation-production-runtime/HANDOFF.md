# 交接 · change `split-cloud-automation-production-runtime`

> **重写于 2026-07-30 17:00**，pin 在 `aidcp-cloud@843bac6`。
> 上一版是「原稿 + 三层增补」摞起来的，读的人得自己对账三个年份——**上一手就因此把一处行号 pin 认错了**。
> 本版按「现在是什么」组织，不再按「哪一批改了什么」；历史沿革在 git log 与 tasks.md 的 `<!-- -->` 里。
>
> **本文最重要的是 §3（门的逐条现状）与 §4（看着做完了、其实只做了一半的）。**
> 不先读 §4，很可能在一个假的绿色上继续盖楼。
>
> 文里的数字都是当场跑出来的。但 fleet 活跃、数字会滞后——**§1 的命令请自己重跑，以你跑出来的为准。**

---

## 1. 起手自检（约 5 分钟）

```bash
cd /Users/baitianxing/codes/aidcp

# ① 四个 canonical checkout 必须都停在默认分支（CLAUDE.md §7 铁律）
git branch --show-current                      # 必须 main
for r in aidcp-cloud aidcp-api aidcp-automation aidcp-content aidcp-kernel aidcp-transport; do
  printf "%-18s %-10s %s\n" "$r" "$(git -C ../$r rev-parse --short HEAD)" "$(git -C ../$r branch --show-current)"
done                                            # 六个都必须是 master

# ② 六仓源码 / 迁移 / pin 三项对账（只读）
./scripts/sync-split-repos

# ③ 边界门禁
cd ../aidcp-cloud && npm run test:acceptance 2>&1 | grep "AC-BOUND metrics"

# ④ 门（这是本 change 真正的进度尺，不是 tasks.md 的条数）
python3 -c "import json;print(json.load(open('../aidcp-automation/boundaries/composition-root-independent-blockers.json'))['summary'])"

# ⑤ change 进度
cd ../aidcp && openspec validate split-cloud-automation-production-runtime --strict
```

**2026-07-30 17:00 实测期望值：**

```
cloud=843bac6  kernel=0a0a94e  transport=c7db33e
api=a28d134    automation=70addd5  content=747c128    （六仓 master，已推送、工作区干净）

AC-BOUND metrics {"sourceFiles":533,"ownershipEntries":533,"crossBoundaryEdges":0,
                  "involvingContent":0,"exemptionEntries":0,"frozenTotal":0,"delta":0,"unplanned":0}

门：automation 台账 13 条（cloud 那份 54 条，两份不同口径、不能直接比总数）
tasks.md 53/104
dev 部署 = 843bac6（迁移 0099 已 apply）；ol 一次没动
测试 cloud 3932 / api 473 / automation 1926 / content 439 / kernel 59 / transport 36，全 0 fail
```

`crossBoundaryEdges` **不是 0** ⇒ 有人新增了跨服务耦合，先查清再往下走（棘轮只许下降）。

**对账输出里这四类是预期噪声，不是回归**（省一次误排查）：
① 「组装根不同 2」打印**三次**（每个业务仓一次，共 6 条 `⊘`）——组装根按设计从不同步；
② 自动化仓另有一条 `⊙ src/automation-composition-root.ts（派生仓私有组装根，只登记不覆盖）`；
③ 输出头部的「迁移残留 13 条」；
④ 因此末行**必然**是「存在差异。」——当前设计下这句永远会出现。

---

## 2. 这个 change 在解决什么，以及**两把尺**

`aidcp-cloud` 拆成三个业务仓（接口 / 自动化 / 内容）+ 两个共享包。
**跨服务耦合早已归零**（96 → 0，前序 change 完成）。剩下的主交付物是「三个仓各写自己的启动入口」：
接口仓与内容仓已有真手写入口；**自动化仓的入口至今是有意 fail-closed 的壳**——读完配置就抛「未就绪」。

它欠的东西是一张清单（`aidcp-automation/boundaries/composition-root-independent-blockers.json`
+ `src/automation-composition-root.ts` 里那个同名常量，两者 deepEqual 有断言看着）。
**清单不清零，就不能把入口从 fail-closed 切成真启动。这是硬顺序，不是流程洁癖。**

### ⚠️ 两把尺，读错会高估进度

| | 现值 | 它衡量什么 |
| --- | --- | --- |
| tasks.md 条数 | 53/104 | **「查清了多少」，不是「交付了多少」。** 分母会随勘察长大——最近两批往里加了 7 条实测发现的新任务 |
| **那张清单（门）** | **13 条** | **真正的交付物。** 从 14 降到 13，而那 1 条还是**以论证撤的**（欠账记在了错的条目上、被算了两遍），不是靠干活减的 |

**收工的判据是门清零，不是 tasks.md 打完勾。** 两者不是同一把尺，别拿后者当进度终点。

**分层验收口径（tasks 5.3，别混）**：契约测试证明路由与客户端形状；**dev 单体部署只证明「现网零回归」**；
**三进程真跑属批次 5，本 change 一次都没证明过，也不声称。**

---

## 3. 门：13 条逐条现状

| id | 组 | 卡在哪 |
| --- | --- | --- |
| `feishu-operator-natural-language-delegate` | 指令 | 契约 + 接收方 + 台账全齐，**只差组装根接线** |
| `feishu-operator-delegated-card-actions` | 指令 | 同上（注入同一个端口即同时点亮它与自由文本那条） |
| `feishu-operator-dispatch-start-stop` | 指令 | 接收方已建（**刻意无持久台账**，见 §4.5），差接线。注：**「飞书 dispatch」这条通道自始至终不存在**，入口只有面板路由与状态灯，一次接线同时点亮两者、飞书侧零改动 |
| `content-concept-write-authority` | 内容 | 契约 + 路由已注册 + 客户端已建，**缺生产消费者** |
| `content-curated-write-authority` | 内容 | 同上 |
| `content-facebook-publish-media-authority` | 内容 | 契约已写，**路由未注册、未接线** |
| `content-token-usage-authority` | 内容 | 契约已写，**路由未注册、未接线**；端口是「提交已合并的增量」而非逐条上报，**属主今天没有这个方法** |
| `content-textcard-transcription-authority` | 内容 | 能力二态端口已写，未接线 |
| `content-role-factories` | 内容 | 待岔口 B 落地（tasks 2.5） |
| `content-generic-llm-authority` | 内容 | 待岔口 A 落地（tasks 2.5） |
| `content-reply-generation-authority` | 内容 | 未开工（tasks 2.6） |
| `content-publish-rejection-evidence-authority` | 内容 | 未开工（tasks 2.9）。**这条曾经无人承接**，核验时才发现——「tasks.md 全做完」不等于「门能清零」 |
| `automation-production-runtime-composition-unwired` | 组装 | 就是那个空壳入口本身；前两组不清完写不了 |

**顺序是硬的**：指令组 + 内容组不清完，组装那条写不了。第 3 段 0/6 不是拖延，是前置没到。

### 已撤的那一条（用户 2026-07-30 裁定）

`feishu-operator-publish-comment`：它两条证据指向的闭包**不可达**——`/publish`、`/comment` 永远走委托分支，
因为统一命令面把 `delegate` 声明成必填、组装根恒注入一个函数（缺服务时是函数**内部**抛，不是不给函数）；
面板那份动作面里也**没有** publish / comment。api 模式下这两条能力真正的失败走**委托通道**，
由 `feishu-operator-natural-language-delegate` 承接。**能力仍被覆盖，少的只是重复计数。**

契约（两个手动指令端口）刻意留着，理由写在 kernel 端口注释里；**MUST NOT 接线**——
接一条今天不执行的通道就是新增一处「看着接好了、其实永不触发」的假绿。
要接必须先重新裁定「这两条命令是否该绕开委托路径直发」。

---

## 4. ⚠️ 看着做完了、其实只做了一半的（先读这一节）

### 4.1 派生 api 仓的手写入口里有两处**已经写下的不诚实**，接线时别照抄

- `dispatchActive: () => false` —— 把「不知道」答成「停着」。而 1.4a 刚把这个字段改成可选，
  就是为了让它能**诚实缺席**。**建议直接省略不传**（类型上已允许）。
- 幂等键里塞了 `randomUUID()` —— 每次重试新随机一个，**幂等键形同虚设**。
- 都还没上生产（三进程在 dev 上没有 systemd 单元），但接线时照抄就会带进生产。
- 出处**分开的**：`delegated-task-channel-adjudication.md` §3 步骤 0-b 只点了随机数那处，
  状态灯那处在同一份文档的 **§5 第 K 条**。

### 4.2 新写传输三件套时照 `content-authority-http.ts` 办，**别照端口文档的字面意思办**

`concept-pool-port.ts` / `curated-selection-port.ts` 的文件头明写：传输适配层 **MUST** 先按码还原、
再重新抛出；**还原不出返回 `null` 时 MUST NOT 套默认原因**。只有 `content-authority-http.ts` 真做到了。

**「只写『不用原型判断』是不够的」这个坑，委托那一族已经关上了**（服务端把 `name` / `status`
放进传输错误附加位 + 客户端按 kernel 的补集判据还原），**内容那一族的新端口还得照着关**。

### 4.3 内容侧监听上还剩一处口径分裂

老的裸形态精选路由（无鉴权、无信封、无目标校验）与新的精选召回路由**同进程并存**。
路径不冲突，但同一个域两套鉴权口径。登记在 `CONTENT_AUTHORITY_WIRING_DEBT` 第 6 条。

### 4.4 派生仓的 `boundaries/*.json` 是**手抄件、不在同步范围内**（已咬两次）

- **第一次（静默）**：automation 那份 `ownership-rules.json` 与事实源差 **88 行**，且早就漏了两条裁定。
  为什么一直没人发现——平时跑的检查读的是**已生成**的产物，正好把窟窿盖住，只有跑「刷新归属」才当场抛。
- **第二次（响亮）**：2026-07-30 加新表时，三仓的 `table-ownership.json` 手抄件都停在 112 条，
  automation 的迁移属主检查当场红；`module-ownership.json` 缺 2 条，边界普查当场红。
- **这条区分影响 0.7c 的优先级判断，此前没记**：静默那种才是真危险。
- 结构问题没动（tasks 0.7c）：要么让同步脚本把这些纳入对账，要么让派生仓不再自持。
- **顺带**：`sync-split-repos` 对**迁移文件只报不改**，新迁移要手工拷进属主仓（对账会报「缺 1 条」）。

### 4.5 调度启停**刻意没有持久台账**——将来一定有人想「补齐四条一致」

它改的状态本身就是**进程内的一个布尔**。给它跨重启的台账，会让「重启后运营再点一次启动」被判成
`duplicate` 并回放一条陈旧的「是否真翻转」——**那是编造**。
4a 的既有判例逐字支持：`src/comm/edge-resume-command-receiver.ts` 明写「回执缓存刻意是进程内的，
因为它管的状态也是进程内的，本适配器 MUST NOT 暗示持久的恰好一次」。
理由已写进 `operator-command-receiver.ts`，并有一条用例（12）钉着「重启后 MUST 重新执行」。

### 4.6 `REQUIRED_SCHEMA_VERSION` 还停在 0097，是刻意的——接线那一批 MUST 一起处理

判据是那条常量自己的门槛（缺了它链路写不了），今天**不成立**：用台账的接收方还没接进任何进程。

**早抬的后果实测过链路，比「起不来」更难查**：schema 契约门是 `segAApiFoundation` 的**第一句**、
裸 `await`、刻意无 try/catch，跑在连接池与所有存储 `init()` 之前；enforce 下失败即抛 → 进程 exit 1 →
systemd 只有 `Restart=on-failure` / `RestartSec=5`、无 OnFailure、机器上无探针
⇒ **每 5 秒静默重启的崩溃循环，零告警**。且「behind」这一档**没有豁免通道**
（`pass`/`waived` 在该分支写死 false；`AIDCP_ALLOW_SCHEMA_AHEAD` 只管「库比代码新」那一档）。

**接线那一批 MUST 同时做三件**：抬 REQUIRED 到 0099、部署序列里在**重启之前**跑 `npm run migrate up`、
对 ol 也补同一步。

**补迁移只能用 `npm run migrate up`（或 `baseline`）**：`scripts/run-migration.ts` 执行 SQL 但
**不写 `schema_migrations` 账本**（其文件头明写这条缺口，且用户 2026-07-25 裁定有意保留它）。
用它补完，表在库里、门读的账本还停在旧版本 ⇒ 照样判 behind，现场看着「表明明建好了」，最费时间。

**另：新迁移的耦合单元是五处，不是四处**——迁移 + `KNOWN_MAX_SCHEMA_VERSION`
+ 该常量上方那段逐迁移追加的裁定 JSDoc + `table-ownership.json`
+ **`test/schema/sync-read-checkpoint-migration.test.ts` 里第二次写死的那个常量**
（一处从目录**算**最大版本、一处**逐字写死**；改完一处会以为完事了）。

### 4.7 那 13 条台账的派生器，自动化侧是**永久手写分叉、且零机械信号**

这条最阴，因为它**直接戳在「台账是机械派生所以诚实」这个主张上**。

两份同路径、同导出名的派生器（中控侧 1916 行 / 自动化侧 1792 行）：自动化那份首行带
`// aidcp:test-owner=derived`，而同步脚本把带这个标记的文件**从期望集与实际集里同时减掉**
⇒ **既不会被覆盖，也永远不会被报成漂移**。
后果：中控侧对探针做的所有改进**一条都到不了它**，而且**没有任何东西会提醒你**。
那 13 条是它算出来的——所以「机械派生」的成立程度，取决于这个分叉有多旧。

**接手动作**：动中控侧派生器时**当场决定**自动化那份要不要同改；不同改就在两份文件里都写明理由。

### 4.8 其余已登记的小项

- `0.3g` —— 标识符使用类探针不在接缝过滤范围内，实测 2/11 落在死分支；要处理需另行裁定（会真删证据行）。
- `0.3h` —— 另一个接缝过滤器仍是老式字符串正则，量词与新判据不同，混用会改变输出。
- `0.5g` —— 缺席的真正上游在角色调度器，刻意延后（理由在台账里）。
- `0.6i` —— 精选库不可用错误的守卫**刻意只按名字判、不要求原因码**：要求它会让守卫对「跑着旧版本的对面」恒 false。
- `0.6j` —— 已修：传输目录的规则描述曾把「必须有 SQL」写成准入条件（那只是第一批成员的形态）。
- `0.8g` —— **活缺口**：三进程形态下厂商密钥读必然失败，且被 `.catch(() => null)` 吞成「本来就没配」。
  api 侧手写 main 既没注册 `provider-secret/get-for-runtime`、也没注册 `role-model-selection/fetch`。

---

## 5. 下一步（顺序是硬的）

前置都齐了：契约（kernel）、传输三件套（两个文件）、接收方 + 幂等台账、19 条契约用例里的 17 条。
**下面是纯接线，对应 `delegated-task-channel-adjudication.md` §3 的步骤 3–6。**

### 第一步 · 步骤 3：把四组路由接到接收方与内部客户端

`operator-command-http.ts` 的四组注册函数与四个客户端类**都已写好，本步只用不改**。
挂在 automation 内部 API 注册块（`startAutomationInternalApi`）里，照它既有的
`if (…) { register… } else { console.warn(…) }` 形状：**每组独立注册、缺依赖走具名 warn，
不连带关闭其它组。** 委托 7 条一并挂上（它们已升到信封 + Bearer 形态）。

### 第二步 · 步骤 4：放宽取数聚合口的委托端口类型

`src/gateway/data-gateway.ts`（属 api，**不在热点清单**）：本地字段与 getter 的类型从 7 方法端口
放宽到 kernel 的 `DelegatedTaskCommandPort`（7+1）；`DataGatewayRemote` 那条闭包同步放宽。
**不新增第二个 getter、不新增第二条闭包。**
验收：typecheck 零错；默认（本地）分支行为逐位不变——getter 返回的仍是注入进去的那个对象本身。

### 第三步 · 步骤 5：组装根接线（`src/server.ts`，**热点，必须串行**）

**2026-07-30 这次集成已经撞过一次**（另一路 session 推了面板改动，rebase 后要在合并树上重跑全量才能合）。
务必等它让出来再动。顺序（每小步能单独编译过）：

1. 共享段构造本地接收方（包住既有服务实例）+ 台账实例。
2. 聚合口构造处：本地字段改喂接收方；`remote` 块新增委托闭包，用**指向 automation 的那个内部客户端与令牌**
   （`AIDCP_AUTOMATION_URL` / `AIDCP_AUTOMATION_INTERNAL_TOKEN`，组装根里已建好一个），
   **不要复用 content 那个 base URL**（那个是指向 content 的）。
3. **四个接线点全改指聚合口，一个不留**：飞书自由文本闭包、飞书入站 deps、
   客户端 API 发布队列视图（`if (!delegatedTaskService) return null` 那处——不改的话
   「问不到」会被渲染成「这个账号没有发布队列」，静默假成功）；面板与客户端 API 主接线已在聚合口上、零改动。
4. 飞书自由文本那段按回执形状重写渲染分支：`rejected` → 还原成业务错误走既有提示（行为逐位不变）；
   `not_delivered` → **明说「这台机器上没有接这条指令的处理器」**，MUST NOT 表述成已受理 / 已排队；
   传输失败 → 明说结果未知。（**异常分流那一半已经做了**，剩下的是把三种回执形状接上去。）

验收：单体形态下部署 dev，飞书 `/delegate`、面板启停与状态灯、面板与客户端 API 的委托任务全套
**行为逐位不变**；重启后错误行数 0；具名的「未接线」告警一条不响（dev 上全都接着线，本来就不该响）。

### 第四步 · 第 2 段剩下的 9 条（内容侧）

- 先落两个岔口的裁决（tasks 2.5：模型调用出口、四个角色工厂）。
- 发帖素材 + 用量记账两组：契约已在，**注册路由 + automation 侧接线**。
  用量那条注意端口是「提交已合并的增量」，属主今天**没有**这个方法——接线时补方法或交适配对象（与精选库那条同形）。
- tasks 2.7 的传递性检查：**特别点名 optional 参数**，那是静默缺席的主要来源。
- tasks 2.9（驳回证据授权）：先坐实现状（属主是谁 / 判定读什么 / automation 侧调用点在哪，带 `文件:行`），
  再决定补端口面还是**明写它由另一个 change 承接**——两条都行，**不能留空**。

### 第五步 · 第 3 段：自动化真入口

组装根骨架已相当完整（属主池、接口客户端、指令接收方、同步读镜像、内部服务端都在），
缺的是 `main()` 与就绪闸。**就绪闸照接口仓那份的形状办**（design.md §4 有模板：
监听先起、业务入口靠标志位 + 去重 promise、定时器 unref）。

### 第六步 · 第 4 段：清零 + 门禁

台账**三份**同批收缩（中控侧派生器 / 自动化侧常量 / 自动化侧 JSON）→ 入口从 fail-closed 切真启动
→ `boundaries:refresh` 逐条对账 → acceptance 红线全过。
**切换本身要有测试证明「台账非空时仍然拒绝启动」这条闸没被删掉。**

### 第七步 · 第 5 段：收尾

六仓对账、dev 部署、真机项登记 backlog、归档。

**⚠️ 「簇 60」在 `docs/real-machine-acceptance-backlog.md` 里出现两次，别登错**：
要登的是**文件头部 2026-07-26 那个说明块「簇 60『云端拆仓 Phase 0–4 的真机验收』」**；
文件里另有一个正式标题段 `## 簇 60 — 桌面客户端 mac 签名+公证包`，grep「簇 60」会**先撞它**。
（该文件当前最大簇号是 121。）

### 然后才是**批次 5**（不在本 change 内）

**三个进程在 dev 上真跑起来。至今没开工。**
六次部署（`b66c022` → `9ae8e1d` → `1b36b74` → `93d339b` → `e790e47` → `843bac6`）**全是单体形态**，
只证明现网零回归，**一次都没证明三进程能跑，也不声称**。

---

## 6. 工作纪律（都是踩出来的，别重踩）

### 6.1 land 前**逐仓**扫 worktree 脏状态与落后

一个任务的改动可能落在**多个仓的 worktree** 里。曾经 cloud 那半提交了、automation 那半留在工作区没提交，
而 automation 的分支已经合进主干推出去了。**这种漏不会报错**——两份台账各自自洽、测试照绿，
只是自动化的欠账表里多留了一条不属于它的债，而两份台账**本来就允许不同**（问的是不同的问题），
所以没有任何机械手段会比对它们。

```bash
CH=split-cloud-automation-production-runtime      # 这行不是占位符，照抄可用
for r in aidcp-cloud aidcp-automation aidcp-api aidcp-content aidcp-kernel aidcp-transport; do
  d=../$r.wt/$CH; [ -d "$d" ] || continue
  printf "%-20s dirty=%-3s behind=%s\n" "$r.wt" \
    "$(git -C $d status --short | wc -l | tr -d ' ')" \
    "$(git -C $d rev-list --count HEAD..origin/master 2>/dev/null)"
done   # dirty 非空即停；behind 非 0 先 fetch + rebase
```

`behind` 也要查：直接在落后的 worktree 上开工 = **从过期基底重新派生**，而 §6.2 抬 pin 的链条
会按过期的 kernel / transport 头去算。

### 6.2 同步顺序：**先把 src 和测试全同步完，再抬 pin**

```bash
./scripts/sync-split-repos --apply --prune        # ① src（--prune 才删搬走的旧副本）
./scripts/sync-split-repos --apply --tests        # ② 测试（不删，「多出」要人工删）
# ③ 再按 kernel → transport → 三个业务仓 抬 pin
```

**为什么**：`--tests` 那趟**也会给 kernel 派测试文件**。若在三个业务仓 pin 抬完之后才跑它，
kernel 头一动，transport 与三个业务仓的 pin 全部作废，整条链重抬一遍。
`--prune` 与 `--tests` **互斥**（脚本硬拦，理由是派生私有测试必须显式保留）。
派生仓私有的测试要加 `// aidcp:test-owner=derived` 标记，否则会被判「多出」。

### 6.3 pin 是**派生事实**，漂了不报错

三个业务仓 + transport 的 kernel pin **MUST 恒等于** kernel master 头。
装到旧 sha **不报错、编译照过**，跑的却是过期契约。`sync-split-repos` 会对账，**每次都看一眼**。

**别把正常环境当坏环境**：`npm install` 加 `--userconfig /dev/null` 是「装不上时才用」，不是 MUST。
本机 `~/.npmrc` 把 `@types` 域指向内网 registry，历史上曾因此装不上（memory
`split-repos-npm-install-blocker`），但 2026-07-30 实测那个 registry 是通的。

**另一件容易误判成事故的事**：自动化仓**不消费** `aidcp-transport` 包，它自持 `src/transport/` 下 50 个文件，
其中 39 个与共享包重合（接口仓 / 内容仓走包引入，自动化仓走相对路径）。
**这是同步脚本的设计**——成员在归属清单里仍标自动化，只是同时复制进包供三家共用；
对账里那句「未 pin aidcp-transport」也是脚本自己的设计文案。
**不是** CLAUDE §8.4 点名的「复制成两份、两端路径悄悄对不上」那种事故。

### 6.4 别高估 typecheck（实测，两轮变异）

把整条路由注册删掉，typecheck **会**红——但红的是「入参解析器成了孤儿」这个副产物，
**一旦解析器被两条路由共用，这个信号就消失**。
而**真实的滑手形态**（注册时手写一遍路径、不用共享常量）**typecheck 完全绿**，只有测试当场红。
这就是「路径常量只能有一份」的全部理由。

### 6.5 变异实测要问「**哪条**用例抓住的」，不只问「会不会红」

这条在本 change 里已经咬过两次，两次同一形态：

- 「客户端给 HTTP 状态码补默认 400」→ **端到端那两条用例（409 / 422）照样绿**，
  因为那两条路径服务端确实带了字段、默认值没机会生效。真正抓住它的是一条还原判据的**单测**。
- 「接收方给业务错误补默认状态码」→ **16 条用例一条都没红**，同样因为所有桩都带了明确状态码。
  补了一条真会触发它的（跨进程业务错误是裸对象、没有状态码）才让它显形。

⇒ 若某条不变量只被一条不起眼的用例守着，**在注释里明写「别当冗余删掉」**，
否则那句理由只活在你脑子里，而删它的人看到的是全绿。

### 6.6 行号会漂，注释**只写符号名**

每一路都报告过行号漂移（最多差 65~71 行）。组装根尤其——并行 session 在写它的时候，
行号在你读的过程中就变了。**定位按符号名，行号只作导航并标 sha。**

⚠️ `delegated-task-channel-adjudication.md` **通篇是行号，且 pin 在 `aidcp-cloud@1b36b74`**
（不是本文的 843bac6）。解析前先 `git show 1b36b74:<path>`，或直接按符号名定位。

### 6.7 部署纪律

只从主 checkout 的默认分支目标提交 `git archive` 出干净快照部署，**绝不从 worktree 部署**。
安全序列：命名 target（`scripts/deploy-target dev --check`）→ 测试通过 → ECS 先备份
→ rsync（排除 `.env` / `node_modules` / `.git`）→〔**带迁移时多一步**：先 `migrate status`
确认待应用条数、再 `migrate up`〕→ 重启 → 健康检查 → 失败即回滚。
**绝不碰同机 isales**（四个独立服务）。**ol 必须用户明确要求且走发布分支。**

健康检查要点（都实测过）：`active running`；8787 + 面板 8090 + 客户鉴权 8091 在监听；
重启后错误行数 0；**三属主库各自 `select 1`**（物理拆库后没有单一连接串了，探一个不算）；
飞书长连接已建立；**上机器逐条确认新代码真的到了**，不靠「rsync 没报错」推断。

---

## 7. 文档索引

| 文档 | 用途 |
| --- | --- |
| 同目录 `tasks.md` | 任务台账（104 条 + 大量 `<!-- -->` 裁定记录）。**它不是「能否收工」的事实源**——那把尺是 §3 那 13 条 |
| 同目录 `design.md` | 三个岔口、就绪闸模板、Phase 0 勘察结论 |
| 同目录 `delegated-task-channel-adjudication.md` | 1.4d 裁定 + 落地步骤 + 19 条契约用例（每条注明「它红的时候在说什么」）。**⚠️ 行号 pin 在 `aidcp-cloud@1b36b74`，见 §6.6** |
| `docs/cloud-service-decomposition-proposal.md` §4.7 / §7.2.1 | **归属的唯一事实源** |
| `docs/cloud-cross-service-coupling-resolution.md` | 耦合处置执行清单 |
| `docs/cloud-composition-root-trisection.md` §0.0 | 组装根三等分进度卡 |
| `docs/cloud-split-next-session-handoff.md` §0.1/§0.2 | 拆仓项目整体交接（比本文范围更大） |
| `CLAUDE.md` §8 | 拆仓期间一律 OVERRIDE 的不变量（事实源 / 编辑纪律 / 消边判据 / 准入 / 红线形态） |

---

## 8. 一句人话

拆仓分两半：**把纠缠解开**、和**让第三个进程真能启动**。第一半早就做完了。

现在卡在第二半，卡点很明确——自动化那个进程欠的东西有一张 **13 条**的清单，
清单不清零就不能声称它能独立跑。**契约、传输、接收方、幂等台账现在都齐了，剩下的是接线。**

**但这句话要打两个折。**
一是那 13 条是一个**永久手写分叉**算出来的，它拿不到中控侧的任何机械信号（§4.7）——
「机械派生所以诚实」的成立程度取决于那个分叉有多旧。
二是**接手时最该警惕的不是「还没做的」，是「看着做完了、其实只做了一半的」（§4）。**
