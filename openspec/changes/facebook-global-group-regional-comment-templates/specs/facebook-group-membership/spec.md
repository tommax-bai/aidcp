## MODIFIED Requirements

### Requirement: Targets are lazily claimed under an atomic one-group-one-account lock with orphan reclaim

An account with join budget and no pending assignment SHALL atomically claim the next available unjoined, non-gated target whose explicit scope either is `global` or is `restricted` and contains that account's current non-empty `accounts.group_label`, such that no two accounts can hold the same group. Global scope SHALL allow a Facebook account with any group label or no group label, but MUST still require a present, fresh Facebook account projection. A restricted ungrouped account, an account whose group has no mapped restricted target, or an account whose eligible targets are already globally owned MUST receive no target. A claimed-but-not-joined assignment held by an offline or paused account MUST be released after a bounded idle TTL so it does not permanently lock the target. Global scope and multiple account-group scopes MUST NOT weaken the existing global one-group-one-account uniqueness constraint.

#### Scenario: Concurrent claim of the same global group yields one owner
- **WHEN** two Facebook accounts from different account groups concurrently attempt to claim the same global target
- **THEN** exactly one account holds the assignment and the other receives no row for that target and proceeds only to another eligible target

#### Scenario: Stale assignment is reclaimed
- **WHEN** an account holds an `assigned`/`joining` row that has not progressed past the idle TTL
- **THEN** the assignment is released back to the pool and becomes claimable only by an account still eligible under the target's current global or restricted scope

#### Scenario: Ungrouped account may claim only global target
- **WHEN** a fresh Facebook account has `group_label=null` and requests the next target
- **THEN** it may claim an otherwise eligible `global` target but MUST NOT claim any `restricted` target

#### Scenario: No fallback from restricted scope
- **WHEN** an account belongs to “华东组” but all enabled restricted targets are mapped only to “招聘组”
- **THEN** it receives no restricted target and MUST NOT treat unrelated restricted targets as global

#### Scenario: Stale or non-Facebook projection cannot use global scope
- **WHEN** an account projection is stale, missing, or belongs to a non-Facebook platform while a global target exists
- **THEN** the account receives no target and no membership row is created

### Requirement: 未完成群分配在执行前重新校验账号分组范围

自动加群和裸 `/comment --join` SHALL 在导航或点击前重新读取新鲜账号投影，并确认目标当前为 `global`，或目标为 `restricted` 且仍映射账号当前非空分组。`assigned` 或 `joining` 分配失配时 MUST 以条件写释放该未完成 membership、返回可诊断的范围失配/无目标结果，且不得导航或点击；投影陈旧时 MUST fail-closed 且不得误删合法分配。已记录为 `joined`、`pending`、`gated` 或其它平台/判断终态的 membership MUST 保留真实事实；修改 scope 只影响未来资格，MUST NOT 把已加入伪写为 `left` 或删除。

#### Scenario: 全局分配在账号换组后仍有效
- **WHEN** 账号认领全局群 G 后、导航前改变账号分组或变为未分组，且投影仍新鲜
- **THEN** 分配仍为 eligible，调度器可继续执行其它既有闸

#### Scenario: 受限认领后账号换组则执行前释放
- **WHEN** 账号在认领受限群 G 后、导航前从“华东组”改到“招聘组”，而 G 未映射“招聘组”
- **THEN** scheduler 释放该未完成分配并返回 scope mismatch，不打开 G 的页面、不点击加入

#### Scenario: 移除范围不伪造退群
- **WHEN** 群 G 已为账号 A 记录 `joined`，运营随后把 G 从 global 改为不匹配 A 的 restricted 范围
- **THEN** G 的 joined membership 保持不变；系统不声称 A 已退群，G 只是不再作为未来候选

#### Scenario: 投影陈旧既不放行也不误删
- **WHEN** 执行前账号投影已过新鲜期，无论目标当前为 global 或 restricted
- **THEN** 重验返回具名陈旧结果，不导航、不点击，也不删除现有未完成分配
