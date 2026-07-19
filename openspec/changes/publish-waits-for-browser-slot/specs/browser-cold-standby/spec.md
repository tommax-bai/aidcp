## ADDED Requirements

### Requirement: 任务安全收敛后 SHALL 立即重判最新待机提示

当 Edge 任务租约释放、排队任务为空、在途发布写者已经收敛且普通浏览恢复到安全边界后，核心 SHALL 通知 Electron 外壳重新应用该环境最新的 `browserStandby` 提示。该通知只触发既有待机判定，MUST NOT 直接关闭浏览器或绕过本地开关、最短持有时长、认证/验证码/暂停状态、任务租约和 in-flight 操作安全闸。

#### Scenario: 发布结束且长期无工作时及时归还槽位
- **WHEN** 一次发布任务完成，环境没有下一条租约，最新待机提示仍为 eligible 且所有本地安全闸通过
- **THEN** Edge 无需等待下一次 Cloud 快照即可进入既有冷待机流程，关闭浏览器归还槽位并触发 FIFO 下一环境

#### Scenario: 发布结束但仍有工作时不强制关闭
- **WHEN** 一次发布任务完成，但最新提示不存在、不再 eligible，或环境仍有浏览/点赞工作、下一条租约、验证码/认证阻塞
- **THEN** 重判只产生 no-op 或 skipped，浏览器保持开启，MUST NOT 因“发布结束”被强制驱逐

#### Scenario: 新任务竞态由既有安全闸拦截
- **WHEN** 核心发出安全空闲提示后、Electron 请求待机前又有新任务取得或排队租约
- **THEN** 核心的任务租约安全闸拒绝进入待机，MUST NOT 从新任务底下关闭浏览器
