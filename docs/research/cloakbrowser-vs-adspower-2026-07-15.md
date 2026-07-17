# CloakBrowser vs AdsPower 指纹浏览器对比（2026-07-15）

> 调研触发：用户问「对比下 cloak 和 ads 指纹浏览器」。本文只做备忘、后续再动工。
> 关联既有分析：`diy-adspower-feasibility`、`adspower-fingerprint-mechanism`（memory）。
> **本仓无 cloak 任何记录**（grep 零命中），以下 cloak 事实来自公开来源、未经本项目真机验证。

## 0. 命名澄清（三个不同东西，勿混）

- **CloakBrowser**（npm `@yingfeilab/cloak-browser`，GitHub ~15k star）：开源、免费、C++ 源码级改核的 Chromium，Playwright drop-in。**这个才是与 AdsPower 同层可比的对象。**
- **Cloak Login**（cloakbrowse.com）：在上面内核外包一层「档案管理 + 免费 profile」的产品化壳。
- **DICloak**（dicloak.com）：另一家独立商业反检测浏览器，与前两者无关。

下文「CloakBrowser」= 第一个。

## 1. 核心对比

| 维度 | CloakBrowser | AdsPower（SunBrowser） |
|---|---|---|
| 反检测路线 | Chromium **C++ 源码补丁**（~49 处），检测 JS 跑前就在内核层伪造 | 改核 Chromium + **读出口叠确定性噪声**（Canvas/Audio）+ WebGL 字符串自定义 |
| 层级 | 内核层（真难那层） | 内核层（闭源私有补丁 `--extended-parameters`=base64 JSON） |
| 开源/费用 | **开源、免费**，npm 直接装 | 商业授权，**按分身/席位收费**（用户所指「贵」在此） |
| CDP/自动化 | **保留 CDP**，Playwright drop-in（改配置即接） | 保留 CDP，本地 API `browser/start`→debug_port |
| 检测通过 | 自称 CreepJS/Pixelscan 30/30、Turnstile 过、reCAPTCHA v3 ≈0.9（**厂商自测，未经本项目真机 XHS/FB 验证**） | 项目已实测过指纹机制，未拿它跑第三方检测分 |
| 代理 | 需自己配（内核开关带代理账密） | **GUI 手工配代理/WebRTC/时区整层托管**——AdsPower 真价值大头 |
| 多账号/团队 | 只有内核 + 薄档案层，**无成熟团队云同步/批量运维** | 成熟分身库、分组、团队协作、批量、台账 |
| 版本维护 | 跟 Chrome 升级靠社区，**滞后=泄漏破绽** | 厂商按分身钉内核版本、自动轮转 |

## 2. 对本项目的判断（接既有铁律）

1. **CloakBrowser ≈ `fingerprint-chromium` 同类**：开源改核、保留 CDP、1:1 接现有 `self` provider 接缝。`diy-adspower-feasibility` 里对 fingerprint-chromium 的诚实代价评估**几乎逐条适用**——检测强度未经真机验证、版本滞后即破绽、`ads-fingerprint.cjs` 约 40% 可搬 60% 要重映射+重探针。

2. **代理面仍是零**：`self` 侧至今无代理代码（`chrome-launcher.ts` 无 `--proxy-server`），AdsPower 真价值有很大一块是「GUI 托管代理/WebRTC/时区」。换 CloakBrowser 省的是**内核授权费**，代理/WebRTC/时区/团队运维**得自己补齐**。**先答铁律：贵的是浏览器还是代理？** 若代理是大头，换内核省不到钱。

3. **风险不对称没变**：内核层对不对，风控接不到真封号信号，**只能离线烧号金丝雀验证**。省=每分身月几毛~1块 OPEX；赔=一批养熟号静默冻可超十年订阅费、几周后才现、无法回滚。CloakBrowser 免费降低了「试」的门槛，**不降低烧号赌注**。

## 3. 务实下一步（若动工）

1~2 周 spike：
- 拿 CloakBrowser 内核起一个真实分身，跑目标站（XHS/FB）+ CreepJS，看它在**本项目真机 GPU** 上的表现（关键：跨机器指纹是否稳、有无软渲染破绽）。
- 量 `ads-fingerprint.cjs` 的重映射工作量（字段是喂 AdsPower 内核的专有指令，换后端要重探针）。
- 量代理面补齐成本（self 侧从零补代理/WebRTC/时区/团队运维）。
- **别为月省几块直接切生产。**

## 来源

- Cloak Login / CloakBrowser: https://cloakbrowse.com/en/
- CloakBrowser 深度拆解（CSDN）: https://blog.csdn.net/Rthan/article/details/161077632
- CloakBrowser 49 C++ 补丁（博客园）: https://www.cnblogs.com/itech/p/20077581
- Best Anti-Detect Browsers 2026（GoLogin）: https://gologin.com/blog/anti-fingerprinting-browser/
- DICloak（独立产品，勿混淆）: https://dicloak.com/
