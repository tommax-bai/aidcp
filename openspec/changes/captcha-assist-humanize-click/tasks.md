## 1. aidcp-edge — 点击原语拟人化缝

- [ ] 1.1 `browse/cdp-util.ts`：`DispatchClickOptions` 增 `hoverDwellMs?: number`（move 到位后、press 前的读图/瞄准停顿，默认 0，普通浏览零影响）；`dispatchClick` 在 `dispatchHover` 返回落点后、press 前，若 `hoverDwellMs>0` 用可注入 sleep 停一段。
- [ ] 1.2 `browse/cdp-util.ts`：`dispatchClick` 返回真实落点（如 `dispatchHover` 那样返回末点），供多点循环把上一真实落点作下一点 `from`（修光标连续性；顺带在 `feed-scroller` 注释澄清 `lastCursor` 为意图坐标近似或一并修）。
- [ ] 1.3 逐帧移动延迟改为带抖动（`dispatchHover` 每帧 `moveDelayMs` 叠轻量对数正态/`jitterAround`），消除 `dt` 方差为 0。

## 2. aidcp-edge — 协助注入循环

- [ ] 2.1 `browse/captcha-assist.ts`：`CaptchaAssistHandlerDeps` 增可注入 `random?`，构造函数默认 `humanize` 的 `defaultRandom`，供路径与停顿共用。
- [ ] 2.2 定义 `CAPTCHA_CLICK_PACING`（jitter、overshootProb、moveDelay 抖动档、hoverDwell 与 interPoint 两档对数正态 `TimingConfig`），中心值叠 `edgeId` 派生每机偏置；集中一处、留 env 覆盖缝但先不做旋钮（YAGNI）。
- [ ] 2.3 `handleClick` 循环重写：track `cursor`（上一点真实落点）；每点 `opts={from:cursor, jitter, overshoot:random()<prob, moveDelayMs(带抖), hoverDwellMs:sampleDelay(hoverDwell), random, sleep}`；点间用 `sampleDelay(interPoint)` 替换固定 `sleep(220)`，仅非末点后停。
- [ ] 2.4 `settle → reprobe → cleared/still_blocked/failed/回传新截图` 整段保持不变（红线：不静默假成功；只有真实清除才 `sendRiskCleared`）。
- [ ] 2.5 给 `handleClick` 总耗时一个显式上界（或在文档声明依赖 console 落点数上限），防未来放开点数后长尾逼近 idle 看门狗窗口。

## 3. aidcp-edge — 测试

- [ ] 3.1 现有 click 用例注入确定性 `random`（使 jitter=0、关 overshoot），保精确落点断言仍成立。
- [ ] 3.2 新增回归：多点用例断言 (a) `mousePressed` 次数 === points 数；(b) 存在 `mouseMoved`（轨迹非瞬移）；(c) 点间停顿按记录到的**时长值**区分 interPoint 与逐帧 moveDelay（不只数调用次数）。
- [ ] 3.3 补一条**真实（非退化恒定）随机源**下 press 落点落在 `target±jitter` 容差内的断言，避免只测退化点。
- [ ] 3.4 honest-result（still_blocked 回传新截图 / failed）用例保持并确认不受拟人化影响。

## 4. 验证与集成

- [ ] 4.1 `cd ../aidcp-edge && npm run typecheck && npm test`（协议未动，AC-PROTO-* 不受影响，仍全量跑）。
- [ ] 4.2 edge land 到 master、tasks.md 回写 sha；edge-only 无 ECS cloud 部署，真机核在运营机 pull 后生效。
- [ ] 4.3 登记真机验收 backlog：协助点击拟人度肉眼观察 + 是否降低验证码复现/被拒。
- [ ] 4.4 `openspec validate captcha-assist-humanize-click --strict` 通过。
