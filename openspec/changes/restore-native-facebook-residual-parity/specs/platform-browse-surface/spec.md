## MODIFIED Requirements

### Requirement: Comment migration is receipt-driven and fail-closed

When the comment surface differs from the read surface, the cloud MUST migrate to detail in two receipt-driven steps: emit a navigate-purpose open, wait for its action-completed with a detail-surface observation and matching note id, and only then emit the comment. If the navigate step fails, the cloud MUST NOT emit the comment and MUST report the approved-not-delivered comment to the operator. When the comment surface equals the read surface, migration MUST be structurally unreachable and no extra open is emitted.

The navigate-purpose open MUST carry enough targeting for the executing side to actually navigate without inferring the target from the current page: a canonical target the platform can navigate to (for platforms whose note identity is itself a canonical permalink, that identity suffices) or an explicit address. The cloud MUST NOT rely on a purpose marker alone to change the executing side's behavior.


#### Scenario: Navigate failure does not send the approved comment elsewhere

- **WHEN** the navigate-purpose open for an approved comment fails to land on the target detail
- **THEN** the comment is not emitted on the current page
- **AND** the approved-not-delivered comment is reported to the operator

#### Scenario: Migration command carries a navigable target

- **WHEN** the cloud emits a navigate-purpose open for an approved comment on a platform whose read and comment surfaces differ
- **THEN** the command carries a canonical target the executing side can navigate to
- **AND** the purpose marker is not the only field the executing side would have to honour to reach the right page

> **两段已从本 MODIFY 摘出（2026-08-01，归档前对账）：迁移闩的生命周期，与闩的消费相关性准入。**
>
> 它们对应的工作已于 2026-07-31 **整体摘出本 change**，落到
> `docs/cloud-orchestration-residuals-descoped-2026-07-31.md` 的 A 组（判据只有一条：Rust 迁移
> 碰过它没有 —— 这两条是**云端编排**缺陷，与 Native 迁移无关），**零开工、待正式立项**。
> 任务 6.5 的收窄注释记的就是这件事。
>
> **摘出 ≠ 弃守**：缺陷仍在、立论仍成立（超时清理只武装了免审强制评论那一支；闩的消费没有
> 相关性判据，一条不相干的回执会把它解掉、并把本次迁移的失败归因到别的命令上，审计线索就此毁掉）。
> 只是它换了账本归属。留在这份 delta 里就会把两条**零开工**的 MUST 并进主 spec。
>
> ⚠️ **MODIFY = 整块替换**：本 MODIFY 现在保留的是「主 spec 原有条款 + 可导航目标那一段」
> （后者对应仍在本 change 内的任务 6.1）。将来承接方要把这两段写回规格时，
> **必须连同主 spec 那时的全部条款与 scenario 一起重述**，只写自己新增的那两段会静默删掉其余。
