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

> **批 C 落地（cloud，2026-07-15）**：在 cloud worktree `lease-strict-preemption` 上，先 rebase 批 A 到 origin/master（批 A commit 9f0194b→ea7eee5；协议往返断言因与 master 首作引导 AC-PROTO-14 撞名，抢占两条重编号为 **AC-PROTO-15/16**；edge 侧仍 14/15）。假成功修复链 cloud 半边（BLOCKER command-sequencer 分类 + 6.2 消费 + 7.1 + 7.2 + 7.3 + 7.5 + 9.1 + HOLE-13）+ 7.8 + 7.6 + 7.10 + 7.11 全落地并测；新增单一事实源 `src/comm/preemption.ts`（isPreemptionReason + CommandPreemptedError）。commit 7c0b7a7/d3221d2/0daf0bb/fae46d3。**7.7、7.9 与 7.10b/7.11d/windowRemainingMs 消费者延后**（见各条登记 + 下方「批 C 延后清单」）。**co-deploy 未做**：必与 edge `6d87e39` 同批部署（cloud 单独上会把 edge 已在回的 preempted 认下而不烧——安全方向，但 edge 的抢占能力尚未随 cloud 主动接线到位，仍以整批同部署为红线）。
>
> **对抗复核（wf_d2def24b，4 视角 find→逐条 verify）：2165 单测全绿仍揪出 2 HIGH+1 MED+2 LOW，已全修（commit 8ba60f4）**：① yield_timeout 曾被归 re-runnable preempted → 自动重投控制面故障 / 卡死写者最终提交则双发 → 改归 submitted_unconfirmed（页面状态未知、绝不重投）；② 委托执行器 commentResult 未认评论新增两态 → /comment --force 走 worker 重入重复评论 → 补 submitted_unknown / deferred 分支；③ 7.2 退避被 60s 兜底扫描击穿（草稿仍 pending+授权在被反复捞起）→ 达阈值**作废授权签名**；④ 7.3 暂停通知每轮重复 ping 运维 → dedup（进入暂停态只发一次）；⑤ windowRemainingMs 保留字段无消费者 → doc 如实标 + 延后。动手前另跑 7 路 read-only 锚点映射（wf_27cf5744）复核漂移。**cloud full 2165 / acceptance 54 / typecheck 0 全绿**。

- [x] 7.1 **发布第四种终局**：outcome 新增 `preempted`；被抢占＝保持待审（不写终态）、不计熔断、FB 素材归还、保留授权签名、事件驱动重投（schedulePreemptedRedispatch：重触发 dispatch 在租约队列上等抢占方释放，非 60s 盲投）。`failed` 不可逆已复核（publish-log-store 无 failed→pending）。HOLE-13「已开始」下移到提交点击真正下发前（onFirstSideEffect），此前零副作用意外失败走 !sequenceStarted 回待审 <!-- aidcp-cloud 7c0b7a7 -->
- [x] 7.2 **抢占计数 + 退避**：独立 consecutivePreemptions（按 recordId），达阈值（默认 3）→ 停自动重投 + 通知运营 preempted_exhausted（仍保持待审、绝不烧稿），与熔断 consecutiveSeqFails 解耦 <!-- aidcp-cloud 7c0b7a7 -->
- [x] 7.3 **边缘硬暂停闸**：runDispatch 下发前 isEdgePaused(edgeId)（server 接 ws-server pausedEdges）→ 暂停即零副作用回待审、保留授权（瞬态不作废）、不烧 failed+熔断、通知 edge_paused_requeued。**不**把 publish.command 加进 ws-server 下发豁免名单（那会把写命令推给验证码挡住的浏览器＝假成功红线） <!-- aidcp-cloud 7c0b7a7 -->
- [x] 7.4 `task_lease_mismatch` 接线：handler.ts **无需改**（原样透传 payload）；识别落在三消费点——command-sequencer 分类（result.error）、edge.post（reason）、role-dispatcher 7.8（reason），全经 `isPreemptionReason` 归抢占（命令到达时租约已不在＝提交前，安全归 preempted） <!-- aidcp-cloud 0daf0bb（+7c0b7a7 分类基座） -->
- [x] 7.5 **活跃租约中断通道**：EdgeTaskLeaseError 新增 window_busy（+windowRemainingMs）/yield_timeout 码；onReleased 补 challenger acquire 拒绝分支（window_busy 精确重排 / yield_timeout 不可恢复）+ 活跃租约被抢占中断回调 onActiveLeasePreempted → command-sequencer.preemptTask 就地 reject 在飞 publish.command（catch 按 CommandPreemptedError 归类、**绝不 unwind executePublishSequence**，防提交后被抢重投双发）。server 接线 <!-- aidcp-cloud 7c0b7a7 -->
- [x] 7.6 评论 edge.post 升三态（CommentPostResult：confirmed/submitted_unconfirmed/preempted/not_dispatched，修 HOLE-8 重复评论）；去重写入门改「提交已派发（confirmed∪submitted_unconfirmed）」；被抢占＝放弃本轮（不写去重、不重建、不换词重试）；两 outcome union + 两穷举结果卡开关 + 三 live 调用点全迁；isEdgeTaskAcquireFailure 补排除 yield_timeout（控制面故障不归 not_started 空转成环） <!-- aidcp-cloud 0daf0bb -->
- [ ] 7.7 **延后**（非假成功修复链必需，见顶部延后清单）：巡视租约被撤收敛 + 独占租约期空闲时钟停表。硬门＝共享 EdgeTaskLeaseClient→按账号 RoleDispatcher 的 taskId 路由 + 外来租约授予/释放的向调度器扇出（今天不存在）。缓解已在位：7.8 原因级短路 + 边缘 canExecute 门控使外来租约期裸浏览命令回 task_lease_mismatch 被短路；被抢巡视仍靠既有空闲看门狗（240s nudge / 1h kill）自然收敛。**onActiveLeasePreempted 已提供撤租信号，缺的只是路由**——落地时接此回调
- [x] 7.8 🔴 **原因级短路**：role-dispatcher action.completed 处理器**顶部**（在 pendingMigration/comment.done/like 重试/noRecoverScroll 名单之前）加 `ok:false && isPreemptionReason(reason)` → 不兜底滚动、不重试、不计失败与配额、不 emit comment.done，直接 return。co-deploy 于 edge §8.1 批 D 之前必落（本条已落，批 D 后即安全） <!-- aidcp-cloud d3221d2 -->
- [ ] 7.9 **延后**（非假成功修复链必需，见顶部延后清单）：FB 评论走租约。facebook-edge-steps 三命令补 taskId（协议 payload 已带 optional taskId、零协议改动）+ runFacebookTargetedTaskBody 把 search→open→submit 包进 withLease。较大结构改动、且「人审(≤90s)是否在租约内」有未决设计点。**风险性质**：不纳入＝有任何租约在跑时 FB 评论命令被边缘静默丢弃、云端干等超时（诚实失败非假成功，可重试；FB 评论与其它租约并发相对少见）。落地时按 XHS keep-open 同构接线
- [x] 7.10 验证码协助受理超时 20s→**45s**（具名常量 CAPTCHA_ASSIST_ACQUIRE_TIMEOUT_MS）。**7.10b 续租延后**：同一验证码事件多次提交今天回 task_busy 拒绝（已避免重复抢占，安全），改「续租而非拒绝」属 UX 增强、无 lease.renew 协议消息需设计，见延后清单 <!-- aidcp-cloud fae46d3 -->
- [x] 7.11 人工触发的加群把档位一路传下去（gear：manual→human/auto→automatic，经 triggerScheduled/joinSpecificGroup→runReal/runShadow/runAssignedJoin 传到四个 group_join acquire）。**7.11d 尾巴部分**：被抢占原因已经由 leaseFailureReason 包成 `lease_unavailable:<code>` 落 isNetworkTransient 白名单（window_busy 短退避重试）；yield_timeout 仍走此瞬态白名单（应排除、控制面故障不该无限退避重试）＝延后清单一条 <!-- aidcp-cloud fae46d3 -->

## 8. aidcp-edge — 静默丢弃收口

- [ ] 8.1 被抢占 / 被让位清掉的浏览、巡视、发布命令**一律补诚实回执**（`main.ts:862-867 / :1058-1063 / :1122-1127` 三处今天只打一行警告；`browse-session.ts:887-889` 让位直接清空队列）
- [ ] 8.2 **巡视必须合成终态回执**（照抄断连时那条模板）：这三条主命令**根本不发动作回执**（只发数据事件），抢占中止不补，云端巡视态永真 → 约 240s 后看门狗**杀整会话**。**这个失败模式在生产上真实发生过**

## 9. 优先级口径（✅ 用户已拍板 2026-07-14：人审通过的发布 = **自动档**）

- [x] 9.1 **今天的档位是按触发路径分的，不是按任务性质**：publish-dispatcher.ts:187 从 `opts?.humanApproval ? 'human':'automatic'` 硬定 `'automatic'`；humanApproval opt 保留（另驱动熔断解除 confirmHumanApproval，不再据此定档）。原 test「人工批准入口使用 human」改为断言 automatic <!-- aidcp-cloud 7c0b7a7 -->
  - **定案（用户 2026-07-14）**：**一切发布一律自动档**，不论触发路径（人审入口 / 兜底扫描 / 事件驱动重投）。理由：它是异步队列作业，批准完人就走了，没人在等回执
  - **人工档只留「运营在线等回执」的动作**：手动评论（`/comment`）、手动加群、客户端内审批的即时动作
  - **副作用（接受）**：手动评论会抢占发布——**这正是设计意图**，但发布被抢占＝整条序列重跑
  - 顺带消灭「同一篇稿因触发路径不同而档位不同」与「重投降级」两个反 aging 缺陷
  - 落点：发布派发处不再按触发路径给档位，硬定自动档；人工入口的档位提升只保留给上面三类在线动作

## 10. spec delta（控制仓 aidcp，`openspec validate lease-strict-preemption --strict` 通过）

- [x] 10.1 HOLE-5 修：MODIFIED#1 header「任务优先级严格生效…」与主 spec:62「任务优先级与同级 FIFO 可预测」不匹配（归档期才暴露、validate 掩盖）→ 补 `## RENAMED Requirements`(FROM/TO)，MODIFIED 内容在新名下生效。两条既有回归 Scenario 语义已在 delta 重定义 <!-- aidcp control-repo（见本次 tasks/spec 提交） -->
- [x] 10.2 四条 requirement：被抢占分档回执（第四终局）+ 被抢占执行流必须真正停止写页面（清场/页面写记账）+ 交接必须有界（有界让位与超时升级）+ **本次补齐**「通知巡视按窗口保护、其不可逆消费段不可被抢占」
- [x] 10.3 「安全取消点」定义已在 delta（MODIFIED#2 抢占浏览取消陈旧待执行命令而非排空队列）
- [x] 10.4 **本次补齐**新增 requirement「让位超时升级为控制面回收，且是人工动作而非自愈」——yield_timeout 通向「请运营重启浏览器客户端」，MUST NOT 自动重试/重投/归还额度

## 11. 测试

- [x] 11.1 让路 4 条（浮层 / 停留 / 世代号判据 / 交接有界）+ 既有 3 条边界断言继续绿 —— **90/90 pass**
- [x] 11.11 **第 4 节取消点 17 条**（`51d060e`）：逐字输入取消粒度 + 接管优先于死线 / 按下-松开原子性（press 抛错也补发 release、原异常不被覆盖）/ 轮询原语死循环护栏 + probe-first / 发布填写打字中途被接管（停在半途 + 清场 + `preempted_by_task`）/ **提交点击之后被接管 → 后置校验照跑到底、绝不改写成 preempted**（禁区）/ 图片下载段可取消 + **塞文件之后不可取消** / 云端选元素在飞时就地作废（毫秒级抛出、不等满 200s、零页面副作用）/ 引擎取消点恰好 2 处（execute→validate 之间零取消点）/ XHS 评论打字被接管 + 提交后禁区 / FB 评论打字被接管（清场 + 诚实回执，**不是** `handler_error`、不是零回执）/ **孤儿写者结束不得解除他人取消点武装**（已验证：换回旧实现即变红）
- [ ] 11.2 抢占矩阵：风控抢人工 ✓ / 人工抢系统 ✓ / 同档不抢 ✓ / 低档不抢高档 ✓
- [ ] 11.3 抢占发布不双写：系统恢复抢占一个正在逐字输入的发布 → 在系统恢复的第一次页面写之前，发布 MUST 已停止向控制端口派发任何输入
- [ ] 11.4 提交窗口内 MUST NOT 强杀 + MUST 立刻如实告知剩余预算（不让抢占者空等）
- [x] 11.5 分档回执（cloud 单元）：AC-PREEMPT-1（submitDispatched→submitted_unconfirmed）/ AC-PREEMPT-4（submitDispatched 压过抢占，提交后被抢仍 submitted_unconfirmed 不重投）/ AC-PREEMPT-2/3（提交前抢占→preempted）+ publish-dispatcher 7.1（preempted 保持待审、保留授权、不计熔断）+ 评论 7.6（submitted→写去重、preempted→不写去重）<!-- aidcp-cloud 7c0b7a7 / 0daf0bb -->
- [~] 11.6 清场：**edge 侧已覆盖**（批 B 提交窗口/清场协议）；cloud 无关
- [~] 11.7 巡视窗口保护：**edge 侧已覆盖**（批 B 通知巡视窗口标志）；cloud 侧对应 7.7 延后
- [~] 11.8 参数一致性：cloud 验证码受理 45s > 最长提交窗口 20s（7.10 具名常量）；cloud acquire 预算 200s > edge quiesce（5.6 边缘侧对齐延后同 7.10 批坐实）
- [x] 11.9 协议往返断言（新原因字符串两端都是裸值，typecheck 抓不到）：edge AC-PROTO-14/15；**cloud rebase 后与 master 首作引导 AC-PROTO-14 撞名 → 重编号 AC-PROTO-15（原因串+windowRemainingMs）/16（submitDispatched）**。cloud full 2162 全绿 <!-- aidcp-edge 9bc6c6b 批 A / aidcp-cloud ea7eee5 rebase 后 -->
- [x] 11.CX **批 C 新增单测**：command-sequencer AC-PREEMPT-1..7（三态分档/submitDispatched 压过/preemptTask 就地 reject 不 unwind/零回归/onFirstSideEffect）、publish-dispatcher 7.1/7.2/7.3、role-dispatcher 7.8（四抢占原因不兜底滚动+对照 modal_timeout 零回归）、comment runner/edge-steps（submitted 写去重·preempted 不写去重）、join 7.11（human/automatic 档）<!-- aidcp-cloud 7c0b7a7 / d3221d2 / 0daf0bb / fae46d3 -->
- [ ] **批 A（协议地基）已落地** — 上述 6.1/6.2/6.3/6.4 + 11.9；inert 未接线，安全独立部署。
- [x] **批 B-2a/B-2b/B-2c/B-2d（edge 抢占激活 + 加固）已落地** — 5.1 六站提交窗口 + 5.10b 加群拆分 + 6.2 边缘置位（bc3e774，inert）→ 5.2/5.3/5.4/5.5/5.9 main.ts wire writers 激活 + 5.9 收紧 CHECK（b9fdfa5）→ 5.8 删遗留 onPublishCommand（9a9ebda）→ **对抗复核 `wf_1657e89b-85a` 加固**（6d87e39）。edge full 1363 / typecheck 0 / acceptance 21。**动 main.ts 发布 handler 区经用户 2026-07-15 明确批准（与 FB pacing 禁区结构隔离）**。
  - **对抗复核结论（5 视角 + 逐条对抗验证，1359 单测全绿仍揪出）**：2 BLOCKER + 1 MEDIUM 已修（6d87e39）——① FB 发帖双发（submit 全程无取消点，窗口前抢占→点击照发+判 preempted 可重投）：submit 接 TakeoverCtx + enter 前同步 checkpoint + catch rethrowIfTakeover；② 加群点击前 observe 无取消点（30s 不可中断→超 quiesce→浏览冻结）：observeUntilReady 接 checkpoint 每轮检查 + enter 前 checkpoint；③ submitDispatched 时机（press 已发但 CDP 抛错→回执假→双发）：dispatchClick 加 onPressDispatched 回调 + catch 补带 submitDispatched。其余发现全部对抗验证驳回（join 动作名有云端归一表、两 Map 去同步不可达、遗留 handler 已删、窗口预算 ~1s 尾巴 graceful 非双发）。
  - **🔴 co-deploy：edge 激活后会回 `preempted_by_task`，云端 command-sequencer 当前烧成 failed → 绝不单独部署，必与批 C（cloud）同批。假成功修复链 = 5.2+5.3+5.9+6.2+command-sequencer 分类，整批同部署**。剩余：5.6（延后与 cloud 7.10 同批）、批 C（cloud，含 command-sequencer BLOCKER + 7.x）、批 E 收口。
- [~] 11.10 `test:acceptance` → 全量 `test` → `typecheck`：**cloud 侧全绿**（acceptance 54 / full 2162 / typecheck 0，2026-07-15）；edge 侧批 B 已跑（full 1363 / acceptance 21 / typecheck 0）。co-deploy 前最终并线再各跑一轮

## 12. 真机验收（dev；**已登记 `docs/real-machine-acceptance-backlog.md` 簇 85**，co-deploy 后跑）

> 12.1–12.8 已归并入 backlog 簇 85（85.1–85.7，B/F 合验、D/E 合验）。硬前置＝edge `6d87e39` + cloud 批 C co-deploy dev。

- [ ] 12.1 **A（10 秒，决定可抢占段是否免费）**：小红书发布页上传一张图后，读预览区缩略图地址前缀。指向本机临时对象＝提交前零副作用；指向平台服务器＝抢占会留孤儿图、**必须写进 spec 显式承认**
- [ ] 12.2 **B（决定清场协议的形状）**：在已填标题正文的小红书发布页、已填正文并附图的 FB 发帖弹层上直接导航离开 → 是否弹「离开此页 / 保存草稿 / 丢弃帖子」确认框。**若弹且无人接管，页面会被冻住 → 抢占者反而拿到一个锁死的浏览器**
- [ ] 12.3 **C（决定巡视有没有可抢占段）**：导航进通知页、**不点任何分类栏目**、立刻离开再回来 → 三个分类角标是否还在。消失＝导航本身已消费未读，**可抢占段为空**
- [ ] 12.4 **D**：抢占一次「已填标题正文、已传图」的小红书发布后，刷创作首页看**草稿箱是否多出一条**
- [ ] 12.5 **E（低危，顺带）**：抢占一次带新建话题的发布后，去平台搜该话题看是否已建出实体
- [ ] 12.6 **F（端到端）**：发布跑到逐字输入中途 → 运营提交验证码点击 → 断言：停手 ≤2s、编辑器被清空、发布稿回待审且**未被烧成失败**、验证码点击**落在验证码上而不是发布编辑页**、抢占方释放后发布自动重投整条序列
- [ ] 12.7 **G**：FB 评论走租约之后，租约在跑时下发的 FB 评论命令**不再被静默丢弃**（今天会）
- [ ] 12.8 **H（逃生梯）**：人为让一个页面写者收到取消后不停手 → 断言协调器判为控制面故障、整队诚实拒绝，运营看到的是「浏览器不听话，请重启客户端」，而不是 20 秒后一句神秘的租约失败

## 13. 收口

- [x] 13.1 `openspec validate lease-strict-preemption --strict` **通过**（含 HOLE-5 RENAMED 修复后）
- [ ] 13.2 真机项归并入 backlog（本次已把 12.1–12.8 登记进 `docs/real-machine-acceptance-backlog.md` 抢占簇）
- [ ] 13.3 **co-deploy dev**：cloud 批 C（本 worktree 4 提交，HEAD 待定）**必与 edge `6d87e39` 同批**部署，绝不 cloud/edge 单独上。走 CLAUDE.md §5 安全序列。**cloud 分支 push 需 force**（批 A 已 rebase 到 master，origin/lease-strict-preemption 从 9f0194b→本 HEAD 为非 ff）——按 §6 需先与用户确认
- [ ] 13.4 archive（co-deploy + dev 真机 F 验收后）

### 🔶 批 C 延后清单（landed 主体之外，非假成功修复链必需；落地时逐条销账）

1. **7.7 巡视租约撤销收敛 + 独占租约期空闲时钟停表**：需共享 lease-client → 按账号 dispatcher 的 taskId 路由 + 外来租约授予/释放向调度器扇出。缓解已在位（7.8 短路 + edge canExecute 门控 + 既有空闲看门狗兜底）。onActiveLeasePreempted 已备撤租信号。
2. **7.9 FB 评论走租约**：三命令补 taskId + runFacebookTargetedTaskBody 包 withLease；较大结构改动 + 「人审是否在租约内」未决。不做＝租约在跑时 FB 评论命令被静默丢弃、云端干等超时（诚实失败非假成功、可重试）。
3. **7.10b 同一验证码多次提交改续租**：今天回 task_busy 拒绝（已避免重复抢占，安全）；改续租＝UX 增强，无 lease.renew 协议消息需设计。
4. **7.11d yield_timeout 排除出加群瞬态重试白名单**：window_busy 已经瞬态短退避重试（对）；yield_timeout（控制面故障）今天也落该白名单会无限退避空转，应排除（同 comment 侧 isEdgeTaskAcquireFailure 已排除的处置）。
5. **5.6 边缘排队默认 45s vs 云端 200s 对齐**：edge-task-coordinator.ts 边缘侧改，延后与 7.10 同批坐实（两端受理预算一致，避免单改成不一致的表）。
6. **window_busy 精确重排消费者**（对抗复核 LOW-5）：EdgeTaskLeaseError.windowRemainingMs 已透传但无消费者——今天 window_busy 的 acquire 失败走各调用方既有「下一轮重触发 / 有界退避」（非空转），尚未实装「按剩余预算 setTimeout 精确重排」。字段 doc 已如实标为保留。落地时挑一个 challenger 调用方在此值上挂重排。

---

## 明确不做（第二批）

- **断点续传**：被抢占的发布**整条序列重跑**（重传全部配图、重打全文）。抢占计数 + 退避（7.2）是防止它变成无限重跑的唯一护栏
- **通知条目增量回传**（每滚一屏就报，把损失窗口收缩到一屏）
- **被抢占的按需评论重建上下文**：重搜重开**已被真机实证会失败**，持锁保正确性正是当初的设计动机。被抢占＝放弃本次，运营需重敲一次
- **排队饿死的归因修正**（云端把「排在别人后面」上报成「请检查浏览器/CDP」）：单独立项 `lease-busy-attribution`
