## Context

account-real-nickname 把采集挂在 `feed.entered{session_start}`,而 `session_start` 仅由 `startSession`/`restartSession` 发出,且只在 `canStartSession()`(诚实人设闸 + 调度开关)通过后才走到。未绑人设的非 `default` 账号被闸短路 → 无 `session_start` → 采集从不武装。三视角对抗核验(redrive/arming/consistency)确认:生产(未带 auto-start)下绑人设也不重新驱动连接,采集永不触发。

## Decision

把采集从「浏览会话」解耦为「登录引导」,云端编排不变(edge 仍纯执行,守铁律):

1. **采集体永久接线**:`nickname_enricher` 从会话角色集(`restartSession` 订阅的 `roles[]`)移出,在 `setup()` 永久 `subscribe`(独立于会话)。它全程自守(库内已有真名 / 占位账号 / 在途 / 采空退避即 no-op),风控·预算中性 → 永久订阅安全。
2. **本人主页命令出口永久接线**:`self.profile.capture → profile_open{direct}` 从会话期命令翻译移到 `setup()` 永久订阅。授信经 `selfCaptureInFlight` 在软暂停 chokepoint 放行。
3. **登录引导触发**:采集体新增 `armLoginCapture()`,与 `session_start` 路径共用同一 `arm()`(置挂起/在途/超时,命令延到首个 `page.cards` 边缘就绪再发——触发点都在 hello 同步窗口内,边端未登记可推送 + 命令循环未起)。dispatcher 的 hello 入口:`canStartSession` 通过 → `restartSession`(原路径,`session_start` 触发);被人设闸拦下且 `isDispatchActive` → `armLoginCapture()`。
4. **红线**:只接采集相关三件(采集体 + `profile_open` 出口 + 已有的无条件 `page.cards`/`profile.detail` 上报);浏览反应链(contentEvaluator 等)仍只在会话激活订阅。未绑人设账号采完即闲置、不浏览。

## Why edge stays pure / 不回退到 edge 读

account-real-nickname 已确立:真名只在本人主页 DOM 可读,且采集编排(何时采 / 打开哪页 / 判定本人)归云端,edge 仅执行 `profile_open` + 上报 DOM。本改只移动**云端触发点**,不改这一分工(铁律不破)。

## Risks

- 永久订阅采集体 + 永久 `profile_open` 出口:已由 self-guard + chokepoint 授信限定;非采集态零扰动(单测覆盖)。
- 未绑人设账号登录后被驱动一次 `profile_open`:风控中性、不浏览;红线由「不接浏览反应链」保证(dispatcher 单测断言 exactly one `profile_open` + zero browse commands)。
- 采完不主动回 feed(无浏览会话时无返回命令翻译):账号本就闲置,停在本人主页无害,identity-watcher 就地读不依赖页面;不为非运行账号新增返回命令(免引入 browse-ish 指令)。
- 真机门:需重连一个未绑人设(或绑了但未采)的已登录账号,确认登录后采到真名、且全程不浏览。
