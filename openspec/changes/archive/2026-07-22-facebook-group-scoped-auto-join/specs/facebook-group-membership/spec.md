## MODIFIED Requirements

### Requirement: Targets are lazily claimed under an atomic one-group-one-account lock with orphan reclaim

An account with join budget and no pending assignment SHALL atomically claim the next available unjoined, non-gated target whose scope contains that account's current non-empty `accounts.group_label`, such that no two accounts can hold the same group. An ungrouped account, an account whose group has no mapped target, or an account whose mapped targets are already globally owned MUST receive no target and MUST NOT fall back to the global catalog. A claimed-but-not-joined assignment held by an offline or paused account MUST be released after a bounded idle TTL so it does not permanently lock the target. Multiple account-group scopes on one target MUST NOT weaken the existing global one-group-one-account uniqueness constraint.

#### Scenario: Concurrent claim of the same group yields one owner
- **WHEN** two accounts from different mapped account groups attempt to claim the same target concurrently
- **THEN** exactly one account holds the assignment and the other receives no row for that target and proceeds only to another target in its own mapped scope

#### Scenario: Stale assignment is reclaimed
- **WHEN** an account holds an `assigned`/`joining` row that has not progressed past the idle TTL
- **THEN** the assignment is released back to the scoped pool and becomes claimable only by an account whose current group remains mapped to it

#### Scenario: Ungrouped account fails closed
- **WHEN** a Facebook account has `group_label=null` and requests the next target
- **THEN** it receives `no_targets` and no membership row is created, even if the global target catalog contains enabled unassigned groups

#### Scenario: No global fallback for unmapped group
- **WHEN** an account belongs to “华东组” but all enabled targets are mapped only to “招聘组”
- **THEN** it receives `no_targets` and does not claim a target from “招聘组”

## ADDED Requirements

### Requirement: 未完成群分配在执行前重新校验账号分组范围

自动加群和裸 `/comment --join` SHALL 在导航或点击前重新读取账号当前分组并确认目标仍映射该分组。`assigned` 或 `joining` 分配失配时 MUST 以条件写释放该未完成 membership、返回可诊断的范围失配/无目标结果，且不得导航或点击。已记录为 `joined`、`pending`、`gated` 或其它平台/判断终态的 membership MUST 保留真实事实；移除 scope 只影响未来候选，MUST NOT 把已加入伪写为 `left` 或删除。

#### Scenario: 认领后账号换组则执行前释放
- **WHEN** 账号在认领群 G 后、导航前从“华东组”改到“招聘组”，而 G 未映射“招聘组”
- **THEN** scheduler 释放该未完成分配并返回 scope mismatch，不打开 G 的页面、不点击加入

#### Scenario: 移除范围不伪造退群
- **WHEN** 群 G 已为账号 A 记录 `joined`，运营随后从 G 移除 A 当前分组的 scope
- **THEN** G 的 joined membership 保持不变；系统不声称 A 已退群，G 只是不再作为未来候选

