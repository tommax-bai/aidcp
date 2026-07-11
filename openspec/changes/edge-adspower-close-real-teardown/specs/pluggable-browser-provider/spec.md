## MODIFIED Requirements

### Requirement: AdsPower 提供商经本地 API 托管浏览器生命周期

`adspower` 提供商 SHALL 经 AdsPower 本地 API 完成「启动→取调试端口→等就绪」与「关闭→确认已关」：启动时取回该 profile 的调试端口并轮询至 CDP 就绪后才交付句柄。**关闭 SHALL 以「该 profile 的 CDP 调试端点不再应答」这一独立于 AdsPower 自报状态的权威信号判定浏览器真死**，MUST NOT 把 AdsPower 的「非活跃」自报、或对其本地 API 的任何查询失败当作「已关」。关闭时 SHALL 调用停止接口并在有界轮询内等待该权威端点变暗；停止接口调用失败 MUST NOT 被静默吞掉，SHALL 纳入关闭结论与日志。若软性停止在有界内未使端点变暗，提供商 SHALL **升级**：重发停止，并在可行时对该 profile 内核进程做 OS 级强杀兜底，直至端点实证消失；升级后仍无法确认、或无法取得可靠内核进程句柄时，MUST 如实报告「未确认关闭」而非假装已回收。关闭路径 SHALL 按 profile 重新发起停止并按端点实证判定，MUST NOT 因关闭前 CDP 客户端连接已断开（如暂停驻留期已拆连接）而静默空转、把未死当已关。对本地 API 的调用 SHALL 串行节流以不触发其每秒一次的限速。

#### Scenario: 启动后等就绪再交付
- **WHEN** `adspower` 提供商请求启动某 profile
- **THEN** 它取回该 profile 的调试端口，轮询确认 CDP 端点就绪后才把句柄交给上层附着；未就绪则在超时后诚实报错

#### Scenario: 关闭以权威调试端点实证判定已关
- **WHEN** 上层请求回收该 `adspower` 浏览器
- **THEN** 提供商调用停止接口，并以该 profile 的 CDP 调试端点是否仍应答（`/json/version`）作为真死活判据，仅在端点在有界轮询内变暗时才判为已关

#### Scenario: 查不动或非活跃自报绝不当已关
- **WHEN** 停止后对 AdsPower 本地 API 的查询报错（超时/不可达/非零 code），或 AdsPower 自报该 profile「非活跃」而权威调试端点仍在应答
- **THEN** 提供商 MUST NOT 据此返回「已关」；SHALL 继续在有界内以端点实证重试，上限耗尽仍未变暗则如实返回「未确认关闭」

#### Scenario: 软停止未生效则升级实杀兜底
- **WHEN** 一次软性停止后权威调试端点在有界内仍应答（浏览器仍活）
- **THEN** 提供商 SHALL 升级——重发停止并在可行时对该 profile 内核进程做 OS 级强杀，再确认端点变暗；确认变暗即判已关

#### Scenario: 暂停拆 CDP 后关闭仍按端点实证收敛
- **WHEN** 关闭发生在暂停驻留之后（此前 CDP 客户端连接已被拆除）
- **THEN** 提供商按 profile 重新发起停止并以调试端点实证判定，MUST NOT 因连接已断而静默当作已关；端点仍应答则照常升级直至实证死亡或如实判未确认

#### Scenario: 升级仍无法确认或拿不到内核句柄则诚实未关
- **WHEN** 重发停止与（在可行时的）OS 级强杀均未使端点变暗，或无法取得可靠内核进程句柄以执行强杀
- **THEN** 提供商 MUST 如实报告「未确认关闭」，MUST NOT 假装已回收
