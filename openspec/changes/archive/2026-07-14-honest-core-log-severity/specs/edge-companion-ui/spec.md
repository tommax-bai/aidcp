## ADDED Requirements

### Requirement: 核心日志的严重级别按内容判定，不得按输出通道判定

桌面客户端 MUST 依据核心进程日志行的**内容**判定其严重级别，MUST NOT 依据该行走的是 stdout 还是 stderr 来判定。

理由：Node 的 `console.warn` / `console.error` 一律写 stderr，因而「这行走了 stderr」只是一个**传输事实**，不承载「出错了」这个**语义断言**。核心里绝大多数写 stderr 的行是良性的诊断、进度与排队说明。

- 边缘进程徽标 MUST 仅在该行被判为 `fatal`（真失败形状）时翻成异常态；被判为 `warn` / `info` 的行 MUST NOT 使边缘进程徽标离开 `running`，MUST NOT 使该环境获得「需处理」角标或被排到环境栏顶部。
- 失败归因候选（核心异常退出时呈现给运营的那条「失败原因」）MUST 只由 `fatal` 行填充。良性 stderr 行 MUST NOT 覆盖它。
- 严重级别分类器 MUST 是可单测的纯函数（不依赖 Electron / 进程 / 文件系统）。
- **不吞真失败**：分类器 MUST 把既有失败签名（启动失败 / 不可达 / `not allowed` / `being used` / `no_target` / `code=-N`）与常见运行时异常形状（`Error:` / `TypeError` / `ECONNREFUSED` / `unhandled` / `FATAL` 等）判为 `fatal`。
- **权威判据不变**：核心真正异常退出时的失败呈现 MUST 继续由退出处（退出码 / 信号）权威判定，不受本分类器影响。日志行分类只是**预测**，退出码才是**权威**。
- 日志**文件**（排障回溯用）MUST 继续按真实输出通道记录（stderr 行仍带 `ERR` 标记）——传输事实要如实留痕，只是不再被误读成语义。

#### Scenario: 良性排队说明不再被讲成运行异常

- **WHEN** 核心因浏览器槽位排队而向 stderr 打印「外壳暂时给不出浏览器槽位（…）：本次诚实作答，环境仍在等槽位队列里」
- **THEN** 该环境的边缘进程徽标保持 `running`，环境栏 MUST NOT 显示「异常」、MUST NOT 加「需处理」角标、MUST NOT 把该环境浮到列表顶部，在场文案 MUST NOT 出现「引擎已停止」

#### Scenario: 发布期诊断日志不再闪红

- **WHEN** 一次发布过程中核心向 stderr 打印租约抑制说明与 `[publish-submit-diag]` 诊断行
- **THEN** 该环境徽标全程不翻红、不出现「闪红又秒恢复」，健康结论保持「运行中」

#### Scenario: 真启动失败仍如实翻红

- **WHEN** 核心打印一条真失败行（如 AdsPower `browser/start` 启动失败、`not allowed to open`、`code=-1`）
- **THEN** 边缘进程徽标翻成异常态，该行被记为失败归因候选

#### Scenario: 核心异常退出时归因是真失败行而非最后一条良性 warn

- **WHEN** 核心先打印若干良性 stderr 行（诊断 / 排队说明），随后打印一条真失败行，再异常退出
- **THEN** 呈现给运营的「失败原因」是那条真失败行，MUST NOT 是任何一条良性 stderr 行

#### Scenario: 未识别的良性 stderr 行不被默认判死

- **WHEN** 核心向 stderr 打印一条既不匹配失败签名、也不匹配运行时异常形状的行
- **THEN** 边缘进程徽标 MUST NOT 因此翻红；若核心确实随后异常退出，红仍由退出处权威判据给出
