# 交接 · change `split-cloud-automation-production-runtime`

> 生成于 **2026-07-30 01:00**，pin 在 `aidcp-cloud@93d339b`。
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

**2026-07-30 01:00 实测期望值：**

```
aidcp=40df0e91(main) cloud=93d339b api=d9c60cf automation=17c7712
content=6ffa70b kernel=3e80194 transport=cbb91b7   （六仓 master，全部已推送、工作区干净）

AC-BOUND metrics {"sourceFiles":531,"ownershipEntries":531,"crossBoundaryEdges":0,
                  "involvingContent":0,"exemptionEntries":0,"frozenTotal":0,"delta":0,"unplanned":0}
cloud 台账 55 条   automation 台账 14 条
tasks.md 46/97   （96 → 97：核验时补了 2.9，见 §3 ②）
```

`crossBoundaryEdges` **不是 0** ⇒ 有人新增了跨服务耦合，先查清楚再往下走（棘轮只许下降）。

**对账输出里这四类是预期噪声，不是回归**（省下一次误排查）：
① 「组装根不同 2」会打印**三次**（每个业务仓一次，共 6 条 `⊘`）——组装根按设计从不同步；
② 自动化仓另有一条 `⊙ src/automation-composition-root.ts（派生仓私有组装根，只登记不覆盖）`；
③ 输出头部的「迁移残留 13 条」；
④ 因此末行**必然**是「存在差异。」——那句话在当前设计下永远会出现。

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

| 段 | 完成 | 内容 |
| --- | --- | --- |
| 0. 准入与三个岔口裁决 | **37/58** | 开工前把有争议的判断钉死 |
| 1. 四条运营指令通道 | **4/11** | 指令从接口侧送到自动化侧 |
| 2. 内容侧属主授权 | **4/10** | 自动化隔着进程用内容库 |
| 3. 自动化真启动入口 | **0/6** | ← 主交付物 |
| 4. 台账清零与门禁 | **0/5** | 清零 + 焊死不可倒退 |
| 5. 派生对账、验收、收尾 | **1/7** | 六仓对齐、部署、归档 |
| **合计** | **46/97** | |

**已部署 dev 四批**（都是**单体形态**）：`b66c022` → `9ae8e1d` → `1b36b74` → `93d339b`。
每批都走了安全序列（备份 → rsync → 重启 → 健康检查），四次都零错误、同机 isales 全程未碰。
**ol 一次没动**（用户没提线上）。

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

### 4.1 六处错误识别点：迁移做了，**跨进程仍然认不出来**

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

### 第一步 · 关掉 §4.1（最高优先，因为它让「已修」变成真的）

按 `delegated-task-channel-adjudication.md` §2.5 补传输层的字段还原。
**验收信号**：构造一个「经过传输编码再解码」的错误喂给守卫，能认出来；HTTP 状态不是补出来的默认值。

### 第二步 · 第 1 段接线（closes 四条台账）

按 `delegated-task-channel-adjudication.md` §3 的六步走，**步骤 0 那两个前置缺陷必须先修**：
分号批的分隔符撞车、手动发帖/评论拿不到稳定键。
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
