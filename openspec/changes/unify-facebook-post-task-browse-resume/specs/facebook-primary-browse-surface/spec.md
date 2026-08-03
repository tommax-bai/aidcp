## ADDED Requirements

### Requirement: Pinned primary surface targets every unified browse redrive

Cloud SHALL use the Facebook surface pinned at session start as the `targetSurface` of `page.scroll{reason:'resume_redrive'}`. A task's temporary group/detail page and a later environment configuration write MUST NOT replace that pinned target.

#### Scenario: Reels-primary session finishes a group task

- **WHEN** a Reels-primary session completes its final group/comment page task and the final lease release is acknowledged
- **THEN** Cloud emits one `page.scroll{reason:'resume_redrive', targetSurface:'reels'}`
- **AND** the temporary group page does not become the session's browse target

#### Scenario: Feed-primary session finishes a group task

- **WHEN** a Feed-primary session completes its final group/comment page task and the final lease release is acknowledged
- **THEN** Cloud emits one `page.scroll{reason:'resume_redrive', targetSurface:'feed'}`
- **AND** Edge restores Facebook home before continuing if a temporary group/search page replaced `active_list_url`

#### Scenario: Configuration changes during a task

- **WHEN** the environment primary surface changes while an existing session's task is in flight
- **THEN** the post-task redrive uses the existing session's pinned surface
- **AND** the new configuration applies only to the next session
