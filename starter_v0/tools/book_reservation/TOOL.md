---
name: book_reservation
track: bonus
kind: action
provider: none (simulated)
requires_env: []
inputs: [place_name, when, party_size, confirmed]
outputs: [status, confirmation_code]
side_effect: true
requires_confirmation: true
---
# book_reservation

Reserves a table/slot at a place found via `place_search`. This is a
simulated booking (no real reservation backend) meant to demonstrate the
confirm-before-action pattern: it only commits (`status: "reserved"`) when
`confirmed` is true, otherwise it returns `needs_confirmation`.
