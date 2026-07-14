# honest-core-log-severity

## Why

桌面客户端把**核心进程的日志走了哪根管子**当成了**这条日志是不是错误**。

`src/electron/main.cjs` 里，核心子进程的两个输出通道是这样接的：

```
child.stdout.on('data', (chunk) => handleEdgeOutput(handle, chunk.toString()));        // isError 默认 false
child.stderr.on('data', (chunk) => handleEdgeOutput(handle, chunk.toString(), true));  // isError 硬编码 true
```

然后状态投影直接读这个标志：

```
const next = { edge: isError ? 'warning' : 'running', lastMessage: message };
if (!isError && handle.status.edgeFailure) next.edgeFailure = null;
```

但 Node 的 `console.warn` 和 `console.error` **本来就写 stderr**。核心 `src/` 里现有
**34 处 `console.warn` + 25 处 `console.error`**，其中绝大多数是良性的诊断 / 进度 / 排队说明。
它们每打印一行，客户端就把该环境的徽标翻成 `edge: 'warning'`，呈现层随即讲出三句**假话**：

- 环境栏：`异常`（`level: 'error'`, `needsAction: true`）→ 该环境被染红并浮到列表顶部，与真正待人工的
  登录 / 验证码 / 风控受限混作一谈。
- 详情：`运行异常` / `引擎未能继续运行，请查看详情后重新启动`。
- 在场：`引擎已停止，请查看详情或重新启动`。

**核心根本没停**——它下一行正常日志一到，`edge` 又被翻回 `running`。这就是运营看到的
「发布时闪红、又秒恢复」。发布路径命中率最高（租约抑制说明 + `[publish-submit-diag]` 诊断在一次发布里必现），
但这不是发布专属 bug：**任何**良性 warn 都会红。

最刺眼的一条实例（`src/main.ts:467`）：

```
外壳暂时给不出浏览器槽位（…）：本次诚实作答，环境仍在等槽位队列里
```

核心在**诚实地说「我在排队」**——「资源暂时被占绝不判失败，排队是机器行为」是刚刚定案的不变量——
而客户端把这句话画成红色的「引擎已停止」。这不是显示瑕疵，是**呈现层在替系统撒谎**。

第二个受害面更隐蔽：`rememberEdgeFailureCandidate()` 的第一行是

```
if (!isError && !/(启动失败|失败|不可达|not allowed|being used|no_target|code=-?\d+)/i.test(raw)) return;
```

`isError` 为真时**直接短路掉内容正则**，于是任何一条良性 stderr 都会被记成
`handle.lastEdgeFailureLine`。等到核心**真的**异常退出时，`abnormalExitFailurePatch()` 拿出来给运营看的
「失败原因」是最后那条**无关**的良性 warn。**真出事时，界面给的归因是错的。**

这与 `honest-first-connect-label`（启动被讲成「正在重新连接」）是同一族红线：**UI 断言了一个状态里
并不存在的事实**。那次是「重连」预设了「连过」；这次是「异常」预设了「出错了」，而系统唯一知道的事实
只是「这行字走了 fd 2」。

## What Changes

**不变量：「哪根管子」是传输事实，不是语义事实。** 状态投影必须按**内容**判定严重级别，不得按通道判定。

- **新增纯函数分类器** `classifyCoreLogLine(message)` → `fatal` / `warn` / `info`，落在既有的纯模块
  `src/electron/fleet.cjs`（`classifyAdsInUse` 已是「内容签名 + 上下文闸防误命中」的先例，同文件同测试位）。
- **状态投影只认 `fatal`**：`edge: severity === 'fatal' ? 'warning' : 'running'`。良性 warn 不再染红、
  不再浮顶、不再说「引擎已停止」。
- **失败候选只认 `fatal`**：`rememberEdgeFailureCandidate` 不再被 `isError` 短路，于是核心真崩时给出的
  归因是**真的那条**失败行，而不是最后一条良性 warn。
- **日志文件保持诚实**：`appendEdgeLog(envId, message, isError)` 继续按**真实通道**记 `ERR` 前缀。
  传输事实该被如实记录——只是它不再被误读成语义。
- **不吞真失败（红线）**：`fatal` 的正例集合覆盖既有失败签名（启动失败 / 不可达 / `not allowed` /
  `being used` / `no_target` / `code=-N`）并补上英文异常形状（`Error:` / `TypeError` / `ECONNREFUSED` /
  `unhandled` / `FATAL` 等），未识别的 stderr 行**不再**默认判死。**兜底不变**：核心真的异常退出时，
  `child.on('close')` 的 `abnormalExitFailurePatch()` 才是权威判据——它一直在，且不受本次改动影响。
  也就是说：日志行只做**预测**、退出码才是**权威**；把预测调准，权威一分不动。

**明确不做**：本 change **不碰 `aidcp-edge/src/main.ts`** —— 那 6 处良性 `console.warn` 的措辞不用改
（改了也只是掩盖症状），而且该文件正由并行流改动（FB 租约闸的节奏豁免）。修在呈现层才是修根因。

## Impact

- Affected specs: `edge-companion-ui`
- Affected code: `aidcp-edge/src/electron/fleet.cjs`（新增分类器）、`aidcp-edge/src/electron/main.cjs`
  （状态投影与失败候选改用分类器）。**edge-only，不改协议、不动云端、无 ECS 部署。**
- 回归面：只影响「什么时候把徽标翻红」。核心真崩 / 真启动失败的红仍照常（由退出处权威判据兜底）。
