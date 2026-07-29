# tasks — restore-native-facebook-inline-expand-read

> 全部落 `aidcp-edge`。云端（`aidcp-cloud`）本 change 零改动。
> 进度按 sub-repo 分节回写，完成后按 `<!-- <repo> <commit-sha> 备注 -->` 标注（sha 必须取自**已推送**的提交）。

## 1. aidcp-edge — 页面规则脚本：就地读的展开与校验

- [x] 1.1 在 Facebook 页面规则脚本的共享层新增「就地展开读全文」助手：入参为已锁定的目标卡根节点，输出 `{ok, body, reason}`；只在该卡的消息容器作用域内操作，绝不跨卡、绝不点链接。
<!-- aidcp-edge 90e093c 共享层 inlineExpandRead 助手，作用域锁在目标卡 message 容器 -->
- [x] 1.2 免点击捷径：先判定消息容器的全文是否已在 DOM 内、仅被视觉截断；成立则直接取全文返回，**不**点击。该判定必须在任何点击之前完成。
<!-- aidcp-edge 90e093c 捷径判据（比例 1.2 + 绝对差 30 字符）在任何点击之前 -->
- [x] 1.3 展开控件定位：限定在目标卡消息容器内的非链接可点控件，以结构为主判据，文案作辅助并覆盖既有词形（`查看更多` / `展开` / `See more` / `View more` / `Ver más` / `Mostrar más` / `Voir plus`）。找不到控件 ⇒ 走「短帖正常成功」路径，不失败。
<!-- aidcp-edge 90e093c 结构主判据 + 文案辅助，新增越南语 Xem thêm / 查看全文 / 顯示更多 -->
- [x] 1.4 增长校验：点击后按有界轮询（固定轮数 × 固定间隔，量级参照已退役实现的 6 × 300ms）等待正文渲染长度增长；长度未增 ⇒ 返回 `expand_no_effect`，**不**返回帖子详情。
<!-- aidcp-edge 90e093c settle 400ms + 6 × 300ms 有界轮询 -->
- [x] 1.5 环境校验：在展开动作前后各采一次 URL、可见弹层数量、目标卡在顶层卡序列中的序号；任一变化 ⇒ 返回 `context_changed`，中止就地读。
<!-- aidcp-edge 90e093c URL / 弹层数 / 目标卡序号三项，展开前后各采一次 -->
- [x] 1.6 把 feed 面 `note_open` 分支改为调用 1.1 的助手，成功时用展开后的正文构造帖子详情上报；失败时按 1.4 / 1.5 的具名 reason 回失败终态。
<!-- aidcp-edge 90e093c 90-dispatch feed 面分支改走助手，noteDetail 接 bodyOverride -->
- [x] 1.7 动作名归一：feed 面开帖失败的动作名由 `open` 改为云端规范名 `open_note`（脚本内其余动作名已对齐，仅此一处漂移）。改前在 edge 与 cloud 两侧全局搜索把 `open` 当动作名消费的位置，确认无依赖后再改。
<!-- aidcp-edge 90e093c open → open_note；全局搜索确认云端无消费 open 这个错名的位置 -->

## 2. aidcp-edge — Rust 执行层：环境变化回落详情

- [x] 2.1 Facebook 命令执行入口识别脚本返回的 `context_changed` 就地读终态。
<!-- aidcp-edge 90e093c facebook_inline_read_context_changed 只认这一条具名终态，不按 ok=false 泛化 -->
- [x] 2.2 命中时按该帖规范 permalink 走既有详情路径（URL 校验 → 导航 → 等就绪 → 等目标身份确认的详情），以 detail 面诚实上报该帖；导航或身份确认失败仍回具名失败，MUST NOT 退化成静默成功。
<!-- aidcp-edge 90e093c 复用 validated_facebook_content_url + until_requested_detail；回落失败回 inline_fallback_detail_unconfirmed -->
- [x] 2.3 确认 `think_ms` 在 Rust 侧保持纯透传、不新增消费点（等待归 TypeScript 会话层，见 3.2），避免两处各等一次。
<!-- aidcp-edge 90e093c Rust 侧 think_ms 保持纯透传，未新增消费点 -->

## 3. aidcp-edge — TypeScript 会话层：节奏字段消费

- [x] 3.1 `applyPacingSnapshot` 不再整体丢弃：留存 `tempo` 供就地读 read floor 使用；`opFloorsMs` 本 change 仍不消费，但须留存并在注释里注明「未接线 —— 最小间隔 gating 属后续 change」，不得再写成「无事可做」。
<!-- aidcp-edge 90e093c 留存 tempo；opFloorsMs 未接线已在注释具名说明 -->
- [x] 3.2 命令执行前统一施加动作前犹豫：收到带 `thinkMs` 的命令时，在触达页面前等待抖动后的时长；等待走可中断 sleep，抢占按既有语义处理为调度事件、不记动作失败。与既有 feed 停留合并为单一「命令前节奏」入口，避免两处各判一半。
<!-- aidcp-edge 90e093c applyCommandPacing 单一入口；thinkMs 只叠抖动、不重复乘 tempo（云端已算进中心值） -->
- [x] 3.3 就地读 read floor：feed 面开帖成功返回帖子详情后，按正文长度（叠 `tempo`）算出 read floor 并锚在就地读开始时刻；行为参照已退役实现的同名计算。
<!-- aidcp-edge 90e093c computeInlineReadFloorMs 在 browse-session 自带一份，不 import 已退役的 FB 会话模块（避免破坏打包裁剪判据） -->
- [x] 3.4 停留取 max：下一条 `page.scroll` 的实际停留取「就地读 read floor」与「新卡锚点 dwell 目标」的较大者，MUST NOT 相加；锚点消费一次后清零，避免残留旧值。
<!-- aidcp-edge 90e093c 锚点取就地读开始时刻、消费一次即清零；读失败不留锚点 -->

## 4. aidcp-edge — 行为级回归测试

- [x] 4.1 就地读判定层用例（克制，覆盖分支即可，不铺量）：折叠长帖点击展开后正文变长并上报；全文已在 DOM 内走捷径不点击；点击后长度未增回 `expand_no_effect` 且不产生详情上报；URL / 弹层数 / 卡序号任一变化回 `context_changed`；无展开控件的短帖正常成功且不是 `no_target`。
<!-- aidcp-edge 90e093c 6 条 router 用例（展开 / 捷径 / 展开无效 / 环境变化 / 短帖 / 动作名） -->
- [x] 4.2 回落用例：`context_changed` 触发详情导航路径，最终以 detail 面上报该帖。
<!-- aidcp-edge 90e093c Rust fake-CDP 用例 facebook_inline_context_change_falls_back_to_detail_navigation -->
- [x] 4.3 节奏用例：带 `thinkMs` 的命令产生实际前置等待；就地读后的 `page.scroll` 停留取 read floor 与 dwell 的较大者而非二者之和；极短就地读不产生零延迟秒滚。
<!-- aidcp-edge 90e093c 4 条 browse-session 用例（thinkMs / 取 max / 短读仍有地板 / 读失败不留锚点） -->
- [x] 4.4 动作名用例：feed 面开帖失败回执的动作名为 `open_note`。
<!-- aidcp-edge 90e093c 并入 4.1 最后一条用例 -->
- [x] 4.5 `npm run typecheck` + `npm test` + `npm run test:acceptance` 全过；Rust 侧 `cargo test`（cargo 不在 PATH，须指 rustup toolchain 下的 bin）。
<!-- aidcp-edge 90e093c typecheck 通过；npm test 2571 passed / 0 failed；test:acceptance 30 passed；cargo test 全绿（fake_cdp 38） -->

## 5. 控制仓 — 收口

- [x] 5.1 把真机验收项登记进 `docs/real-machine-acceptance-backlog.md`：真实 Facebook 长帖的展开控件形态、两种折叠语义（视觉裁短 vs 点击补文）的实际分布、多语言文案命中率、以及规则模式吞吐下降的实测量级。
<!-- aidcp 控制仓 簇 120（9 项），另含人设模式粗筛质量对比与动作名归一回归 -->
- [x] 5.2 把「Native 路径缺少 `command-pacing` 要求的操作类命令最小间隔 gating」单列登记（本 change 明确不做），写清现状坐标与影响面。
<!-- aidcp 控制仓 记在簇 120 头部并显式标注「不是真机项」，附 applyPacingSnapshot 坐标与两层差异 -->
- [x] 5.3 `openspec validate restore-native-facebook-inline-expand-read --strict` 通过。
<!-- aidcp 控制仓 validate 通过 -->
