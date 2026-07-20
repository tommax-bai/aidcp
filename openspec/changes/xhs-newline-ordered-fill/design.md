## Context

小红书发布正文是 `.tiptap.ProseMirror` contenteditable。当前 `typeHumanized` 先按全文长度求统一块长，再直接切字符串；因此一个 `Input.insertText` 可能同时包含 `\n` 与其后的正文。实机记录 #153 的所有错序块均跨越换行：ProseMirror 把换行解释为段落结构事务，稍后的 selection 归一把光标放回该块尾字之前，下一块遂插到尾字前，尾字逐块倒序积累到文末。

当前最终回读能在中文也错序时 fail closed，但它发生在整篇输入完成之后，只能阻止提交，不能避免错误填写；测试 fake 也只同步追加字符串，无法覆盖换行后的 selection 回退。

## Goals / Non-Goals

**Goals:**

- 保证小红书正文的任何 `Input.insertText` 参数都不含 CR/LF。
- 用真实 Enter 表达每一个正文换行，并在继续输入前确认段落结构数、已有前缀和末端 selection 均已稳定。
- 保留拟人化总停顿预算、抢占清场和最终全文后置校验；确认失败时绝不继续提交。
- 用可复现 selection 回退的 fake 覆盖多段、连续空行与尾字倒序积累回归。

**Non-Goals:**

- 不修改 Cloud 指令编排、协议、审批内容、标题/话题输入或小红书发布元数据。
- 不以固定延迟替代状态确认，不放宽最终后置校验，也不构建桌面安装包。
- 不在本 change 重定义小红书对 URL、emoji、Markdown 的平台级富文本改写规则。

## Decisions

### 1. 换行成为独立输入单元

正文先把 `CRLF`/裸 `CR` 归一为语义等价的 `LF`，再构造成普通文本块与 newline 两类单元。普通文本仍按全篇非换行字符数计算统一块长，保持 `Input.insertText` 往返数有界；newline 单元只派发一次真实 Enter。这样同一次浏览器输入事件不再同时承担“拆段落”和“写新段文字”。

备选的“继续整块输入但加长 sleep”被拒绝：冲突发生在含换行的单次编辑器事务内部，固定等待既没有验收条件，也无法保证不同机器/正文长度下稳定。

### 2. Enter 后以状态而非命令 ACK 推进

每次 Enter 后进行有界轮询。探针同时读取当前正文、统计顶层段落/`br` 所表达的换行数，并检查 selection 是否折叠在编辑器末端；若光标不在末端则显式把 Range collapse 到末端。只有“段落结构数达到截至当前 Enter 的预期”“已写前缀仍可回读”且“连续两次观察都位于末端”才允许输入下一单元。这样即使页面吞掉 Enter 而光标仍在末端，也不会误判为成功。

中文正文沿用现有 Hanzi 序列口径确认已写前缀，避免 URL/emoji 的平台自动改写造成假失败；无汉字正文回退归一化全文前缀。整篇完成后仍走既有最终回读与污染阈值，单次 Enter 确认不替代最终验收。

### 3. 失败沿用现有清场与诚实结果

段落/光标无法在有界窗口内稳定时抛出明确的 `content_newline_unstable` 输入错误，由 `runFillField` 既有异常分支执行整字段清场并返回 `ok:false`。抢占仍只发生在下一个页面写入前；一旦某单元已写入，失败或抢占都不得留下半篇正文。

### 4. 测试模拟真实的 selection 回退

Fake CDP 增加光标位置与 Enter 建段建模：若旧路径把换行与后续文字一起交给 `Input.insertText`，fake 会让光标回退到该块尾部之前，从而复现尾字倒序积累；新路径必须表现为纯文本 insert 与 Enter 事件交替，并在 Enter 后通过段落数/末端校准恢复顺序。测试同时断言连续空行数量、最终文本顺序、Enter 被吞时失败清场和所有 `Input.insertText` 参数不含换行。

## Risks / Trade-offs

- [真实 Enter 可能触发编辑器特有输入规则] → 复用已在 Edge 使用的 CDP `dispatchKey`，并以段落/selection 状态确认而非假定成功。
- [逐换行确认增加耗时] → 普通文字仍按全篇 50 次发送目标计算统一块长，并与 newline 单元共享 12 秒总停顿预算；确认轮询短且有界，长正文最终仍受现有 30 秒 Cloud 等待与失败清场保护。
- [Hanzi 前缀口径忽略纯 ASCII 局部变化] → 本 change 先消除换行导致的结构错序，最终全文校验保持现有兼容边界；更严格的富文本等价规则另行演进。

## Migration Plan

1. 在 Edge 隔离 worktree 实现并通过聚焦测试、完整测试和 typecheck。
2. 集成到 `aidcp-edge/master` 后由当前 dev 源码客户端重启加载；不需要 Cloud/Console 部署或数据迁移。
3. 若新路径在 dev 实机返回 `content_newline_unstable`，发布会停在提交前并清场；回滚只需回退 Edge 提交，不涉及服务端或数据库。

## Open Questions

无。若后续实机证明某种小红书布局不接受裸 Enter，将另开变更校准该布局的段落原语，而不是在本 change 内回退到含换行的 `Input.insertText`。
