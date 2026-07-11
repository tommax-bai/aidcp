## Context

关闭按钮只在暂停态显示，是关指纹浏览器的唯一入口。现状链路（edge master `1d2620a`，10-agent 对抗验证）：
- 关闭 → 外壳 `closeEdge`（`main.cjs`）→ 发 `lifecycle.close` 给核心 → `CoreLifecycleController.finalize({preserveBrowser:false,requireConfirmedClose:true})` → `closeOwnedBrowser` → `AdsPowerProvider.killAndConfirmDead` = `stop()`(本地 API `browser/stop`) + `confirmClosed()`(轮询 `browser/active`)。
- provider 恒为 adspower、`reused` 恒 false，故关闭一定走 `killAndConfirmDead`（已排除 reused 跳过 / 端口身份漂移两假设）。

两处现状约束是本设计要绕开的：
1. **无 OS 级实杀**：adspower 的浏览器实例句柄 `pid:null`、`kill:()=>stop()`，回收全靠软性 `browser/stop`。对比 self 路径（`chrome-launcher.ts`）是真 SIGTERM→SIGKILL + 轮询确认调试端口释放。
2. **收尾不诚实**：`stop()` 吞掉一切失败不上抛；`confirmClosed()` 在「非活跃自报」或「任何查询报错」时都返回 true（"查不动就当已关"），只有连 5 次 Active 才 false。核心据此 `exit(0)`，外壳只凭退出码宣称「浏览器已关闭。」。
3. **暂停先拆 CDP**：暂停 `deactivate` 已 `session.close()→cdp.close()`。领先假设（真机待证）：AdsPower 因此把该驻留分身当脱离/非活跃，随后 `browser/stop` 空操作、真窗口残留。

约束：edge-only、不动协议 v2 / 云端 / 风控 / 发布；不破坏「暂停保持浏览器打开」这一正确语义；`core-lifecycle.ts` + `browser-provider.ts` 与 `self-contained-ads-runtime` 逐字相同（热点、单写、须 forward-port）；遵守浏览器生命周期核心单写与「绝不静默假成功」红线。

## Goals / Non-Goals

**Goals:**
- 用户发起关闭后，指纹浏览器**真的被关掉**；关不掉时**如实呈现「未确认关闭」**而非假报已关。
- 关闭确认基于**独立于 AdsPower 自报状态的权威信号**，不被 `browser/active` 的非活跃自报或查询失败糊弄。
- 软停止未达成实证死亡时能**升级实杀兜底**，使「诚实但仍开着」不再是终局。
- 补齐假成功分支的回归测试。

**Non-Goals:**
- 不改「暂停保持浏览器打开」语义；不引入 headless / 最小化。
- 不改协议、不动云端、无 ECS 部署。
- 不重构 provider 抽象或 CDP 接入下游（定位/拟人/读身份零改）。
- 不给 self 路径加东西（其回收已正确）。
- 不在本变更承诺「彻底改造暂停期 CDP 拆除时序」——用关闭期权威实证 + 升级绕开它（见 Decisions D4 / Open Questions）。

## Decisions

### D1. 权威关闭信号 = 该分身 CDP 调试端点不再应答，而非 AdsPower 自报
关闭确认以**探测该分身调试端口的 `/json/version` 是否仍应答**为准（活 = 仍应答；死 = 端口不再应答，有界轮询）。理由：对抗验证决定性洞见——AdsPower 的 `browser/active` 会说谎（拆 CDP 后自报非活跃而窗口仍在）。调试端口在浏览器存活期一直开着（端口 ≠ 我们暂停时关掉的那条**客户端** socket），故端口探活是拆 CDP 之后仍有效的真死活判据；这正是 self 路径 `chrome-launcher.ts` 已用的「端口释放确认」手法，adspower 路径复用之。
- 备选：继续信 `browser/active`（现状、已坏）；查 OS 进程表（需内核 PID，AdsPower 不直接给）。均劣于端点实证。
- 权衡：若 AdsPower 关掉调试端口却保留一个不可驱动的窗口，端点探活会判「已关」而窗口残留——但那是另一类（不可驱动窗口）故障，且仍严格优于现状；记为 Risk。

### D2. `confirmClosed` 诚实化：查不动 = 不确定，绝不当已关
`confirmClosed` 重写为「有界轮询直到调试端点变暗」：端点仍应答 → 未死，继续；查询报错 → **不确定**，继续重试（不再 `return true`）；有界上限内端点变暗 → 已关（true）；上限耗尽仍应答/仍不确定 → **如实返回未确认**（false）。`stop()` 的失败 **纳入结论、不静默吞**（保留容忍继续、但记入诚实关闭判定与日志）。

### D3. 升级实杀兜底（软停止未达成实证死亡时）
关闭序列改为：发 `browser/stop` → 有界等端点变暗 → 未暗则**重发 `browser/stop`** → 仍未暗则**尽力做 OS 级强杀兜底**（解析该分身内核进程后 SIGKILL）→ 再确认端点变暗。拿不到可靠 PID 时**不假成功**，退回 D2 的「如实未确认」。
- PID 解析优先级：AdsPower `browser/start`/`active` 回参（`webdriver`/debug_port）→ 经调试端点 `/json/version` 的 `webSocketDebuggerUrl`/端口反查占用进程 → 皆不得则放弃 OS 杀、走诚实未确认。
- 备选：只做诚实化不加实杀（D2 单独）。**否决**——决定性洞见证明诚实化只把「假成功」变「诚实卡住」，操作者仍关不掉浏览器；必须有一条能真关的路径。
- 权衡：OS 杀 AdsPower 托管内核可能让 AdsPower 自身账本短暂不一致 → 缓解：优先用 AdsPower 自己的停止，OS 杀只作**最后兜底**且清晰记日志；AdsPower 下次启动的在跑分身对账（`reconcileRunningProfiles`）已能收拾遗留。可选：把 OS 杀升级用 env 旗标护栏（默认开）以便一键回退。

### D4. 关闭不依赖暂停前的连接状态
关闭路径按目标分身 `user_id` **重新发起**权威停止并按 D1 端点实证判定，不复用暂停前已拆的 CDP 连接、不因「已 detach」而静默空转。这样即便 D3 中的 pause→detach 假设成立，关闭仍能靠「重发 stop + 端点实证 + 升级实杀」收敛，而**无需改动暂停语义**（改暂停时序留作 Open Question，非本变更必需）。

### D5. 外壳诚实收尾，改动最小
- 核心修好后（只在端点实证变暗才 `exit(0)`，否则 `lifecycle.close_failed`），外壳沿现有分支即自动继承诚实：确认关 → `session:'closed'`；未确认 → 保持暂停 + 「关闭状态未能确认」。故外壳大部分无需改。
- 唯一补的洞：`closeEdge` 的 **no-child 分支**（驻留核心在暂停与关闭间已死）MUST NOT 零停止直接宣称「已关闭」。对本进程自有分身补一次「停止 + `browser/local-active`（外壳已有 `listActiveProfiles`）实证」，或如实报「无法确认已关」。保持外壳只读 ads-local-api 边界——如需外壳侧发停止，走窄封装、不扩成通用写通道。

## Risks / Trade-offs

- [端点探活假阴：调试端口关了但残留不可驱动窗口] → 判「已关」而窗口在，但属另一类故障且仍优于现状；真机观察，必要时叠加一次 AdsPower `browser/active` 交叉核对。
- [OS 级杀让 AdsPower 账本不一致] → OS 杀仅最后兜底、优先 AdsPower 自停；清晰日志；依赖 AdsPower 下次启动分身对账收尾；OS 杀升级可 env 护栏默认开、便于回退。
- [`browser/stop` 1req/s 节流 + 有界轮询增加关闭时延] → 设关闭总时长有界上限，期间显示诚实「正在关闭…」；到界如实判未确认，绝不无限挂起。
- [热点文件 `core-lifecycle.ts`/`browser-provider.ts` 与 self-contained 逐字相同] → 单写纪律、谨慎落地、必 forward-port，避免并发漂移。
- [拿不到内核 PID 使 OS 杀不可用] → 退回诚实未确认（不假成功），并把该真机缺口登记 backlog 供后续补 PID 解析。

## Migration Plan

- edge-only、无 ECS：改动落 `../aidcp-edge`，`npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿后提交推 master。
- 生效路径：运营机 pull master + 安装包重建（登记真机 backlog 项：暂停→关闭后浏览器真关、失败态如实呈现、no-child 场景）。
- 回退：纯正确性修复，回退 = revert 对应 edge commits；OS 杀升级若加 env 护栏则可单独关闭该升级层、保留诚实化部分。

## Open Questions

- AdsPower `browser/start` / `browser/active` 回参是否暴露稳定内核 PID / 可用于 OS 杀的句柄？（apply 时读码 + 真机确认；否则经调试端口反查占用进程。）
- 真机核实：暂停期 `cdp.close()` 是否确实使 AdsPower 把该分身翻为非活跃、致 `browser/stop` 空操作？若属实，评估是否值得把「会 detach 的 CDP 拆除」推迟到真关闭（改暂停时序）作为后续优化——本变更用关闭期权威实证 + 升级先行绕开。
