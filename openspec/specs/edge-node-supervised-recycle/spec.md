# edge-node-supervised-recycle Specification

## Purpose
TBD - created by archiving change edge-own-chrome-supervised-recycle. Update Purpose after archive.
## Requirements
### Requirement: 不可恢复终态 MUST 诚实下线并以可重起语义退出

边缘节点在 CDP 连接到达**不可恢复终态**(有界重连耗尽,或快判判定浏览器进程已死 / 页面 target 归零)时,MUST **主动诚实下线**:停止一切上报,并**干净关闭边-云连接**,使云端经其现成的掉线清理立即把该节点移出账号→节点路由目标。随后边缘 MUST 以「请重起」语义(非零退出码)退出进程,把恢复移交看护层。

边缘 MUST NOT 在终态时保持边-云连接开着空转(那会让云端在线判据窗口内仍把该节点算作在线并向已失去浏览器的节点派活,属静默假成功);MUST NOT 以「停止上报、被动等云端 idle 看门狗兜底」替代主动下线。

关闭边-云连接只是**发起**关闭握手,边缘退出 MUST 等连接真正关闭(`close` 事件)后再退,并对该等待设**有界上限**(到时仍未关闭则照常退出);MUST NOT 在发起关闭后**同步立即**退出,以免关闭帧未送达、云端短时仍当其在线。

#### Scenario: 终态 → 先诚实下线再退出,云端立即停止路由
- **WHEN** 边缘判定 CDP 连接不可恢复(进程级回收节点)
- **THEN** 边缘停止一切上报、关闭边-云连接、等待该连接真正关闭(有界上限内)后以可重起退出码退出
- **AND** 云端观察到的是干净关闭(非超时/RST),掉线清理即时生效、该节点不再被账号→节点路由选中

#### Scenario: MUST NOT 同步退出致关闭帧丢失
- **WHEN** 边缘发起关闭边-云连接
- **THEN** 边缘 MUST 在连接 `close` 事件到达或等待上限到时后才退出进程,MUST NOT 在发起关闭的同一步同步退出

### Requirement: 终态分类 MUST 区分进程级与页面级丢失并快判回收

CDP page-WS 意外关闭时,边缘 MUST 在**进入有界重连之前**先探测浏览器**进程级**端点以分类:
- 浏览器进程级端点不可达(端口拒连)→ 浏览器进程已死 = 终态,MUST 立即回收、跳过重连。
- 进程级端点可达但持续无可用页面 target → 浏览器活着但页面归零 = 终态(经实测此态基本不可恢复),MUST 立即回收,MUST NOT 在该病浏览器上磨满重连预算。
- 进程级端点可达且页面 target 复现 → 走既有有界重连透明续跑。

此快判 MUST 位于重连之前,使主导失败 case 不必先烧满重连总时长。

#### Scenario: 端口拒连 → 立即回收不等重连
- **WHEN** page-WS 关闭且浏览器进程级端点探测失败(端口拒连)
- **THEN** 边缘判定进程级终态、立即走回收路径,MUST NOT 先耗满有界重连总时长

#### Scenario: 进程在但页面归零 → 判终态回收
- **WHEN** 进程级端点可达但重发现持续找不到可用页面 target
- **THEN** 边缘判定终态并回收,MUST NOT 在页面归零的浏览器上磨满重连

### Requirement: 回收前 MUST 确认旧浏览器真死且端口与登录锁释放

进程级回收路径在退出前,MUST 真正终止本进程**自启并独占**的浏览器,并 MUST **确认其真死、调试端口与单例登录锁已释放**后再退出。确认 MUST 在**仍活着的本进程**上执行(对调试端口轮询探测到空),MUST NOT 仅凭终止信号的返回值即认定已死,MUST NOT 把该确认放到「已退出的旧进程」里(那样没有活着的执行者)。

若优雅终止信号在有界时间内未使浏览器退出,边缘 MUST 升级为强制终止,以保证端口与登录锁被释放 —— 否则重起的新进程会被单例登录锁的诚实拒启逻辑挡下、把重起预算白白烧光。

#### Scenario: 杀浏览器后确认端口真空再退
- **WHEN** 回收路径终止本进程独占的浏览器
- **THEN** 边缘轮询调试端口直至探测为空(优雅终止超时则升级强制终止),确认端口与登录锁释放后才退出进程

#### Scenario: 端口未释放即退出会导致重起自锁死(MUST 避免)
- **WHEN** 旧浏览器尚未真死、端口仍被占用
- **THEN** 边缘 MUST NOT 此时退出让看护重起(重起的新进程会被单例登录锁诚实拒启),MUST 先完成终止与端口释放确认

### Requirement: 看护进程 MUST 有界重起并对连续失败诚实放弃

看护进程(多节点启动器)观察到子节点以「请重起」语义退出时,MUST 按该节点的**固定槽位**(固定端口、固定登录目录、固定账号与节点标识)重新拉起,并 MUST 施加崩溃循环保护:**指数退避** + **连续失败计数上限**。计数 MUST 按「连续失败」累计、并仅在节点重新进入活跃且**健康存活达到最小时长**后清零(MUST NOT 用墙钟滑动窗口的重起次数作判据,因单轮失败可能耗时数分钟、滑动窗口永远凑不满而导致无限重起)。

连续失败达到上限时,看护进程 MUST **诚实放弃**该节点:打出可识别的「已放弃」日志、留该节点下线(MUST NOT 无限重起、MUST NOT 假装健康),且 MUST 不影响其余节点继续运行。

为压低单轮失败时长,重起子节点的登录等待 MUST 收紧到远小于冷启动人工登录的时长(headless 重起无人工登录可能,登录态本应已持久化、秒级命中,否则按崩溃快速计入预算)。

#### Scenario: 节点反复失败 → 退避重起到上限后诚实放弃
- **WHEN** 某节点连续以可重起码退出、达到连续失败上限
- **THEN** 看护进程停止重起该节点、打「已放弃」日志、留其下线,其余节点不受影响

#### Scenario: 节点恢复健康 → 失败计数清零
- **WHEN** 某节点重起后进入活跃并健康存活达到最小时长
- **THEN** 其连续失败计数清零,后续再失败重新从头计

### Requirement: 看护进程 MUST 将停止与重起信号送达执行体及其浏览器

看护进程拉起子节点的方式 MUST 保证停止/重起信号能**真正送达执行体进程**(而非只停在外壳 / 包装进程),使执行体的关机路径(终止其独占浏览器的唯一路径)必然运行。MUST NOT 留下孤儿执行体或孤儿浏览器霸占调试端口与登录锁(那会让后续重起被单例登录锁诚实拒启、全盘卡死)。

#### Scenario: 看护进程收到终止信号 → 零孤儿
- **WHEN** 看护进程收到终止信号并停止全部子节点
- **THEN** 不残留任何孤儿执行体进程、不残留任何孤儿浏览器进程,各节点调试端口与登录锁均被释放

### Requirement: 回收与真关机 MUST 退出码语义清晰且关机优先

边缘退出 MUST 用退出码区分意图:真关机(终止信号)= 不重起码,回收(终态)= 请重起码。当回收与真关机时序相撞时,看护进程 MUST 以「关机优先」处置:看护进程自身收到终止信号后,MUST **无条件抑制对任何子节点的重起**(无论子节点退出码),避免在操作者关机期间又把节点拉起。边缘侧 MUST 保证「真终态」即便有终止信号撞入也以请重起码退出,MUST NOT 把真终态掩成 clean exit。

#### Scenario: 操作者关机期间不误重起
- **WHEN** 看护进程收到终止信号、同时某子节点退出(任意退出码)
- **THEN** 看护进程抑制重起、走整体停止,MUST NOT 在关机期间重新拉起该节点

#### Scenario: 真终态不被信号掩成 clean exit
- **WHEN** 边缘已请求回收(真终态),随后终止信号撞入退出流程
- **THEN** 边缘以请求重起码退出,看护进程据此(在非关机态下)重起

### Requirement: 回收 MUST NOT 在真账号上造成半截或重复发布

进程级回收若发生在一次发布(对真实账号发帖)执行中途,边缘 MUST 先把该次发布**诚实判失败**(使审批/通知侧看到失败而非半成品)再退出;MUST NOT 静默丢弃在途发布而让其跨重起被重新触发,在真账号上造成**重复发帖**。发布链 MUST 保证「提交」是最后一个不可逆动作,使回收发生在提交前不会留下半张帖。

浏览侧在途互动在回收时 MUST 按既有约束如实回报失败、MUST NOT 在新会话握手后自动重放断连前的半截命令。

#### Scenario: 回收撞上在途发布 → 诚实判失败不重复发
- **WHEN** 进程级回收发生时有一次发布正在执行且尚未提交
- **THEN** 边缘把该次发布诚实判失败上报后再退出,新进程握手后 MUST NOT 自动重放该发布

#### Scenario: 提交为最后不可逆步
- **WHEN** 回收发生在发布的提交动作之前
- **THEN** 平台上不留半张帖(提交是发布链最后一个不可逆动作)

### Requirement: 复用模式与单机开发 MUST 只诚实退出不回收外部浏览器

节点以复用外部浏览器模式运行(显式开启复用开关)时,本进程并不拥有该浏览器,回收路径 MUST 按「是否复用」分支:复用模式下终态只做**诚实下线 + 退出**,MUST NOT 尝试终止 / 回收一个本进程不拥有的浏览器(对其终止是空操作,硬走回收会对外部浏览器空转或卡等端口释放)。单机裸跑无看护时,终态即诚实退出一次,由人工重起,行为与多节点一致。

回收能力节点 MUST 断言本进程**自启并独占**浏览器;若检测到复用开关泄漏到本应独占的节点,MUST 拒绝回收路径并诚实失败,MUST NOT 误把空操作终止当成已回收。

#### Scenario: 复用模式终态只退出不回收
- **WHEN** 复用外部浏览器的节点到达 CDP 终态
- **THEN** 边缘诚实下线并退出,MUST NOT 尝试终止外部浏览器

#### Scenario: 复用开关泄漏到独占节点 → 拒回收并诚实失败
- **WHEN** 一个本应独占浏览器的回收能力节点检测到复用开关被开启
- **THEN** 边缘拒绝走回收(终止将是空操作),诚实失败,MUST NOT 假装已回收

### Requirement: 多节点回收 MUST 互不影响且复用同一登录目录保活

每节点拥有独立端口、独立登录目录、独立浏览器进程;单个节点的回收 MUST **仅影响该节点**,MUST NOT 触碰兄弟节点的会话、浏览器或路由。看护进程重起一个节点 MUST 复用该节点**原本的登录目录**(登录态随目录持久化、重起即带过来,MUST NOT 清空目录致重新登录),并 MUST 按**固定槽位标识**重起(端口/目录/账号/节点标识),MUST NOT 因重起而落到兄弟节点的目录或端口上。

看护进程为各节点构造的环境 MUST 在启动时**快照固定**、重起时按固定槽位复用该快照,MUST NOT 在重起时重新展开看护进程的活动环境(以防复用开关等设置漂移泄漏,致重起的新进程去接管孤儿浏览器而破坏独占不变量)。

#### Scenario: 回收一个节点不影响兄弟节点
- **WHEN** 节点 i 进入回收并被重起
- **THEN** 节点 j(j≠i)的会话、浏览器与路由不受任何影响

#### Scenario: 重起复用同一登录目录、登录态保活
- **WHEN** 节点 i 被看护进程重起
- **THEN** 新进程复用节点 i 原登录目录、登录态命中,MUST NOT 清空目录或落到其它节点目录

#### Scenario: env 快照冻结防复用开关漂移
- **WHEN** 看护进程按固定槽位重起节点 i
- **THEN** 使用启动时冻结的该节点环境快照(复用开关保持关闭),MUST NOT 重新展开活动环境致设置漂移

### Requirement: 诚实下线 / 停手 MUST 真正终止进程，绝不留存活僵尸钉死事件循环

「诚实下线 / 停手 / 终态退出」路径 MUST **真正使进程终止**——这是对「不可恢复终态 MUST 诚实下线并以可重起语义退出」的强化落实：在置可重起退出码后，节点 MUST 主动释放一切会令事件循环保持存活的**常驻句柄**（至少含：与看护层之间的 IPC 通道、以及为浏览器停放 / 控制打开的 stdin 控制读取器），必要时显式断开 IPC / `process.exit`，MUST NOT 仅置退出码后 `return` 就当作已退出。

若进程带有此类常驻句柄而只 bare-return，进程会挂成**存活僵尸**（退出码已置但进程不退、其 CDP 可能已被关闭），后果链 MUST 被杜绝：① 看护层永远收不到子进程退出事件，其**有界重起与诚实放弃逻辑根本不触发**；② 外壳的手动「启动」因僵尸子进程句柄仍在而**空操作**（对操作者表现为「点了没反应」）；③ 操作者唯一的恢复手段退化为强制终止（重新登录 / 终止信号）或重启整个外壳。

故任何诚实停手路径 MUST 以「进程确已退出」为完成判据。系统 SHALL 有回归测试断言：带 IPC 通道与 stdin 控制读取器的核心，在停手 / 终态路径上**进程确实终止**（而非存活僵尸）。

#### Scenario: 身份确立失败停手 → 进程真正退出、看护层据退出码语义处置
- **WHEN** 核心在启动期身份确立最终失败（等待登录超时 / 中断下线）而走诚实停手
- **THEN** 核心关闭 IPC / stdin 等常驻句柄并**真正退出**，看护层收到子进程退出事件并按退出码语义处置（登录超时 / 早窗中断走**干净停止**码→不自动重起、待人工再触发；其它可重起终态→按固定槽位重起或达上限诚实放弃），外壳「启动」不因僵尸句柄而空操作

#### Scenario: 带常驻句柄的核心停手 → 收口关闭句柄再退
- **WHEN** 一个带 IPC 通道与 stdin 控制读取器的核心走任一诚实停手 / 终态路径
- **THEN** 收口 MUST 关闭这些句柄（或显式退出），使事件循环不被钉住、进程确实终止，MUST NOT 留存活僵尸

#### Scenario: 回归测试守住「不留僵尸」
- **WHEN** 对停手 / 终态退出路径做回归测试
- **THEN** 测试 MUST 断言在 IPC + stdin 常驻句柄存在的条件下进程终止（而非仍存活），使「置 exitCode 后 bare-return」的僵尸回归被 CI 挡下

### Requirement: 不可重起终局（同账号并发占用拒启）MUST 即刻诚实停止且不动他处浏览器

指纹浏览器提供商在启动被拒、且拒因表明「该分身已被同一账号在别处打开 / 不允许并发打开」时，看护进程 MUST 把此次退出识别为**不可重起终局**（重起不可能使其自愈），MUST **立即诚实停止**该节点、MUST NOT 将其计入有界重起预算做无谓退避重试。该识别 SHALL 独立于普通崩溃与缺内核可恢复态。

该终局处置 MUST NOT 对该分身的浏览器发起任何停止 / 强制终止 / 调试附着——因为占用者是同一账号在**别处的活跃会话**，动它会破坏他人会话并可能触发平台风控。此处「诚实停止」仅指停止本机对该节点的重起并如实呈现原因，绝非回收 / 关闭那个别处的浏览器。

系统 SHALL 提供护栏开关，可退回把该退出按普通崩溃重起的旧行为，供识别误伤时应急。

#### Scenario: 同账号并发占用拒启 → 即刻停止不重试
- **WHEN** 某节点启动时提供商因「分身已被同账号在别处打开、不允许并发打开」而拒启、进程随之退出
- **THEN** 看护进程识别为不可重起终局，立即停止该节点、不进退避重起、不消耗连续失败预算，并留其下线待操作者处置

#### Scenario: 不可重起终局 MUST NOT 关闭他处浏览器
- **WHEN** 处置该终局时
- **THEN** 看护进程 MUST NOT 对该分身发起停止 / 强杀 / 调试附着，占用它的别处活跃会话不受任何影响

#### Scenario: 护栏关闭时退回旧重起行为
- **WHEN** 护栏开关被关闭
- **THEN** 该退出按普通崩溃走既有有界重起路径（用于识别误伤时的应急回退）

### Requirement: 冷待机期间云连接不可恢复不得触发浏览器重启

When an edge core is already in browser cold standby, exhaustion of the cloud WebSocket reconnect budget SHALL NOT be treated as an ordinary recoverable terminal failure that exits with recycle semantics and asks the supervisor to restart the browser. The edge MUST remain in the cold-standby lifecycle, keep the browser closed, and expose that cloud connectivity is recovering or degraded within standby. A scheduled wake, manual wake, explicit close, or non-standby terminal browser/CDP failure MAY still use the existing recycle/close paths.

#### Scenario: 冷待机云重连耗尽仍保持待机
- **WHEN** the core is in cold standby and cloud WebSocket reconnect attempts are exhausted
- **THEN** the core MUST NOT request recycle shutdown or exit solely because of that cloud reconnect exhaustion
- **AND** the Electron supervisor MUST NOT start a new browser for that environment as a result of this condition
- **AND** the environment remains represented as cold standby with cloud recovery pending

#### Scenario: 非冷待机云不可恢复沿用既有诚实下线
- **WHEN** the core is not in cold standby and cloud reconnect attempts are exhausted
- **THEN** the existing honest shutdown/recycle behavior remains available so the node does not silently pretend to be online

### Requirement: 冷待机子进程退出不得被分类为普通异常重启

The Electron supervisor SHALL classify a child-process close while `coldStandbyPending` or `coldStandbyActive` is set as a standby lifecycle event, not as a normal abnormal exit. It MUST NOT consume ordinary crash-respawn budget or immediately launch a browser unless a scheduled/manual wake explicitly asks it to leave standby.

#### Scenario: 冷待机中子进程退出不立即 respawn
- **WHEN** an edge child process closes while the shell marks the environment as cold-standby pending or active
- **THEN** the shell keeps the environment in standby/degraded-standby state and MUST NOT immediately call the normal environment start flow

#### Scenario: 非冷待机异常退出仍按重起策略处理
- **WHEN** an edge child process closes abnormally outside cold standby
- **THEN** the existing bounded respawn and honest give-up policy continues to apply

### Requirement: Exhausted CDP control-stall recovery SHALL honor browser ownership during recycle

When recovery from an input-control stall reaches an unrecoverable terminal state, the edge SHALL use the existing honest shutdown and supervised recycle semantics. If the browser is owned by the edge, the recycle path MUST establish a fresh browser boundary before future work. If the browser is external or reused, the edge MUST only honestly stop and leave it untouched; it MUST NOT terminate, force-stop, or otherwise interfere with that browser.

#### Scenario: Owned browser reaches unrecoverable control-stall state
- **WHEN** an edge-owned browser cannot recover from a CDP input-control stall within the bounded recovery policy
- **THEN** the edge follows its existing recyclable terminal path and future work is admitted only by the restarted node

#### Scenario: External browser reaches unrecoverable control-stall state
- **WHEN** an external or reused browser cannot recover from a CDP input-control stall
- **THEN** the edge honestly stops and requires operator recovery, while leaving that browser process untouched

### Requirement: 外部占用拒启后的本机关闭不得触碰或假称关闭占用端

当 AdsPower `browser-profile/start` 因其他设备或窗口占用而在取得本机浏览器句柄前拒绝启动，且操作者随后关闭本机自动化时，监督器 SHALL 将该环境的本机自动化意图收敛为停止、清除本轮终态失败并取消本机排队/重试。监督器 MUST NOT 对该 profile 发送 stop、强杀或调试附着，MUST NOT 要求恢复接管外部会话后再关闭，也 MUST NOT 宣称占用端浏览器已被本机关闭。

#### Scenario: 占用终态关闭只收敛本机意图

- **GIVEN** 本轮 `browser-profile/start` 已被明确分类为外部占用拒绝，且本机从未取得浏览器句柄
- **WHEN** 操作者点击“关闭自动化”
- **THEN** 监督器 SHALL 将本机自动化意图置为停止、取消本机重试与排队并清除该轮错误
- **AND** SHALL 如实说明本机自动化已关闭、占用端会话未受影响

#### Scenario: 占用终态关闭不执行浏览器关闭确认

- **GIVEN** 本轮启动在 provider 分配本机浏览器句柄前已被外部占用拒绝
- **WHEN** 监督器执行无子进程关闭收敛
- **THEN** MUST NOT 调用本机 profile active/stop 路径来推断或关闭占用端浏览器
- **AND** MUST NOT 将外部仍 active 重新投影为“需恢复接管后再关”的本机失败

#### Scenario: 非占用异常继续诚实确认遗留浏览器

- **GIVEN** 自动化因非占用异常终止，且本机浏览器是否遗留无法从退出事实确定
- **WHEN** 操作者关闭自动化
- **THEN** 监督器 SHALL 继续执行既有本机浏览器关闭确认
- **AND** 只有取得确认后才 SHALL 宣称关闭完成，无法确认时 MUST 保留可操作失败

