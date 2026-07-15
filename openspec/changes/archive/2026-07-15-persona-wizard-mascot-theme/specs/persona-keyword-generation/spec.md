## ADDED Requirements

### Requirement: 人设向导使用吉祥物功能色并保留多平台身份

Edge 客户端账号人设向导 SHALL 使用 AIDCP 吉祥物色系建立局部视觉层级：青绿蓝作为通用功能交互色，金黄作为待确认/待更新状态色，珊瑚色可作为小红书平台点缀。选择项文字 SHALL 与区块标题形成可辨层级，MUST NOT 依赖过重字重表达选中状态；选中状态 SHALL 主要由指示器、边框、浅底和文字颜色共同表达。

平台身份与功能交互色 MUST 正交：当前环境为 `xiaohongshu` 时，人设浮层 SHALL 显示“小红书”及其平台点缀；当前环境为 `facebook` 时 SHALL 显示“Facebook”及 Facebook 平台蓝。通用选择、步骤和 CTA MUST NOT 因平台切换而改变功能语义或被写死为单一平台样式。

未选内容项和自定义入口的加号 SHALL 使用不依赖字体字形基线的几何绘制，确保跨 PingFang、Microsoft YaHei、Segoe UI 等系统字体时保持视觉居中。

#### Scenario: Facebook 环境显示平台身份但沿用通用功能色

- **WHEN** 当前环境平台为 `facebook` 且用户打开账号人设向导
- **THEN** 浮层平台标签显示“Facebook”并使用 Facebook 平台蓝，而步骤、选择项和主 CTA 仍使用吉祥物青绿功能色

#### Scenario: 小红书环境显示小红书平台身份

- **WHEN** 当前环境平台为 `xiaohongshu` 且用户打开账号人设向导
- **THEN** 浮层平台标签显示“小红书”并使用珊瑚平台点缀，MUST NOT 残留 Facebook 文案或平台类

#### Scenario: 加号跨字体保持居中

- **WHEN** 未选内容项或自定义入口在任一受支持系统字体栈下渲染
- **THEN** 加号由几何线条居中绘制，不依赖 `+` 字符的字形基线
