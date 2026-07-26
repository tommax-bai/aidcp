## ADDED Requirements

### Requirement: AdsPower profile 占用拒绝必须结构化且脱敏

AdsPower provider 在 `browser-profile/start` 明确返回目标 profile 被其他邮箱或设备占用、禁止打开时，SHALL 把该结果分类为稳定的 profile 占用错误，MUST NOT 压成无类型内部错误、MUST NOT 回落 self provider、MUST NOT 自动停止或抢占占用方浏览器。原始占用邮箱 MUST NOT 出现在异常 message、Cloud payload 或客户 API；Edge 本地诊断只 MAY 记录脱敏 owner hint。

#### Scenario: 已验证的占用拒绝被窄分类

- **WHEN** `browser-profile/start` 返回非零 code，且 message 符合已验证的 “profile is being used by owner and is not allowed to open” 形状
- **THEN** provider SHALL 抛出稳定的 profile 占用错误并保留目标 profile id
- **AND** 错误与安全日志 MUST NOT 包含原始 owner 字符串，只能包含脱敏提示
- **AND** provider MUST NOT 回落 self、重发 stop 或宣称浏览器已启动

#### Scenario: 非占用启动失败不被误分类

- **WHEN** `browser-profile/start` 因 profile 不存在、内核未就绪、网络错误或未知 message 失败
- **THEN** provider SHALL 保持既有诚实失败路径
- **AND** MUST NOT 把该失败标成 profile 被占用
