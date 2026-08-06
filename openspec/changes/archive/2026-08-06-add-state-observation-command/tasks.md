# Tasks

> 蓝图批 3。动协议（93→95），批内锁步双仓；与批 2（`recategorize-nonpage-commands`，不动协议）并行，
> 登记表撞车集成时串行解。登记类别用批 2 的 `page_observation`（若批 2 未先落地，rebase 时对齐）。
> 设计裁定（已定，勿重议）：一条命令一次带回面 + 身份（「问现状」），不拆两条；无平台段；观察族。

## 1. 协议与登记（锁步双仓）

- [x] 1.1 两份 `protocol.ts` 逐字一致地新增请求 / 应答消息类型与载荷（面＝穷举联合含「没能确认」态 + 原因；身份观察复用既有身份载荷形状；采集时刻）。命名按语法（观察族 `域.动作`，候选 `state.read` / `state.report`，以实读协议命名惯例定）。
  <!-- aidcp-edge ff94776 / aidcp-automation 35f7c13 定名 state.read / state.report。载荷：StateReadPayload{captureId}（照 identity.read_current 关联模式）；StateReportPayload{captureId, surface, identity, observedAt}。surface 两态判别式：{outcome:'confirmed', kind: StateSurfaceKind} | {outcome:'unconfirmed', reason: browser_unavailable|executor_busy|probe_failed|page_unrecognized}；kind 穷举 = STATE_SURFACE_KINDS（home/explore/search/note_detail/profile/notification/publish/login/captcha/error，与 Native 引擎现役页面分类词表同源）。identity 两态：{outcome:'confirmed', accountId, nickname?} | {outcome:'unconfirmed', reason: browser_unavailable|executor_busy|read_failed}。两份 protocol.ts diff 为空（byte-identical 实测）。 -->
- [x] 1.2 登记表 ×2：请求登记为 `page_observation`（批 2 类别；其 identity 维非 `page_account`——身份未落定时本命令 MUST 可用，它正是解开该终局的探针之一）。
  <!-- aidcp-edge ff94776 / aidcp-automation 35f7c13：两仓各新增 page_observation 类别（提交时批 2 尚未落 master，已在类别定义处注明「与 recategorize-nonpage-commands 协调，落地时对齐」）；state.read 描述符两侧逐字段一致 {category:page_observation, transport:automation_ws, identity:bound_account, browser:required, platformFootprint:none}。identity=bound_account ⇒ 边缘身份闸按 identity 维放行、无需进救援清单。注意：automation 侧 kernel 传输闸（transport-gate-exemptions）的类别词汇不含 page_observation，调用点显式映射成 null（保守侧＝副本陈旧时不放行，不死锁；kernel 词汇扩容留给批 2 串行集成，本批不动 kernel）。 -->
- [x] 1.3 **edge-client 主动命令路由白名单**（第 4 处同步点）：请求必须放行到处理器；应答按信封 id 关联。漏放行＝静默丢弃——加反向结构断言覆盖（登记表→源码找分派点的那套已存在，新命令自动被覆盖，确认即可）。
  <!-- aidcp-edge ff94776：state.read 进 onMessage 白名单→browseHandler。「自动被覆盖」经核实不成立——既有反向断言只过滤 category==='page_automation'，新类别不在其内；已把过滤器扩成 page_automation|page_observation（test/client/operation-registry.test.ts）。变异坐实：摘掉白名单那行 ⇒ 断言当场红并点名 state.read。 -->
- [x] 1.4 protocol.md：计数 93→95 + §2 表两行 + 载荷节。
  <!-- 控制仓（本批只改文件不 commit，主 session 收口）：新增 §2.9 观察命令表（两行）+ §3.14 载荷节。偏离说明：protocol.md 头部自 2026-07 起明写「本文不复制易漂移的消息总数」，已无计数可改；93→95 落在两仓 AC-PROTO-02 断言（均已改 95 并实测过）。 -->

## 2. 边缘实现

- [x] 2.1 实读引擎现有观察能力：FB 面分类器（`facebook/probes/page-structure.ts` 一族已退役？以 Native 引擎内的分类为准——先盘引擎里现役的面分类落点）与身份读取路径（`identity.read_current` 的实现形态照抄其模式）。**能走注入路由现有探测就不动 Rust**；必须动 Rust 时：排除表 / 清单 / 时序三表同步纪律 + `node scripts/build-native-page-engine.mjs` 重钉产物摘要（批 1 趟过：改 Rust / 改清单后 artifact 测试与 gate:native 会逐个点名，修到全绿）。
  <!-- aidcp-edge ff94776 零 Rust 改动、零产物摘要变更。实盘结论：现役面分类落点 = 引擎 page_probe 命令（XHS 走 probe.rs classify_page；FB 走 facebook-router/90-dispatch.js 把内部 classify() 归一到同一张 PageKind 词表），两平台都登记为阻断豁免的纯读探针，TS 层可直接执行——无需新造探测。身份读取复用装配层 readPlatformIdentity（FB=Native cookie 派生 identity_bootstrap、XHS=TS CDP 就地扫描，运行期身份校验体同一条路径），以 readIdentity 选项注入 browse-session、allowNavigate:false 强制。已知词表缺口如实处理：FB 的 Reels / 群组页在共享 PageKind 词表里归 unknown ⇒ 应答 unconfirmed page_unrecognized（不扩 Rust 词表，留给后续批次）。 -->
- [x] 2.2 纯读保证：实现路径零导航零输入零滚动；「没能确认」真实可达（页面读不出时不伪装、不默认面）。
  <!-- aidcp-edge ff94776：answerStateRead 只执行 page_probe 一种引擎命令 + 注入身份读；冷待机回 browser_unavailable 且绝不唤醒浏览器（不走 handleBrowserAbsentCommand 的 wake 路径）；会话 quiesce（独占任务持有引擎单写 owner 位）回 executor_busy 且零引擎触碰——观察绝不抢占在跑任务的引擎会话；probe 失败/超时 → probe_failed；引擎 unknown → page_unrecognized；缺 captureId 按语法规则二 fail-closed 拒收（不伪造应答）。 -->
- [x] 2.3 测试：请求→应答关联、两态诚实、纯读断言、路由白名单覆盖确认。
  <!-- aidcp-edge ff94776 test/native-page-engine/state-observation.test.ts 6 用例全绿：信封 id 关联（replyTo=请求 id）、两态诚实（unknown 不伪装 / probe_failed / read_failed / 面身份两维独立）、纯读断言（executions kinds 恒 ⊆ ['page_probe']；executor_busy 时恒空）、fail-closed 拒收。白名单覆盖 = 扩展后的反向结构断言（见 1.3）。 -->

## 3. aidcp-automation 云端侧

- [x] 3.1 下发出口与应答处理（信封关联，pending 表模式照 `identity.read_current` 的既有形态）；**只落通道不接决策**（何时问、问完怎么办＝阶段四）。
  <!-- aidcp-automation 35f7c13：EdgeCommand 增 state_read + command-bridge 映射 state.read；软暂停/配额休眠/评论在途闸豁免 state_read（恢复探针恰在浏览被扣时最需要）；handler 'state.report' → 事件 state.report.arrived{report, accountId, envelopeId, ts}（envelopeId=边缘回填的请求信封 id）；src/comm/state-observation.ts StateObservationChannel：captureId pending 表 + 20s 有界超时（照本人身份采集兜底口径、计时器可注入 unref）；RoleDispatcher.askEdgeState() 暴露能力、零触发策略。另：boundaries/module-ownership.json 按 src/comm/ inherit 规则直接登记新文件（refresh 生成器被根目录未裁定文件卡死，循既有登记先例）。 -->
- [x] 3.2 测试：发得出（出口闸放行）、收得到（应答关联回请求方）、超时如实（不静默）。
  <!-- aidcp-automation 35f7c13 test/comm/state-observation.test.ts 7 用例全绿：登记表放行（描述符 deepEqual，防 operation_unclassified 静默拒发）、桥接映射、handler 事件携 envelopeId、reported 关联、timeout 如实（且迟到应答不复活已判 timeout 的请求）、not_sent 与 timeout 两态分开、错 captureId 不冒领 pending。 -->

## 4. 验证与集成

- [x] 4.1 双仓 `typecheck` + `test:acceptance` + 全量 + edge `gate:native`；AC-PROTO 计数断言更新（93→95）。
  <!-- 实测数字：edge typecheck 过；edge test:acceptance 40/40；edge 全量 3191 用例 3190 pass / 0 fail / 1 skip（首跑红一处：identity-revalidation 的宿主装配契约断言要求 nativeSession.onCloudCommand 全 main.ts 只出现一次——已改为 state.read 走闸内唯一执行入口、只在闸内豁免租约抑制，复跑 36/36 绿）；edge gate:native OK（fmt,clippy,test；零 Rust 改动零摘要变更）。automation typecheck 过；test:acceptance 299 pass / 0 fail（首跑红两处：①单写断言要求 kernel 导入行原样 → 拆成独立 type-only import；②boundary census 缺新文件归属 → 登记 module-ownership.json）；automation 全量 2316 用例 2313 pass / 0 fail / 3 skip。AC-PROTO-02 两仓 93→95 + 新增 AC-PROTO-08C 载荷往返。 -->
- [x] 4.2 变异：摘掉白名单放行 ⇒ 反向结构断言红；应答「没能确认」改伪装成具体面 ⇒ 两态测试红。
  <!-- 两条都实跑坐实：①删 edge-client 白名单 state.read 行 ⇒ 「every dispatchable page command is actually routed」红并点名；②observeSurfaceForStateRead 把 page_unrecognized 改成 confirmed home ⇒ 「unrecognized page kind is reported as unconfirmed」红。均已还原并复跑全绿。 -->
- [x] 4.3 推分支、报告（不 land、不部署——主 session 串行集成 + 部署）。
  <!-- aidcp-edge 分支 add-state-observation-command @ ff94776 已推 origin；aidcp-automation 同名分支 @ 35f7c13 已推 origin。未 land、未部署。 -->
- [x] 4.4 真机项登记 backlog：引擎侧改动需出包；「问现状在真机上对五种面各答对一次」。
  <!-- docs/real-machine-acceptance-backlog.md 簇 149（六项：五面各答对一次、captcha/login 面穿透、FB Reels/群组 unconfirmed 如实、冷待机不唤醒、任务期 executor_busy 不扰动、纯读复核）。引擎零 Rust 改动，但边缘 TS 改动需出包才到运营机。 -->

## 5. 主 session 收尾（agent 不做）

- [x] 5.1 锁步成对落地 + 闸复验 + 部署 dev。
  <!-- 集成提示：①与批 2 撞的三个文件：两仓 operation-registry（page_observation 类别定义与批 2 的类别词汇对齐）、edge test/client/operation-registry.test.ts（反向断言过滤器与 ≥25 下限）、edge identity-command-gate 无改动（本批未动救援清单）；②land 后跑 scripts/operation-registry-parity 与 scripts/protocol-parity（读 canonical checkout，分支上跑不了）；③kernel transport-gate-exemptions 的类别词汇未扩（automation-edge-access 调用点已显式映射 null 保守处理），若批 2 扩 kernel 词汇，可顺手把该映射改回直传。 -->
- [x] 5.2 tasks 回写 master sha → validate → archive。

## 6. 集成实录（主 session，2026-08-06）

- master 落点：edge `1b7465b`、automation `7091662`（分支 ff94776 / 35f7c13 rebase 批 2 后重写）。
- 冲突解法：类别词汇 / 构造器 / 断言过滤器取批 2 的（agent 与批 2 各自定义的 `page_observation` 合一）；`state.read` 条目叠上，描述符统一用批 2 构造器 ⇒ **identity 从 agent 的 bound_account 对齐为 local_environment**（观察不以账号名义动作，且与读身份两条同类同维）；kernel 传输闸调用点用批 2 的映射（page_observation→page_automation），agent 的 null 映射与遗留 type import 随之退役。
- 闸复验：协议逐字一致、登记表 44 条逐字段一致。部署 dev（备份 → rsync → restart → active / NRestarts=0 / 8787 / 零 error）。
- 真机：backlog 簇 149（六项）；云端通道零触发方（阶段四接线），真机验收需手动调用。边缘 TS 改动需出包才到运营机（例行）。
