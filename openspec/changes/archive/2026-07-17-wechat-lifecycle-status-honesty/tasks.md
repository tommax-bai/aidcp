# Tasks

## 1. aidcp-edge — 作用域校验口径与真态应用

- [x] 1.1 `interaction-workspace.js` 的 `changeLifecycle`：把回包作用域校验从云端环境键改为**本机运行时 ID**，与发送侧同口径；确认校验通过后 `onLifecycleStatus(next)` 能真正执行（现状是守卫在其之前抛出，真态永不被应用）。
  <!-- repo=aidcp-edge commit=d24bb89 validation=修前先让新断言复现用户原文案「暂停失败：这条互动已不可用，或不属于当前环境。」，修后转绿 deploy=n/a deviation=none -->
- [x] 1.2 同函数：移除本机运行时 ID 缺失时回落成云端环境键的兜底，改为诚实拒绝该次动作；理由是回落会让主进程查表落空并静默作用于当前选中的**另一个**环境。
  <!-- repo=aidcp-edge commit=d24bb89 validation=新增「标识缺失 MUST NOT 发请求」用例通过 deploy=n/a deviation=none -->
- [x] 1.3 给两处口径相反的作用域守卫（本机回包 vs 云端回包）各补一行注释写清各自基准，避免下一个改动者再改错一侧。
  <!-- repo=aidcp-edge commit=d24bb89 validation=两处守卫各注明基准并互相点名 deploy=n/a deviation=none -->

<!-- 说明：本 change 只改 renderer 一个函数 + 其测试，未新增/改动协议、云端、风控与发布链，故无需 §2 协议四处同步与 AC-PROTO/AC-PUB/AC-RISK 之外的额外闸；红线全量已随 test:acceptance 23/23 覆盖。 -->

## 2. aidcp-edge — 拆掉夹具致盲、钉住回归

- [x] 2.1 `test/electron/interaction-workspace.test.ts`：夹具改用主进程真实造得出的标识形状（云端环境键 = 裸分身 ID，本机运行时 ID = `ads-<分身ID>`），不得两者同值——现夹具正因同值而构造性致盲。
  <!-- repo=aidcp-edge commit=d24bb89 validation=偏离说明见下 deploy=n/a deviation=生命周期用例的夹具本就已是真实形状（envId=ads-k1eoujd8 / profileId=k1eoujd8），无需改；致盲点不在夹具形状而在断言只覆盖发送侧，故实际修的是 2.2。boot() 默认夹具仍两口径同值，但它不走生命周期路径，本次不动以免扰动其余 31 个用例。 -->
- [x] 2.2 生命周期用例补断言：动作成功后提示为成功文案、且回包真态被下游消费（`onLifecycleStatus` 被调用），不只断言发送侧参数。此断言在修复前 MUST 失败（先确认它真的红，再修）。
  <!-- repo=aidcp-edge commit=d24bb89 validation=修前实跑为红且 actual 逐字等于用户上报文案；断言落在 #iw-sync-status（生命周期提示的真实渲染位，非 .iw-action-notice——后者只在回复详情面板内） deploy=n/a deviation=未直接 spy onLifecycleStatus（renderer 接线固定、无注入点），改断言用户可见结论，等价且更贴红线 -->
- [x] 2.3 补一条「本机运行时 ID 缺失 → 拒绝、不向本机通道发请求」的用例。
  <!-- repo=aidcp-edge commit=d24bb89 validation=新用例通过 deploy=n/a deviation=none -->
- [x] 2.4 跑 `npm test` 全量 + `npm run typecheck`。
  <!-- repo=aidcp-edge commit=d24bb89 validation=全量 1685/1685、test:acceptance 23/23、typecheck 退出码 0（未用管道，避开 tail 吞退出码） deploy=n/a deviation=none -->

## 3. 真机验收（登记 backlog，不阻塞归档）

- [x] 3.1 真机跑一次 AdsPower 视频号环境的 启动 / 恢复 / 暂停 / 关闭 全矩阵，确认界面呈现成功且状态即时刷新（不必等下一次心跳）。建议并入视频号既有真机簇，不新开。
  <!-- repo=aidcp commit=23157ce validation=已登记 docs/real-machine-acceptance-backlog.md 簇 99（4 项：四动作不谎报 / 状态即时刷新 / 只作用目标环境 / 真失败仍报失败） deploy=n/a deviation=另起簇 99 而非并入既有视频号簇——既有簇 87/98 的前置环境是「已登录且有历史互动的环境」，本簇只需 AdsPower 分身且**必须避开 self 环境**（self 下两标识同值、守卫不误伤 ⇒ 拿 self 验会假绿），前置条件不同故未合并 -->

## 备注：与其他 change 的关系（不阻塞本 change）

- 能力归属：控件本身属 `wechat-channels-interaction-management`（其未合并 delta 的生命周期条款被本回归直接违反）。
- 回归引入方：`wechat-channels-browser-foreground-control` 的任务 5.5（`09bf813`）。该 change 只剩归档一步。**若它先归档而本修复未落，回归的「因」进 archive、「果」仍活在主干，日后对账只能靠全文 grep sha 才接得回来。**
- 上述两个 change 的 worktree 当前均被其他 session 占用，故本修复不动它们的分支与 delta。
- 另需留意（本 change 不处理）：`wechat-channels-interaction-management` 未合并 delta 里「本机 lifecycle IPC 携当前 envKey」的措辞已被 `09bf813` 的正确 ID 拆分证伪，照原样归档会把一句错的话并入主 spec。应由该 change 的持有者订正。
