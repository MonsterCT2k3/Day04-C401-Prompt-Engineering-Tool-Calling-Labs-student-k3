---
name: clarify
track: core
kind: control
requires_env: []
inputs: [question, response_type, options]
outputs: [question, response_type, options, awaiting_user]
side_effect: false
---
# clarify

Returns a question to the user and pauses until the next user turn.
`response_type` is required. Use `text` for open-ended clarification questions (missing handle, missing URL), and use `yes_no` for confirmation questions. `options` is optional and can be used to provide multiple choice options for the user; if `response_type` is `yes_no`, options will be ignored.
