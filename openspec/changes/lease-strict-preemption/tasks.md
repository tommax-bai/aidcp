# tasks — lease-strict-preemption

> **串行标记（热点文件）**：本 change 要改**两份 `protocol.ts`**（租约释放原因新增 3 个值 + 发布结果新增「已派发提交」位）+ `aidcp-edge/src/execution/edge-task-coordinator.ts`（写者注册表 + 抢占）+ `aidcp-edge/src/main.ts`（发布写者注册 + 删遗留处理器 + 静默丢弃补回执）+ **`aidcp-cloud/src/publish-agent/command-sequencer.ts`**（🔴 设计评审新点名的 BLOCKER 落点，见下）。按 CLAUDE.md §2 必须四处同步，且**不与他人并行**。
> **占用中的文件，本 change 不碰**：`aidcp-edge/src/main.ts` 的 FB 租约闸节奏豁免段——**⚠️ 设计评审实测：该段在本 worktree/master/全部分支里目前根本不存在，是用户未提交的并行工作**（唯一同型存在物是 XHS 的 pacing 穿透 `main.ts:1145`）。§8.1 要补回执的 FB 两处（定向评论 879-884、浏览 1075-1080）**就是禁区本身**，不是相邻——必须排在用户 FB pacing 豁免落地/合并之后、按内容特征定位、动前与用户协调。
> **取证来源**：workflow `wf_66958524-d70`（初次取证 5 路 + 3 视角对抗）+ **`wf_18b37a11-416`（2026-07-15 抢占核心动手前复核：5 路重新坐实 + 3 视角对抗 + 总装配）**。全部结论带 `文件:行`。**复核产物**：`handoff-section-5-preemption-core.md`（接手主文档：fleet 闸已清证据 + 锚点漂移表 + holes + 分批序列）、`design-review-synthesis-wf18b37a11.md`（总装配方案原文）。

## 🔴 设计评审复核结论（2026-07-15，wf_18b37a11-416）——抢占核心动手前必读

- **Fleet 定序闸已清**：并行 change `browser-slot-scheduling` 对协调器/main.ts 的改动**已全部落进本分支地基**（其 edge 提交经 `merge-base --is-ancestor` 验证既在 master 也在本分叉点 `e30c211`；协调器内容哈希在 base/master/slot 三处全等 `b569764`；我落后 master 的 8 提交无一碰协调器/main.ts；edge 仓无 browser-slot 活跃 worktree）。§5 原「等 slot 落定」的推进边界**解除**，可独占实装。
- **🔴 BLOCKER（tasks 从没点名的层）**：被抢占的发布在边缘一律以普通命令结果 `ok:false` 浮现（edge `main.ts:780/758/744` 三条出口），云端 `command-sequencer.ts:238/258` 把任何核心步 `ok:false` 归 `failed_before_submit` → `publish-dispatcher.ts:380` 写**不可逆 failed + 熔断**。**即便 §5+6+7 按原锚点全落地，被抢占的发布仍被烧成 failed**——§7「被抢占≠失败」的核心目标不达成。**修法**：command-sequencer 的 `ok:false` 分支与 catch 识别抢占原因串 → 产出独立 `preempted` outcome、绝不并入 failed_before_submit；publish-dispatcher `:380` 前加 `preempted` → 保持 pending 分支。列为本批必改热点，与 5.3/5.4/6.1/7.4 同批。
- **落地序焊死（P0-c，单边接线=烧稿）**：批 1 先落**协议**（6.x，inert 安全）→ 批 2 落 **cloud「认而不烧」**（7.x 大半是修今日既存烧稿，先落只让 cloud 更宽容）→ 批 3 **edge 真 emit + 协调器 + main.ts + cloud 主动抢占 co-deploy**（不可分单元，批 2 须已在生产）。§8 静默丢弃收口**绑进批 3**（8.1↔7.8 单边会净新增兜底滚动污染）。假成功修复链 = 5.2+5.3+5.9+6.2+7.1+**command-sequencer 分类**，必须一起部署。
- **6.2 置位语义**（评审新增红线）：「已派发提交」布尔位 MUST 在「按下事件真正发出那一刻」置真（XHS `publish-command-handlers.ts:942` 点击成功后、pollBounded 前；FB `publish-executor.ts:498` dispatchClick 后），center 查找类失败保持 false，**MUST NOT 复用 5.1 的提交窗口标志**（语义/时机相反）。6.4/11.9 往返断言范围要扩到「原因字符串 + 发布回执布尔位」。
- **锚点漂移**：tasks §5-8 行号写于早期基线、被 §1-4 下移（main.ts 早段+17/晚段+23、coordinator+5、通知巡视分类栏目严重漂到 3019/3068、cloud 目录多处缺 `src/publish-agent/`|`src/comment-agent/`、7.8 约错 120 行到 2269-2282）。**edge/cloud 一律以 handoff §5.3 的修正表为准，勿信 tasks 原行号。**

---

## 取证结论：核心假设活了一半，抢占成立但有硬前置

**活下来的一半**（代码坐实）：不可逆提交点**之前**确实不向平台写入——导航、开页、选栏目、填标题、填正文、评论输入，全程只有页面事件、页面内文本注入与页面内校验，**读不到任何向平台发起的写请求**。

**被证伪的三处**：
1. **通知巡视的不可逆点在开头，不在结尾**。点开分类栏目那一刻平台未读就被消费，而抓到的条目要十几秒后才回传。中间被抢占＝**一整波未读永久丢失**（未读只在「从无到有」翻转时上报一次，两端都无副本，无可回退游标）。→ 巡视**几乎没有可抢占段**，必须单独立规则。
2. **配图在点发布之前就已经交给平台了**。文件塞进上传控件后由页面脚本接管；缩略图指向本机还是平台服务器，代码读不出（**真机项 A**）。若指向平台，抢占「已传图未提交」的发布会在小红书留下**没人引用的孤儿图，且无回收手段**。
3. **「扔」不是零动作，是一个必须实现的清场协议**。小红书填字段**没有清空前置**、后置校验**只比对正文前 8 个字** → 抢占一旦允许中途中止，半截正文留在编辑器里，下一篇稿接着往后追加，8 字探针照样放行，**真发出一篇拼接的帖子**。离开脏编辑器页还可能触发平台的「离开此页/保存草稿」确认框，而我们**启用了页面域却没有任何对话框处理器** → 最高优先级的抢占者反而拿到一个**被冻住的浏览器**。

**两条今天就存在、抢占会立即踩爆的缺陷**：
- 浏览会话的阻断浮层等待**无上界**，且这段等待**被算进页面写占用** → 验证码一出现，让位永远等不到，而唯一能清掉验证码的正是被让位挡在门外的那个任务。**今天就是一个真死锁。**（→ 第 1 节，**已修**）
- **Facebook 的让位探针会撒谎**：它问的是「命令链空了没有」，而命令超时会在执行体**仍在写页面时**就放行命令链。它不是查不到，是主动回答「页面已静默」。（→ 第 2 节）

**结论**：发布**必须、也能够**在这一批覆盖，不需要「先粗暴中止、以后补回滚」的两步走——清场动作两个平台都已存在，缺的只是把它挂到「租约被撤走」上。**要如实认下的代价**：被抢占的发布**整条序列重跑**（重传图、重打正文）；小红书侧可能留孤儿配图；被抢占的按需评论**放弃本次**（连同 90 秒人审）。断点续传与通知条目增量回传属**第二批**。

---

## 1. aidcp-edge — 安全取消点与让路（解死锁）✅ 已完成

- [x] 1.1 接管取消令牌（接管世代号 + 检查抛出 + 专用异常类型）。**判据必须是世代号、不能是「浏览已冻结」标志**——交接一开始就置冻结、只在恢复时才清，独占任务自己的命令就跑在冻结期内；用标志作令牌，评论/巡视的每条命令要么当场自尽、要么跳过浮层闸对着验证码墙点击 <!-- aidcp-edge 0ae90c8 分支 lease-strict-preemption（未合 master；第 2–8 节完成后一并集成） -->
- [x] 1.2 阻断浮层等待加第三个出口（世代号已变）+ 换成可打断 sleep（`browse-session.ts:3145-3190`）。**抛出而非 return**——return 会让命令继续往下对着验证码墙点击
- [x] 1.3 两处停留 + 动作前统一闸同样接管可打断（`:512-548`、`:550-560`）。停留让路时**保留详情页锚点**（笔记确实还开着；清掉反而会让下次关闭跳过停留兜底、制造真秒退）
- [x] 1.4 主循环拍世代号 + 捕获接管 → 诚实回执 `preempted_by_task`、不记账、不重放。**不新建边缘侧动作名映射表**（CLAUDE.md §2 第 5 处漂移点）
- [x] 1.5 交接有界（复用已有的有界排空原语，预算 30s / `AIDCP_TASK_QUIESCE_MS`）+ 未收敛抛出 + **按世代号守卫回滚自己置的冻结标志**（不回滚＝把停摆从「让位态」搬到「浏览冻结态」，症状一样但更难查）
- [x] 1.6 协调器：交接抛错 → **不授予 + 诚实终结排队申请 + 解除浏览冻结 + 返回**。顺带修掉既有隐患「交接抛错却仍继续授予」（catch 只打日志随即照常 acquire ⇒ 在仍在写页面的孤儿动作之上授权）
- [x] 1.7 回归断言 4 条全绿（浮层让路 / 停留让路 / **世代号判据（写错了会比现状更糟的唯一一格）** / 交接有界不撒谎）；既有 3 条「真页面写在途时不许提前交接」继续绿

## 2. aidcp-edge — 让位探针不许撒谎（抢占的前提）✅ 已完成

- [x] 2.1 Facebook 会话：让位返回值改为基于**在飞写者计数**（与浏览会话的引用计数同形），不能来自命令链的 promise。计数**只在执行体真正 settle 时才减**——超时放行串行链不减。三处执行体全部记账：浏览命令 / 主页直读 / 评论加群委托 <!-- aidcp-edge c8e3202 分支 lease-strict-preemption -->
- [x] 2.2 命令超时放行串行链时登记**孤儿写者**；孤儿存在期间让位一律回「未静默、不可接管」。`quiesceForTask` 改为有界 + 诚实抛出（复用 `BrowseQuiesceTimeoutError`）
- [x] 2.3 **顺带修同一个洞的第二个出口**：冷待机 / 关浏览器前的排空（`waitDrained`）也只等串行链 → 会在孤儿写者仍在写页面时关掉浏览器。同步收紧
- [x] 2.4 **顺带把第 1 节的安全取消点补到 FB 侧**（否则「探针诚实」只会把双写换成「验证码协助永远拿不到锁」）：动作前犹豫 / 翻页前停留改可打断 sleep + 接管检查 → 零副作用作废、回诚实 `preempted_by_task`。判据同样是接管世代号
- [x] 2.5 会话注册处的两个 `quiesceForTask` 调用点加 catch（`main.ts:1069 / :1133`，**非** FB 租约闸 pacing 豁免段）：交接现在会诚实抛出，不能让它炸掉装配流程
- [x] 2.6 回归 3 条：孤儿在飞时交接 MUST 抛出（**修复前回 0＝谎话**）/ 停在犹豫上被接管秒收敛且零页面写 / 无在飞命令时照常收敛回 0 —— typecheck 通过、acceptance 19/19、全量 **1312/1312**

## 3. aidcp-edge — 清场协议（抢占的硬前置，不做就是把偶发雷改成常态雷）✅ 已完成

- [x] 3.1 **小红书填字段**：填写前先清空并回读确认为空（清不掉即诚实 `editor_not_clean`），填写后改为**全文比对 + 少量多余字符容差**（`FILL_EXTRA_CHAR_TOLERANCE=4`），**废掉 8 字探针**；失败路径统一走清场 + 诚实回报（脏页 / 页面已走两态分开）。移植 FB 侧已走通的做法 <!-- aidcp-edge bd9ffc0 分支 lease-strict-preemption -->
- [x] 3.2 **小红书评论**：输入前清空编辑器（同一个追加语义）；提交后未确认从 `state_unchanged` 改为 **`submitted_unconfirmed`**——提交动作**已经派发出去了**，谎报「未提交」会让上游重试 ⇒ 重复评论。（已核实：云端 `state_unchanged` 重试白名单只作用于 like/collect，不含 comment ⇒ 改名零回归；cloud 侧接线见 7.6）
- [x] 3.3 **FB 发帖**：放弃填写时除清空外**关闭发帖弹层**并回读确认（今天全仓没有）——清空 ≠ 让位，弹层还盖着，抢占者看不见底下的 feed / 验证码
- [x] 3.4 **离开确认框接管**：CDP 层订阅页面对话框事件并一律 accept（放弃编辑＝接受离开）。**`Page.enable` 开着却没有任何对话框处理器是今天就在的雷**（`cdp/session.ts` + `stealth-injector.ts` 都 enable 了）：离开脏编辑器页触发「离开此页？」→ 页面永久阻塞 → 最高优先级的抢占者反而拿到一个冻住的浏览器。**只在 attach 注册一次**（订阅表跨重连存活，放进重连路径会叠加监听器）。真机项 B 仍需证「FB / XHS 到底弹不弹」，但接管本身无条件正确
- [x] 3.5 **测试桩升级（否则整节无法断言）**：XHS 填字段的 CDP 桩过去对任何 `Runtime.evaluate` 恒回 `true`，验不出这条路径真正的语义（**输入是追加**）。换成真编辑器模型（insertText 追加 / 全选 + Backspace 才清空 / 回读返回真实文本）。新增 5 条断言：残文不拼接 / 清不掉诚实失败 / **只吃进前 8 字被抓出（旧探针恰好放行）** / 被塞脏字符 `field_polluted` / 评论清不掉 `editor_not_clean` —— typecheck 通过、acceptance 19/19、全量 **1317/1317**

## 4. aidcp-edge — 取消点补齐（不补，任何受理超时数字都是空的）✅ 已完成

> **本节的接线边界（重要，别误读成「抢占已可用」）**：**发布路径只铺管道、不注入取消信号**（`main.ts` 的 dispatch 调用点不传）。理由：协调器要到 5.4 才会抢占，此刻接上，信号唯一能翻真的时机是租约到期 / 断连——那会让本来能跑完的发布回一条云端**全仓不认识**的 `preempted_by_task` → 判 `failed_before_submit` → **不可逆 failed + 熔断 +1**。单边落地 = 净新增一条烧稿路径而抢占能力为零。接线属 **5.3 + 7.1 + 7.4** 同批。
> **⇒ 4.3 的「600 秒黑洞」本节一秒没少**，只是从此**可以**被打断；**12.6 F 的真机项要等 5.3 + 7.1**。
> **顺带纠正一个算错的数**：600s 站不住。云端挂起 → 选择器转 `llm_error` → 引擎**立刻升级上报、不进第 2 轮** ⇒「云端不回话」这一档的真实上界是 **1×200s**；600s 只在「每轮都在 200s 内成功回一个没匹配上」连着三轮才凑得齐。故引擎参数**一个值不改**（压到 20s 会把一次合法 thinking 选择误判成 `llm_error` ⇒ 烧稿）。

- [x] 4.1 **逐字输入**：守卫从「只认死线」扩成「死线 or 取消信号」，抛可区分的被抢占异常。新叶子模块 `src/execution/takeover.ts`（零 import）：`TaskTakeoverError`（从 browse-session 迁入、原地 re-export，instanceof 不破）+ `Checkpoint = () => void`（**抛异常、绝不返回 boolean**）+ `TakeoverCtx {checkpoint, signal?}`。`cdp-util` 三个 options 接口收口成 `InputSafetyOptions`，**接管优先于死线**（顺序写反 = 一次让路被报成 `fill_deadline_exceeded`）。六处调用点全接：FB 发布 / FB 评论正文 + 联系方式 / 搜索词 / XHS 评论正文 / XHS 发布的 `typeHumanized`（它不走 `dispatchKeystrokes`、有自己的分块循环）。打字中途取消**成对清场** <!-- aidcp-edge 51d060e 分支 lease-strict-preemption -->
- [x] 4.2 抽「有界 + 可取消」轮询原语 `src/flows/bounded-poll.ts`，替换 6 个手写循环 + 图片上传的第 7 个。**签名里故意没有取消入参**——6 个循环里 **5 个是禁区**（导航已提交 / 正文已打进去 / 发布按钮已点下 / 话题词已进正文 / 建议项已点），在那里取消 = 把一次可能已生效的写当成没发生 ⇒ 上游重投 ⇒ 发两遍。**参数不存在 = 编译器焊死禁区**。唯一可取消的选「上传图文」把取消点内联在自己的 `onMiss` 首行。双闸=墙钟+迭代帽（`ceil(timeout/interval)+2`），probe-first。**副作用**：6 个循环从裸 `setTimeout` 换成注入 sleep ⇒ 发布指令测试从 9.8s → **0.6s**
- [x] 4.3 云端选元素接取消：`ElementSelector.select` 加可选第 3 参（`{signal, timeoutMs}`）、`EdgeClient.request` 加可选 `signal`（**真删 pending + clearTimeout**——只 race 不删会把事件循环最长吊住 200s，那个计时器没有 unref）。选择器 catch 首行 `rethrowIfTakeover`：**吞成 `llm_error` 会让引擎回「已升级、模型不可用」——把一次让路谎报成一次失败，而这条路径的失败在云端是不可逆终态**。引擎取消点**恰好 2 处**（进守卫前 / 每轮重试边界）；`execute` 返回到 `validate` 返回之间**一格都不加**。`main.ts` 显式传 `{maxAttempts: 3, selectTimeoutMs: 200_000}`（**= 今天的默认值，行为不变**），把上界从「两处默认值意外相乘」变成写下来的一个数
- [x] 4.4 图片上传：下载段外部 signal 并进内部 AbortController（**被接管 ≠「图取不到」**——报成 `image_fetch_failed` 会让上游换图重试，那是一条假失败）。**塞文件之后不可取消**：页面 JS 已自行异步读 FileList 传给平台，取消其后的后置校验 = 把一张**可能已贴上的图**当成没贴 ⇒ 重传双写（→ 真机项 A）
- [x] 4.5 **（对抗评审坐实的真 bug，非计划内）** FB 会话的「当前命令世代号」是一个**共享标量**，而 FB **允许写者重叠**（命令超时放行串行链、执行体变成孤儿仍在写页面，下一条命令已开跑）。孤儿收尾时会把**正在跑的那条命令**的判据清成 null ⇒ 它的取消点**全部静默失效**：评论一路打完并按下回车，让位退化成「等满整条命令」、交接烧成 quiesce timeout。洞是第 2 节引入的，第 4 节是第一批真正依赖它的取消点。判据改为**按写者隔离**（`AsyncLocalStorage`，沿 await 链传播，重叠写者各看各的、谁也清不掉谁）。回归断言已验证有牙：换回旧的共享标量实现即变红
- [x] 4.6 门禁：typecheck 通过 / `test:acceptance` **19/19** / 全量 **1334**（基线 1317 + 17 条新断言）。评审 10 条发现 → 驳回 9、坐实 1（即 4.5）

### 🔴 本节发现、必须在第 5/6/7 节修的既有假成功（登记，勿遗忘）

- **发布提交的后置校验把「已离开发布页」当成发布成功**（`publish-command-handlers.ts` 的 `CHECK` 里 `|| !location.href.includes('/publish/publish')`）。抢占方会在这 15s 窗口内替我们把页面导航走（租约到期 → 协调器 `resumeBrowseIfIdle` → 浏览恢复导航），于是一篇**可能根本没发出去**的稿被记成 `ok:true`。**本节不修**（半修更糟：报 `post_validate_failed` 会把稿烧成不可逆 failed）。正确修法 = **5.2 + 5.3**（发布登记为页面写者，有在途发布写时协调器不得导航）+ **6.2**（「已派发提交」回执位）+ **7.1**（云端第四终局）。**钩子必须卡在 `resumeBrowseIfIdle`，不是只卡 `quiesceForTask`**——队列为空时 drain 根本走不到 quiesce。
  - 新增测试**刻意不给它背书**：submit 用例的桩只用成功文案作证据，URL 全程钉在发布页。
  - **同型镜像**：图片上传的 `verifyAttached` 被导航污染 → 报一条干净的 `image_not_attached`（**假失败**）→ 云端重传 → 同一张图贴两遍。同一个修法覆盖。
- **有意不覆盖**（别当漏改）：验证码轨迹回放（运营正在手动解题，给它加取消点 = 在运营正解的题上留一个按住不放的左键）；FB 加群（`onJoin` 不收 checkpoint）；`facebook/publish-executor.ts` 的 `waitUntil`（第 8 个纯墙钟循环，无迭代帽）——后两者登记为第 5 节顺手项。

## 5. aidcp-edge — 提交窗口标志 + 页面写者注册表 + 抢占

> **推进边界（2026-07-15 更新，fleet 闸已清）**：原「等 `browser-slot-scheduling` 落定再动协调器」的定序**已解除**——实测其协调器/main.ts 改动已全部落进本分支地基、逐字节等同 master、edge 仓无活跃 slot worktree（证据见上「设计评审复核结论」与 `handoff-section-5-preemption-core.md §3`）。**已先行落地**：**5.7**（验证码回放前复检）+ **5.10(a)**（`waitUntil` 迭代帽），见 `aidcp-edge 35d3aec`。**抢占核心可动手**：动手前设计对抗评审（`wf_18b37a11-416`）已完成、结论见上及两份复核产物；**rebase 推迟到最终集成**（本 base ↔ master 在协调器/main.ts/protocol 逐字节相同，评审直接以本 HEAD 35d3aec 为准坐实；冲突面仅 `browse-session.ts`/`facebook-session.ts` 两文件+测试，留最终并线一次解）。按 handoff §6 分批序列开工；**动 main.ts 前先与用户协调**（禁区=用户未提交工作）。

- [x] 5.1 **提交窗口守卫（六处）**：进入不可逆动作**之前** `enter(budgetMs)`、拿到确认或预算耗尽后 `dispose()`。协调器只在窗口关闭时才允许抢占（窗口内回 window_busy + 剩余预算）。叶子模块 `CommitWindowGuard`（时基兜底自动过期 + 世代守卫）<!-- aidcp-edge a062cbd（叶子）/ bc3e774（六站接线）分支 lease-strict-preemption -->
  - XHS 发布提交 `publish-command-handlers.ts` runSubmit（窗口 15s，pacing/bare 两分支各 enter）
  - FB 发布提交 `facebook/publish-executor.ts` submit（20s，与 XHS 共用 publishGuard）
  - XHS 评论提交 `browse-session.ts` executeComment（4s，最短）
  - FB 评论回车 `facebook/comment-executor.ts` submitComment（20s，最长 ⇒ **统一上界取它**；确认段 try/finally dispose）
  - FB 加群点击 `facebook/join-executor.ts` joinGroup（**收窄至短确认 18.5s** + 5.10b 可中断尾巴）
  - 通知巡视分类栏目 `browse-session.ts` browseNotificationComments/viewNotificationCategory（20s，**无回滚 ⇒ 窗口 MUST 覆盖点击**，finally dispose 防 no_target 早退泄漏）
  - **6.2 同站落地**：submit 回执携 submitDispatched（点击真正发出那一刻置真，center 查找/no_target 保持假）；测试三态 + 5.9 CHECK 串无 URL 判据
- [x] 5.2 **页面写者注册表**：协调器单一浏览闸泛化成注册表探针，每个写者提供 `取消 / 有界让位 / 是否在提交窗口` 能力 <!-- aidcp-edge 52d2a78 B-1 协调器侧 EdgeTaskPageWriterProbe + 25 单测；b9fdfa5 B-2b main.ts wire writers（combineCommitWindows + publishInFlight + cancelPublish）激活 -->
- [x] 5.3 **发布执行流注册为第二个写者**——`main.ts` onPublishAtomCommand 的 dispatch 传 per-command TakeoverCtx（AbortController=接管世代令牌，局部不入单例字段）；inFlightPublishCancels 登记 abort+settled；writers.cancelPublish 遍历触发 abort + 有界等收敛、未收敛即抛。**用户 2026-07-15 明确批准动 main.ts 发布 handler 区（与 FB pacing 禁区结构隔离）** <!-- aidcp-edge b9fdfa5 分支 lease-strict-preemption -->
- [x] 5.3b **notifyPublishSettled 接线**（复核 finding C：此钩此前零调用者）：dispatch 收敛的 finally 调用 → 恢复浏览，否则 publishInFlight 闸让浏览在发布结束后永久冻结 <!-- aidcp-edge b9fdfa5 -->
- [x] 5.4 **抢占**：入队时若来者档位**严格高于**在跑者 → 触发取消 → 有界等停 → 授予。**同档不抢占**（FIFO，事实源＝申请到达时刻）。窗口占用时**立刻回「窗口占用中 + 剩余预算」**，不让抢占者空等 <!-- aidcp-edge 52d2a78 B-1 + 1f67249 加固：drainOrPreempt 三态 + cancel-before-declare（preemptedPending，对抗复核 wf_3a8e8996 BLOCKER）+ 27 单测；**b9fdfa5 B-2b wire 真 inCommitWindow → 抢占引擎激活**（此前 inWindow=undefined 休眠）。co-deploy 批 C 前不部署 -->
- [x] 5.5 **等停到期仍未停手 → 判控制面故障并整体升级回收**（不是永久失败，也不是死等）：写者收到取消仍不停手＝控制面故障，整队诚实拒绝、退出让位态、**绝不解除 browseBlocked**（复核 wf_3a8e8996 finding #1）。前提 4.x 已完成 <!-- aidcp-edge 52d2a78 B-1：quiesce 终态按结构判据分流——控制面丢失(canAcquire===false)→cdp_unhealthy（良性，cloud edge-task-lease-client:212 已识别）、写者不停手→yield_timeout（=请运营重启客户端，§10.4，cloud 7.5 才识别）；窗口豁免＝window_busy 早返回不进等停钟。b9fdfa5 B-2b：cancelPublish 有界等收敛、未收敛即抛，激活发布写者侧的这条判据 -->
- [x] 5.9 **（第 4 节登记）浏览恢复的导航必须让位于在途发布写**：钩子卡在 `resumeBrowseIfIdle`（**不是** `quiesceForTask`——队列空时 drain 直接 return）。「已离开发布页 ⇒ 判成功」假成功的根治点 <!-- aidcp-edge 52d2a78 B-1：resumeBrowseIfIdle/canExecute/blocksBrowse/hasActiveLease 认 publishInFlight + notifyPublishSettled 恢复（协调器侧+单测）；b9fdfa5 B-2b：wire 真 publishInFlight=inFlightPublishes.size>0 + 收紧假成功 CHECK（去 URL 判据、只认成功文案正证据）→ 闭环 -->
- [~] 5.10 **（第 4 节登记）顺手项**：
  - [x] (a) `facebook/publish-executor.ts` 的 `waitUntil`（第 8 个纯墙钟 `for(;;)`、旧无迭代帽 → 注入恒定 now 即死循环）已补双闸=墙钟 + 迭代帽 `ceil(timeout/interval)+2`，同 `flows/bounded-poll`；护栏语义已由 `bounded-poll.test.ts` 覆盖，按补测克制不重复造桩 <!-- aidcp-edge 35d3aec 分支 lease-strict-preemption -->
  - [x] (b) FB 加群接取消点（与 5.1 加群窗口同批原子交付）：joinGroup 加 `checkpoint?` 参数，点击后 46.5s 观察轮询拆成「短确认窗口 ≤18.5s（协调器不抢占）+ 可中断尾巴」；尾段每轮门控 `if (!commitWindow?.isOpen()) checkpoint?.()`（窗口内世代号未变→no-op）；被接管抛 TaskTakeoverError，joinGroup catch 加 rethrowIfTakeover 防降级成 nav_error → 冒泡到 comment-handler.handle catch 转 preempted_by_task。checkpoint 经 comment-handler.onJoin 接线（comment-only join-handler 路径无 quiesce 追踪、传 undefined 安全） <!-- aidcp-edge bc3e774 分支 lease-strict-preemption -->
- 附注：6.2 的边缘置位、5.9 收紧 CHECK 已随批 B-2a/B-2b 落地（见 5.1/5.9）。**5.6（边缘 45s 排队默认 vs 云端）延后与 cloud 批 C 7.10 同批坐实**（受理超时口径两端一起定，避免边缘单改成不一致的表）
- [ ] 5.6 边缘排队默认值与云端不一致（边缘 45s vs 云端 200s，`edge-task-coordinator.ts:58`）：改成同值，或对缺失该字段的申请**诚实拒绝**，别用不一致的表默默摘掉任务
- [x] 5.7 **验证码落点回放前强制复检**（`browse/captcha-assist.ts`）：回放前重新探阻断类型 + 读当前 URL。阻断已消失 → `not_blocked`（绝不在已无验证码的页面盲点）；阻断类型或 URL 变了 → `stale_snapshot` + 重抓帧让运营在新帧上重标；复检本身失败 → 诚实 `failed`。复用现有回执枚举、**零协议改动**。URL 仅比 origin+pathname（验证码 token 每刷新都变、纳入会误判）。**硬前置**——今天靠「租约拿不到」挡着（安全的失败）；抢占之后会变成「抢到了 → 在发布编辑页上按几分钟前的旧坐标盲点真实鼠标」（**不安全的成功**）。回归：回放前阻断消失 → not_blocked 且**零鼠标派发**；回放前 URL 变 → stale_snapshot + 重抓帧且**零鼠标派发** <!-- aidcp-edge 35d3aec 分支 lease-strict-preemption -->
- [x] 5.8 删除遗留的整页发布处理器 `client.onPublishCommand`（全程不过租约闸，云端已无发送方 publish.request）+ 三个孤立 import（publishPost/PublishResultPayload/buildPublishApprovalRequestId）；publishPost 函数与 edge-client API 保留（测试仍用） <!-- aidcp-edge 9a9ebda 批 B-2c -->

## 6. 协议（🔴 热点文件，两份逐字同改 + docs/protocol.md）

- [x] 6.1 租约释放原因新增 3 个值：**被抢占 `preempted_by_task` / 提交窗口占用中 `window_busy` / 让位超时 `yield_timeout`（控制面故障）**（`protocol.ts:1296` edge / `:1289` cloud）；`window_busy` 另附可选 `windowRemainingMs`（剩余预算，让 11.4「不让抢占者空等」可实装），两份 protocol.ts 改动区逐字一致 <!-- aidcp-edge 9bc6c6b / aidcp-cloud 9f0194b 批 A -->
- [x] 6.2 发布结果回执新增「**已派发提交动作**」布尔位 `submitDispatched`——今天「已点未确认」与「压根没点」回执面完全相同，云端一律判提交前失败 ⇒ **帖子可能已发出却被记成失败**（**置位语义=按下那一刻置真、center 查找类失败保持 false，属批 B/5.1+6.2 边缘侧接线，本条只落协议类型**） <!-- aidcp-edge 9bc6c6b / aidcp-cloud 9f0194b 批 A -->
- [x] 6.3 `docs/protocol.md` 同步：`edge.task.released`/`publish.command.result` 两表行 + 释放 JSONC 示例，**回填既有缺口 `browser_wake_failed`**（合计 9 原因值）；头部消息计数 76 **不变**（§6 不新增 MessageType） <!-- aidcp 098a394 批 A -->
- [x] 6.4 新增的原因字符串两端都是**裸值、typecheck 抓不到漂移** → 手写往返断言焊住：AC-PROTO-14（原因串 + `windowRemainingMs`）/ AC-PROTO-15（`submitDispatched` 有值/缺省两态），edge + cloud 两份 `protocol-contract.test.ts` 各一份、两端全绿 <!-- aidcp-edge 9bc6c6b / aidcp-cloud 9f0194b 批 A -->

## 7. aidcp-cloud — 失败语义（被抢占 ≠ 失败）

- [ ] 7.1 **发布第四种终局**（`publish-dispatcher.ts:331-343 / :380-409 / :99-142`）：被抢占＝**保持待审、不写失败终态、不计熔断、FB 素材走归还而非隔离、保留授权签名**，由抢占方释放后**事件驱动重投**（不能靠 60s 兜底扫描盲投——会 spin：每 60s 重投一次、每次排队到 200s 受理超时）
  - `failed` 是**不可逆终态**（`publish-log-store.ts` 无任何 failed→pending 回退路径）——写了就救不回来，人工再批也没用
  - 「已开始」标志**下移到首条业务命令真正下发之后**（今天在拿到租约瞬间就置真 ⇒ 零副作用失败被判终态失败 + 熔断 +1）
- [ ] 7.2 **抢占计数 + 退避**：「被抢占不计熔断」拆掉了系统里唯一那道（意外的）刹车，必须补上。达阈值（建议 3）→ 停止自动重投 + 通知运营
- [ ] 7.3 **边缘硬暂停闸**（`publish-dispatcher.ts:321-344`）：验证码期云端暂停向该 edge 下发一切页面命令，而发布命令**不在豁免名单** → 投递数 0 → 序列器立即 reject → **烧成 failed + 熔断 +1**。下发前加闸；投递数为零按零副作用回待审
- [ ] 7.4 边缘已回的 `task_lease_mismatch` **云端全仓零处理** → 被当普通业务失败、直接烧稿 + 熔断。接线
- [ ] 7.5 **活跃租约的中断通道**（`edge-task-lease-client.ts:210-244 / :173-189`）：收到被抢占/让位超时/排队超时的释放 → **立刻中断该任务的执行体**并抛可区分错误；新原因即时拒绝，不再空等自己的计时器
- [ ] 7.6 评论（`comment-scheduler.ts:1271-1290 / :1523-1525`）：被抢占**不得判「未开始」**；已过提交点按「已提交待确认」处置并写去重账本；被抢占的按需评论＝**放弃本次**（含 90s 人审），不重建、不本轮重试（重建已被真机实证会失败）
- [ ] 7.7 巡视（`role-dispatcher.ts:569-622`）：租约被撤 → 走既有失败出口收敛（解除软暂停、回 feed）。会话空闲时钟在独占租约期间**停表**
- [ ] 7.8 🔴 **「被抢占」必须作为原因级短路，插在兜底滚动抑制名单判断之前**（`role-dispatcher.ts:2149-2162`）——该名单按**动作名**匹配，开笔记 / 刷新 / 看主页**不在名单里**，一旦补上诚实回执就会立刻触发一次恢复滚动，**滚到抢占方的页面上**。不补滚、不重试、不清计数、不计互动失败与配额
- [ ] 7.9 **FB 评论走租约**（`comment-agent/facebook-edge-steps.ts` 三条命令全无任务标识）：不纳入，「覆盖全部独占任务」就是假话。且今天只要有任何租约在跑，云端下发的 FB 评论命令会在边缘被**静默丢弃**、云端干等到超时
- [ ] 7.10 验证码协助受理超时 20s → **45s**（`captcha-assist.ts:349-368`）：覆盖最长 20s 提交窗口 + 取消停手 + 让位 + 往返。同一验证码事件的多次提交改为**续租而非重复抢占**
- [ ] 7.11 被抢占原因补进加群的瞬态白名单；人工触发的加群把**档位一路传下去**（今天硬写成自动档 → 严格三档下运营手动敲的加群会被另一条人工任务抢掉）

## 8. aidcp-edge — 静默丢弃收口

- [ ] 8.1 被抢占 / 被让位清掉的浏览、巡视、发布命令**一律补诚实回执**（`main.ts:862-867 / :1058-1063 / :1122-1127` 三处今天只打一行警告；`browse-session.ts:887-889` 让位直接清空队列）
- [ ] 8.2 **巡视必须合成终态回执**（照抄断连时那条模板）：这三条主命令**根本不发动作回执**（只发数据事件），抢占中止不补，云端巡视态永真 → 约 240s 后看门狗**杀整会话**。**这个失败模式在生产上真实发生过**

## 9. 优先级口径（✅ 用户已拍板 2026-07-14：人审通过的发布 = **自动档**）

- [ ] 9.1 **今天的档位是按触发路径分的，不是按任务性质**：同一篇人审通过的稿，走人工入口＝人工档，走 60s 兜底扫描补投＝自动档 → **可抢/不可抢取决于它怎么被触发，且重投时档位反而降级**（教科书式的反 aging）
  - **定案（用户 2026-07-14）**：**一切发布一律自动档**，不论触发路径（人审入口 / 兜底扫描 / 事件驱动重投）。理由：它是异步队列作业，批准完人就走了，没人在等回执
  - **人工档只留「运营在线等回执」的动作**：手动评论（`/comment`）、手动加群、客户端内审批的即时动作
  - **副作用（接受）**：手动评论会抢占发布——**这正是设计意图**，但发布被抢占＝整条序列重跑
  - 顺带消灭「同一篇稿因触发路径不同而档位不同」与「重投降级」两个反 aging 缺陷
  - 落点：发布派发处不再按触发路径给档位，硬定自动档；人工入口的档位提升只保留给上面三类在线动作

## 10. spec delta

- [ ] 10.1 现行 spec **明文禁止本次要做的事**（「正在执行且已产生副作用的独占任务 MUST NOT 被强杀；高优先级只影响下一次授予顺序」）→ **必须改写而非新增**，且两条既有回归 Scenario 的语义要重新定义，否则归档时与主 spec 冲突
- [ ] 10.2 新增四条 requirement：**清场协议 / 有界让位与超时升级 / 被抢占的第四终局 / 通知巡视的窗口保护**
- [ ] 10.3 首次定义「**安全取消点**」（已在当前 delta 里）
- [ ] 10.4 写明：让位超时升级为控制面回收 → 通向的是「**请运营重启浏览器客户端**」这个**人工动作**，不是自动恢复。别让人以为系统会自愈

## 11. 测试

- [x] 11.1 让路 4 条（浮层 / 停留 / 世代号判据 / 交接有界）+ 既有 3 条边界断言继续绿 —— **90/90 pass**
- [x] 11.11 **第 4 节取消点 17 条**（`51d060e`）：逐字输入取消粒度 + 接管优先于死线 / 按下-松开原子性（press 抛错也补发 release、原异常不被覆盖）/ 轮询原语死循环护栏 + probe-first / 发布填写打字中途被接管（停在半途 + 清场 + `preempted_by_task`）/ **提交点击之后被接管 → 后置校验照跑到底、绝不改写成 preempted**（禁区）/ 图片下载段可取消 + **塞文件之后不可取消** / 云端选元素在飞时就地作废（毫秒级抛出、不等满 200s、零页面副作用）/ 引擎取消点恰好 2 处（execute→validate 之间零取消点）/ XHS 评论打字被接管 + 提交后禁区 / FB 评论打字被接管（清场 + 诚实回执，**不是** `handler_error`、不是零回执）/ **孤儿写者结束不得解除他人取消点武装**（已验证：换回旧实现即变红）
- [ ] 11.2 抢占矩阵：风控抢人工 ✓ / 人工抢系统 ✓ / 同档不抢 ✓ / 低档不抢高档 ✓
- [ ] 11.3 抢占发布不双写：系统恢复抢占一个正在逐字输入的发布 → 在系统恢复的第一次页面写之前，发布 MUST 已停止向控制端口派发任何输入
- [ ] 11.4 提交窗口内 MUST NOT 强杀 + MUST 立刻如实告知剩余预算（不让抢占者空等）
- [ ] 11.5 分档回执：提交前被抢 → 「未提交，已中止」+ 熔断不变；提交后被抢 → 「已提交，结果未知」+ **不自动重试**
- [ ] 11.6 清场：抢占一个填了正文的发布 → 编辑器被清空 → 重发时**正文不拼接**
- [ ] 11.7 巡视窗口保护：点分类栏目之后抢占 MUST 被拒（回「窗口占用中、剩余 ≤20s」）
- [ ] 11.8 参数一致性断言：云端受理预算 > 最长提交窗口 + 取消停手 + 让位 + 往返
- [x] 11.9 协议往返断言（新原因字符串两端都是裸值，typecheck 抓不到）：AC-PROTO-14/15 两端各一份，edge full 1338 / cloud full 2044 全绿 <!-- aidcp-edge 9bc6c6b / aidcp-cloud 9f0194b 批 A -->
- [ ] **批 A（协议地基）已落地** — 上述 6.1/6.2/6.3/6.4 + 11.9；inert 未接线，安全独立部署。
- [x] **批 B-2a/B-2b/B-2c/B-2d（edge 抢占激活 + 加固）已落地** — 5.1 六站提交窗口 + 5.10b 加群拆分 + 6.2 边缘置位（bc3e774，inert）→ 5.2/5.3/5.4/5.5/5.9 main.ts wire writers 激活 + 5.9 收紧 CHECK（b9fdfa5）→ 5.8 删遗留 onPublishCommand（9a9ebda）→ **对抗复核 `wf_1657e89b-85a` 加固**（6d87e39）。edge full 1363 / typecheck 0 / acceptance 21。**动 main.ts 发布 handler 区经用户 2026-07-15 明确批准（与 FB pacing 禁区结构隔离）**。
  - **对抗复核结论（5 视角 + 逐条对抗验证，1359 单测全绿仍揪出）**：2 BLOCKER + 1 MEDIUM 已修（6d87e39）——① FB 发帖双发（submit 全程无取消点，窗口前抢占→点击照发+判 preempted 可重投）：submit 接 TakeoverCtx + enter 前同步 checkpoint + catch rethrowIfTakeover；② 加群点击前 observe 无取消点（30s 不可中断→超 quiesce→浏览冻结）：observeUntilReady 接 checkpoint 每轮检查 + enter 前 checkpoint；③ submitDispatched 时机（press 已发但 CDP 抛错→回执假→双发）：dispatchClick 加 onPressDispatched 回调 + catch 补带 submitDispatched。其余发现全部对抗验证驳回（join 动作名有云端归一表、两 Map 去同步不可达、遗留 handler 已删、窗口预算 ~1s 尾巴 graceful 非双发）。
  - **🔴 co-deploy：edge 激活后会回 `preempted_by_task`，云端 command-sequencer 当前烧成 failed → 绝不单独部署，必与批 C（cloud）同批。假成功修复链 = 5.2+5.3+5.9+6.2+command-sequencer 分类，整批同部署**。剩余：5.6（延后与 cloud 7.10 同批）、批 C（cloud，含 command-sequencer BLOCKER + 7.x）、批 E 收口。
- [ ] 11.10 `test:acceptance` → 全量 `test` → `typecheck`，edge / cloud 两侧

## 12. 真机验收（dev；登记 `docs/real-machine-acceptance-backlog.md`）

- [ ] 12.1 **A（10 秒，决定可抢占段是否免费）**：小红书发布页上传一张图后，读预览区缩略图地址前缀。指向本机临时对象＝提交前零副作用；指向平台服务器＝抢占会留孤儿图、**必须写进 spec 显式承认**
- [ ] 12.2 **B（决定清场协议的形状）**：在已填标题正文的小红书发布页、已填正文并附图的 FB 发帖弹层上直接导航离开 → 是否弹「离开此页 / 保存草稿 / 丢弃帖子」确认框。**若弹且无人接管，页面会被冻住 → 抢占者反而拿到一个锁死的浏览器**
- [ ] 12.3 **C（决定巡视有没有可抢占段）**：导航进通知页、**不点任何分类栏目**、立刻离开再回来 → 三个分类角标是否还在。消失＝导航本身已消费未读，**可抢占段为空**
- [ ] 12.4 **D**：抢占一次「已填标题正文、已传图」的小红书发布后，刷创作首页看**草稿箱是否多出一条**
- [ ] 12.5 **E（低危，顺带）**：抢占一次带新建话题的发布后，去平台搜该话题看是否已建出实体
- [ ] 12.6 **F（端到端）**：发布跑到逐字输入中途 → 运营提交验证码点击 → 断言：停手 ≤2s、编辑器被清空、发布稿回待审且**未被烧成失败**、验证码点击**落在验证码上而不是发布编辑页**、抢占方释放后发布自动重投整条序列
- [ ] 12.7 **G**：FB 评论走租约之后，租约在跑时下发的 FB 评论命令**不再被静默丢弃**（今天会）
- [ ] 12.8 **H（逃生梯）**：人为让一个页面写者收到取消后不停手 → 断言协调器判为控制面故障、整队诚实拒绝，运营看到的是「浏览器不听话，请重启客户端」，而不是 20 秒后一句神秘的租约失败

## 13. 收口

- [ ] 13.1 `openspec validate lease-strict-preemption --strict`
- [ ] 13.2 真机项归并入 backlog
- [ ] 13.3 部署 dev（走 CLAUDE.md §5 安全序列）
- [ ] 13.4 archive

---

## 明确不做（第二批）

- **断点续传**：被抢占的发布**整条序列重跑**（重传全部配图、重打全文）。抢占计数 + 退避（7.2）是防止它变成无限重跑的唯一护栏
- **通知条目增量回传**（每滚一屏就报，把损失窗口收缩到一屏）
- **被抢占的按需评论重建上下文**：重搜重开**已被真机实证会失败**，持锁保正确性正是当初的设计动机。被抢占＝放弃本次，运营需重敲一次
- **排队饿死的归因修正**（云端把「排在别人后面」上报成「请检查浏览器/CDP」）：单独立项 `lease-busy-attribution`
