## ADDED Requirements

### Requirement: Manual Feishu publish approvals route to the triggering conversation

When a publish generation is triggered by a Feishu command event, the generated publish approval card SHALL be sent to the same Feishu conversation that delivered that command when the event provides a source `chatId`. A private-chat `/publish` command SHALL therefore receive its approval card in that private chat, and a group-chat `/publish` command SHALL receive its approval card in that group. Publish triggers without a source conversation SHALL continue to use the configured default approval group.

The system MUST NOT treat a failed approval-card send as a successful delivery. If the source or default target rejects the card send, the system SHALL log the failed delivery and keep the draft in an honest pending state; it MUST NOT claim that the card was sent.

#### Scenario: Private command receives approval card in private chat

- **WHEN** a Feishu private-message command `/publish <nickname>` triggers a publish generation and the event includes `chatId=P`
- **THEN** the publish approval card is sent to `P`
- **AND** the default approval group is not used for that manual command

#### Scenario: Group command receives approval card in triggering group

- **WHEN** a Feishu group-message command `/publish <nickname>` triggers a publish generation and the event includes `chatId=G`
- **THEN** the publish approval card is sent to `G`
- **AND** the default approval group is not used for that manual command

#### Scenario: Non-command publish still uses default approval group

- **WHEN** a publish generation is triggered by an automatic, scheduled, panel/reference, mock, or edge-originated flow without a source Feishu `chatId`
- **THEN** the publish approval card is sent using the existing default approval group resolution

#### Scenario: Approval card send failure is honest

- **WHEN** the chosen Feishu approval target rejects the approval card send
- **THEN** the failure is logged with the request or record context
- **AND** the system MUST NOT report that the approval card was successfully sent
