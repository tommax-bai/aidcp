## Why

`facebook-scheduled-comment` 的 target-URL 定向评论设计已废弃删除（2026-07-11，被 keyword-in-container 版取代）。但它唯一真正落地的 task 2.9——**Facebook 账号昵称经握手持久化**——代码早已上线：edge `6d4cdca`（hello 附带 `accountNickname` + 启动/重连传播）+ cloud `8ab3199`（平台校验通过后、仅账号库内无昵称时写入），2026-07-09 部署 dev。问题是这条已上线行为的需求 spec 只活在那个被删 change 的 delta 里、从未并入主 spec——留着就是「行为在线上跑、主 spec 却不记它」。本 change 把这条已上线契约正式归到它的自然归宿 `facebook-identity` capability 名下。

## What Changes

- 从被删 change 恢复该需求，**剔除已被 `facebook-nickname-inplace-read`（簇 42，edge `ae86cc9`）取代的 `/me` 昵称探针描述**——现网昵称读取已改为**就地、id 锚定、绝不导航 `/me`**（见 `facebook-identity` 现有 4 条读取要求）。改写为与现网一致的 edge→cloud 契约：边缘在数字 id 身份确立后，于 hello 附带**就地读到**的昵称；云端仅在平台校验通过且账号当前无昵称时写入；通用 / 未绑定名忽略；既有昵称不被握手自动覆盖（更正走人工 / 后台）。
- 作为 `## ADDED Requirements` 挂进 `facebook-identity`。**纯 spec 契约补登，无新代码**（实现已上线）。

## Capabilities

### Modified Capabilities

- `facebook-identity`: 在现有 4 条纯边缘读取要求之外，新增一条「昵称经握手持久化」要求，补齐 edge→cloud 传播 + 云端仅库内空时写入的契约。

## Impact

- Affected repos: `aidcp`（本 OpenSpec change，纯文档）。**无 edge / cloud / 协议改动**——实现 2026-07-09 已上线（edge `6d4cdca`，其 `/me` 探针后被 `ae86cc9` 就地读取取代；cloud `8ab3199`）。
- 无部署。归档即把该要求并入 `openspec/specs/facebook-identity/spec.md`。
- 背景：接 `facebook-scheduled-comment` 废弃（2026-07-11）与 `facebook-nickname-inplace-read`（簇 42）。
