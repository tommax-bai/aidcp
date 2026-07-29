# tasks — restore-native-facebook-inline-expand-read

> 全部落 `aidcp-edge`。云端（`aidcp-cloud`）本 change 零改动。
> 进度按 sub-repo 分节回写，完成后按 `<!-- <repo> <commit-sha> 备注 -->` 标注（sha 必须取自**已推送**的提交）。

## 1. aidcp-edge — 页面规则脚本：就地读的展开与校验

- [ ] 1.1 在 Facebook 页面规则脚本的共享层新增「就地展开读全文」助手：入参为已锁定的目标卡根节点，输出 `{ok, body, reason}`；只在该卡的消息容器作用域内操作，绝不跨卡、绝不点链接。
- [ ] 1.2 免点击捷径：先判定消息容器的全文是否已在 DOM 内、仅被视觉截断；成立则直接取全文返回，**不**点击。该判定必须在任何点击之前完成。
- [ ] 1.3 展开控件定位：限定在目标卡消息容器内的非链接可点控件，以结构为主判据，文案作辅助并覆盖既有词形（`查看更多` / `展开` / `See more` / `View more` / `Ver más` / `Mostrar más` / `Voir plus`）。找不到控件 ⇒ 走「短帖正常成功」路径，不失败。
- [ ] 1.4 增长校验：点击后按有界轮询（固定轮数 × 固定间隔，量级参照已退役实现的 6 × 300ms）等待正文渲染长度增长；长度未增 ⇒ 返回 `expand_no_effect`，**不**返回帖子详情。
- [ ] 1.5 环境校验：在展开动作前后各采一次 URL、可见弹层数量、目标卡在顶层卡序列中的序号；任一变化 ⇒ 返回 `context_changed`，中止就地读。
- [ ] 1.6 把 feed 面 `note_open` 分支改为调用 1.1 的助手，成功时用展开后的正文构造帖子详情上报；失败时按 1.4 / 1.5 的具名 reason 回失败终态。
- [ ] 1.7 动作名归一：feed 面开帖失败的动作名由 `open` 改为云端规范名 `open_note`（脚本内其余动作名已对齐，仅此一处漂移）。改前在 edge 与 cloud 两侧全局搜索把 `open` 当动作名消费的位置，确认无依赖后再改。

## 2. aidcp-edge — Rust 执行层：环境变化回落详情

- [ ] 2.1 Facebook 命令执行入口识别脚本返回的 `context_changed` 就地读终态。
- [ ] 2.2 命中时按该帖规范 permalink 走既有详情路径（URL 校验 → 导航 → 等就绪 → 等目标身份确认的详情），以 detail 面诚实上报该帖；导航或身份确认失败仍回具名失败，MUST NOT 退化成静默成功。
- [ ] 2.3 确认 `think_ms` 在 Rust 侧保持纯透传、不新增消费点（等待归 TypeScript 会话层，见 3.2），避免两处各等一次。

## 3. aidcp-edge — TypeScript 会话层：节奏字段消费

- [ ] 3.1 `applyPacingSnapshot` 不再整体丢弃：留存 `tempo` 供就地读 read floor 使用；`opFloorsMs` 本 change 仍不消费，但须留存并在注释里注明「未接线 —— 最小间隔 gating 属后续 change」，不得再写成「无事可做」。
- [ ] 3.2 命令执行前统一施加动作前犹豫：收到带 `thinkMs` 的命令时，在触达页面前等待抖动后的时长；等待走可中断 sleep，抢占按既有语义处理为调度事件、不记动作失败。与既有 feed 停留合并为单一「命令前节奏」入口，避免两处各判一半。
- [ ] 3.3 就地读 read floor：feed 面开帖成功返回帖子详情后，按正文长度（叠 `tempo`）算出 read floor 并锚在就地读开始时刻；行为参照已退役实现的同名计算。
- [ ] 3.4 停留取 max：下一条 `page.scroll` 的实际停留取「就地读 read floor」与「新卡锚点 dwell 目标」的较大者，MUST NOT 相加；锚点消费一次后清零，避免残留旧值。

## 4. aidcp-edge — 行为级回归测试

- [ ] 4.1 就地读判定层用例（克制，覆盖分支即可，不铺量）：折叠长帖点击展开后正文变长并上报；全文已在 DOM 内走捷径不点击；点击后长度未增回 `expand_no_effect` 且不产生详情上报；URL / 弹层数 / 卡序号任一变化回 `context_changed`；无展开控件的短帖正常成功且不是 `no_target`。
- [ ] 4.2 回落用例：`context_changed` 触发详情导航路径，最终以 detail 面上报该帖。
- [ ] 4.3 节奏用例：带 `thinkMs` 的命令产生实际前置等待；就地读后的 `page.scroll` 停留取 read floor 与 dwell 的较大者而非二者之和；极短就地读不产生零延迟秒滚。
- [ ] 4.4 动作名用例：feed 面开帖失败回执的动作名为 `open_note`。
- [ ] 4.5 `npm run typecheck` + `npm test` + `npm run test:acceptance` 全过；Rust 侧 `cargo test`（cargo 不在 PATH，须指 rustup toolchain 下的 bin）。

## 5. 控制仓 — 收口

- [ ] 5.1 把真机验收项登记进 `docs/real-machine-acceptance-backlog.md`：真实 Facebook 长帖的展开控件形态、两种折叠语义（视觉裁短 vs 点击补文）的实际分布、多语言文案命中率、以及规则模式吞吐下降的实测量级。
- [ ] 5.2 把「Native 路径缺少 `command-pacing` 要求的操作类命令最小间隔 gating」单列登记（本 change 明确不做），写清现状坐标与影响面。
- [ ] 5.3 `openspec validate restore-native-facebook-inline-expand-read --strict` 通过。
