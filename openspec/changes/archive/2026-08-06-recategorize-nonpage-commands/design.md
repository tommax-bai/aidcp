## Context

判例四的根治批。前置已齐：语法规格已归档（类别按编址单位）、留痕维已上线（close-account-layer-operation-manual 已落 master）、救援清单已有断言护着（改动它测试会响）。

## Goals / Non-Goals

**Goals:** 七条改类、救援补丁摘除、平台段闸落地（休眠态）、身份闸判据收敛为零例外。
**Non-Goals:** 不动协议、不改任何命令名（批 4/5）、不动 Rust 引擎、不实装观察命令（批 3 并行中）。

## Decisions

### 决策一：身份闸的新判据＝纯身份维，零例外清单

改类后判据收敛为一句话：**身份未落定时，拒绝一切 `identity: 'page_account'` 的命令**。

关键裁定：**`edge.task.acquire` 保持 `page_account`**。它不留痕（留痕维 `none` 不变），但「持有租约」就是「以该账号名义动作的准入」——身份都不知道是谁，谈不上以谁的名义认领。这正是「留痕维 MUST NOT 单独决定放行」那条反例的机械落点：留痕 `none` + 身份 `page_account` 并存，各答各的问题。

七条改类前后的行为对照（身份未落定时）：

| 命令 | 旧机制 | 新机制 | 结果 |
| --- | --- | --- | --- |
| `identity.read_current` / `read_self_profile` | 类别拦 → 救援清单放 | `page_observation` 不拦 | 不变（放行） |
| `captcha.assist.capture` / `.click` | 同上 | `environment_assist` 不拦 | 不变（放行） |
| `edge.task.release` / `session.end` | 同上 | 身份维非 page_account 不拦 | 不变（放行） |
| `edge.task.acquire` | 类别拦（不在清单） | 身份维仍 `page_account` → 拦 | 不变（拒绝） |

**七条全部结果不变、机制换血**——这是「不出包也安全」的依据：新旧两套判据对同一输入给同一结论。

### 决策二：类别扩容的边界

只加真实在编址上不同的两类：`page_observation`（翻译层观察：读页面得出「登着谁 / 在哪」，需浏览器、不产生账号动作）、`environment_assist`（环境层处置：验证码协助）。`edge.task.*` / `session.end` 不新造「编排类」——它们归入既有 `automation_control`（编排控制本就是这一类的语义），只改身份维。**防笛卡尔积：不为「将来可能有」预留类别。**

### 决策三：平台段闸先落后名

闸的判据：命令名首段 ∈ 平台枚举（取自代码平台标识）⇒ 必须等于该会话账号的平台；无平台段 ⇒ 放行走原逻辑。当前 43 条无一带平台段 ⇒ 闸休眠。**为什么现在落**：批 4 改名时若无闸，第一条 `facebook.*` 命令下发时没有任何东西校验它发对了平台——先有闸再有名。变异测试证明闸醒着：构造一条带平台段的假命令 + 平台不符的账号 ⇒ 必须拒绝。

### 决策四：救援清单断言的去向

close-account 刚加的断言（清单 ⊆ 不留痕）随清单一起退役,改写为结构等价的新断言：**身份未落定时被拦集合 ＝ { identity: 'page_account' } 的登记集合**（按引用推导，零手抄），且该集合 MUST 含全部留痕命令 + acquire。变异：把 `interaction.comment` 的身份维改掉 ⇒ 断言红。

## Risks / Trade-offs

- **[改类破坏冷待机唤醒逻辑]**（main.ts 按 browser 维决定唤醒）→ 七条的 browser 维一律不动，只动 category / identity。
- **[automation 侧类别联合类型与 edge 漂移]** → 对表闸已比全部字段，落地即验。
- **[闸休眠被误以为生效]** → 测试注释明写「当前词汇无平台段命令，本闸休眠至批 4」；变异测试是它活着的唯一证明。
