# Tasks - publish-image-postgen-safety-validation

> 落地仓预计为 **aidcp-cloud**。本 change 是从 `category-adaptive-images-and-judgment` 拆出的未决能力：必须真实看生成图，不能用占位规则或 prompt 字符串判断冒充产后校验。

## 1. 方案与模型接入

- [ ] 1.1 选定视觉 / 多模态判定模型与调用通道，明确成本、超时、并发与失败语义。
- [ ] 1.2 定义视觉校验输出类型与审计字段：`pass | reject | unavailable`、reasons、provider、checkedAt。
- [ ] 1.3 明确高风险触发条件：人物 / 人脸 / 局部人体 / 背影 / POV / 封面文字 / prompt 含 text 等。

## 2. 云端实现

- [ ] 2.1 在配图生成成功 URL 写入 `imageDirective` 前接入视觉校验步骤。
- [ ] 2.2 `reject` 时丢弃该张并按受控次数重生成；仍失败则沿用既有部分成功 / 全失败诚实语义。
- [ ] 2.3 `unavailable` / 超时 / 非法响应必须如实记录，MUST NOT 标成视觉校验通过。
- [ ] 2.4 审计日志与发布记录展示“已校验 / 未校验 / 被拒原因”，不暴露原始敏感模型输出。

## 3. 验证与收尾

- [ ] 3.1 单测覆盖 reject、unavailable、部分成功、全失败、重试上限。
- [ ] 3.2 acceptance / typecheck 按 aidcp-cloud 规范通过。
- [ ] 3.3 部署 dev 后用真实生成图验证：含疑似真人、含乱码文字、低风险 no-text/no-people 三类样本。
- [ ] 3.4 `openspec validate publish-image-postgen-safety-validation --strict` 通过后归档。
