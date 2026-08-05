## Why

Facebook 首登的「凭据已填好」判据是**两个输入框都非空**，而指纹浏览器的凭据是**逐字符模拟人手敲进去的**（实测：表单第 ~10.7s 出现，邮箱 26–27 字符敲约 4s，密码第 ~15.2s 才开始、约每秒 5 字符）。协调器每 500ms 探一拍，于是密码出现第一个字符的下一拍就被判成「填完了」并点提交——**提交上去的是密码的前 1–2 位**。

2026-08-05 在三个环境上实测复现（真引擎 + 真协调器 + 真预算）：

| 环境 | 结果 |
| --- | --- |
| `k1fd38uh` | 判定就绪时密码只有 1–2/15 位 → 点击后 Facebook 回「The password you entered is incorrect」；点击抢走焦点，指纹浏览器停在第 5 位不再往下打 |
| `k1fd398b` | 同样提交半截密码，随后第二次点击后置校验拿不到确认 → `auth_postcondition_unconfirmed` 终局失败 |
| `k1fd395p` | 密码敲到第 6 位时 Facebook 重绘登录区把两个框清空，之后无人重打 → 25s 宽限期到点，报 `credential_fill_unavailable` |

这不是偶发竞态而是**几乎必中**：密码从空变非空到被抓拍最多半秒。运营侧已按现象把 9 个环境改名成 `password`、2 个 `checkpoint`、1 个 `locked`——每启动一次就向 Facebook 递一次错密码，重复错密码正是账号被 checkpoint / 锁定的常规诱因。

点击前那道复核救不了：信号指纹算的是**按钮**的 DOM 路径 / 角色 / 几何 / 文档代次，**不含输入框内容**，所以密码从 2 位涨到 4 位仍被认作「同一个信号」。

另外 25s 凭据宽限期**只管「空」的那条分支**，且从**文档开始加载**起算——而表单第 10.7s 才出现、密码第 15.2s 才开始敲，实际只剩约 10s 余量。代理慢一点就会在敲完之前先判「凭据不可用」。

## What Changes

- **就绪判据从「非空」改成「稳定」**：两个凭据框的内容需连续观测保持不变达到一个具名安定窗口，才允许发出 `login_submit_ready`。内容仍在变化时一律回 `credential_fill_pending`，不得判成就绪。
- **信号指纹纳入凭据填充状态**：`login_submit_ready` 的 signal id 除现有按钮证据外，还绑定两个输入框内容的**长度**（只用长度，绝不取内容、绝不外传字符）。点击前的 fresh-revalidate 因此能发现「我准备点的这段时间里密码又长了」，当场作废重来，而不是照点。
- **凭据宽限期改起算点并加长**：从「文档加载」改为「登录表单首次被观测到」起算，并延长到足以容纳整段逐字符输入 + 代理慢的余量；安定窗口的等待计入同一预算。
- **BREAKING**：无。对已登录（无登录表单）的环境行为不变；对未登录环境只是把「提交半截密码」换成「等它敲完再提交」。

## Capabilities

### New Capabilities

无。本变更收紧的是既有 Facebook 首登能力的判据，不引入新能力。

### Modified Capabilities

- `facebook-browser-environment`: 两条要求改判据——① 「Facebook first-login assistance reconciles one independent signal at a time」下的登录提交场景，从「确认两个框非空」改为「确认两个框已安定」，并要求 signal id 绑定凭据填充状态；② 「Unavailable Facebook credential fill SHALL preserve a controlled manual-login session」的宽限期改为从表单出现起算并加长。

## Impact

- `aidcp-edge/native/page-engine/src/facebook-router/06-auth.js`：`authLoginObservation` 的就绪分支、`authObservation` 的指纹构造、`facebookAuthCredentialFillGraceMs` 的语义与取值；`authPostcondition` 中 `login_submit_ready` 分支需与新指纹一致。
- `aidcp-edge/native/page-engine/src/facebook/auth.rs`：`FacebookAuthSubmitLogin` 走 `execute_click`，其 action-time 复核依赖 signal id，指纹变更后需确认拒绝路径仍如实回报（不静默改判）。
- `aidcp-edge/native/page-engine/tests/facebook_auth.rs` 与 `aidcp-edge/test/native-page-engine/facebook-auth*.test.ts`：新增安定窗口与指纹失配的守护用例。
- 无协议消息变更、无云端改动、无 console 改动。`credential_fill_pending` / `credential_fill_unavailable` 两个原因值保持不变，客户端文案与失败归因不受影响。
