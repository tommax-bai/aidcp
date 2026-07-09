# Loosen 一码一号 for group-comment enable: shared code → allow + warn

## Why

自动群评（`PUT /api/content-schedule/:accountId` 的 `groupCommentEnabled=true`）此前对「该账号群码与任一其它账号 verbatim 相同」做**硬阻断**（具名拒 `shared_group_code`、整块不落库、MUST NOT 以警告放行）。这是防关联封号的最强指纹拦截。

运营明确要求放松此开关限制：允许多账号共用同一群引流码时也能开启自动群评。经确认放松档位为「**共用可开 + 提示**」——共用群码放行、但保存时如实弹一条防关联风险提示；「**无码**」仍硬拒（没配码开开关无意义）。这是运营在知情前提下的风险取舍：放松会提高多号被平台关联/封号的风险，靠小日上限 + 错峰 + 人审 + 明示提示压制，诚实声明非零风险。

## What Changes

- **cloud** `ContentScheduleStore.setAccount`：`groupCommentEnabled=true` 且群码与其它账号共用时，不再 `return {ok:false, reason:'shared_group_code'}`，改为置 `sharedGroupCodeWarning` 后照常放行落库。`no_group_code` 仍硬拒。成功结果新增可选 `sharedGroupCodeWarning`，失败 union 去掉 `shared_group_code`。
- **cloud** `panel-server` `PUT /api/content-schedule/:accountId`：成功响应透传 `sharedGroupCodeWarning`（绝不静默把关联风险咽下去）。
- **console** `ContentSchedulePage`：`patchAccount` 响应带 `sharedGroupCodeWarning?`；新增 `onSuccess` 在其为真时弹一条防关联风险 `message.warning`（非错误、非阻断）。`errorText` 去掉 `shared_group_code` 映射（已非 error）、保留 `no_group_code`。
- **触发端不变**：命令式评论机器的群码闸只对**缺码** fail-closed（`comment-scheduler`），从不校验「共用」——放行后共用群码账号的群评能真跑，非静默空转。

## Impact

- Affected specs: `console-write-operations`（写通道硬校验）、`content-schedule`（群评刹车描述）、`group-chat-injection`（排期侧刹车列举）。
- Affected code: `aidcp-cloud/src/config/content-schedule-store.ts`、`aidcp-cloud/src/panel/panel-server.ts`、`aidcp-console/src/pages/ContentSchedulePage.tsx`、`aidcp-console/src/api/errorText.ts`。
- **风险取舍（明示）**：共用群码是最强的跨账号关联指纹，放松后关联/封号风险上升；由运营知情决策，前端提示 + 小日上限 + 错峰 + 人审为压制手段。
- **协调**：与 pending change `generalize-contact-info-change`（将把 `group_chat_info`→联系方式泛化、物理重命名列/wire 键、群评一并正名）同区域，二者合入需相互 rebase 携带本放松语义。
