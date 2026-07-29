# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Xong trước 11:30 để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. Có thể hoàn thiện sau buổi debate để nộp bài.

## Team

- Team:
- Members:
- Provider/model:

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> 1–2 câu mô tả agent dùng để làm gì.

Ví dụ: "Research agent: tìm tin theo từ khóa / theo tài khoản, đọc URL và tổng hợp thành digest."

**Link dùng thử (truy cập được trong showdown):**

> Dán public URL nếu người khác cần mở từ máy riêng; localhost cũng được nếu demo trực tiếp trên máy trình chiếu. Streamlit được khuyến nghị, nhưng nhóm có thể dùng bất kỳ framework nào.
>
> URL:

## A2. Tool agent có

> Liệt kê các tool agent đang dùng. Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin | không |
|  |  |  |
|  |  |  |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1.
2.
3.

## A4. Kịch bản demo đã rehearse

> Chuẩn bị 3–5 scenario. Mỗi scenario cần cho thấy tool đã làm gì và một thay đổi cụ thể giữa các version.

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
|  |  |  |  |

---

# PHẦN B — Chi tiết / Bằng chứng

> Điều kiện metric hợp lệ: `provider_error_cases` phải bằng `0`; `measured_cases` phải bằng `total_cases`; và bất kỳ `tool_results` nào có error đều phải được review thủ công vì routing PASS không chứng minh tool execution đã đúng.

## B1. Version evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | Baseline run; no prompt/tool changes yet | Baseline shows the agent guesses missing handle and uses tools too eagerly | case_accuracy | 0.65 | 0.80 | v0_B_base_openai_20260729T101321700753.json |
| v1 | system_prompt.md: stronger routing rules for tweet questions and no guessing when handle is missing | Clearer routing rules should reduce wrong-tool and missing-info errors | case_accuracy | 0.80 | 0.85 | v1_B_base_openai_20260729T103729522319.json |
| v2 | system_prompt.md: distinguish “tweet of a person” vs “topic search” | Better prompt separation should improve routing and argument correctness | case_accuracy | 0.80 | 0.85 | v2_B_base_openai_20260729T104135763829.json |
| v3 | clarify/TOOL.md: require response_type=text for clarification requests | Explicit tool contract should fix missing-info cases | case_accuracy | 0.85 | 0.85 | v3_B_base_openai_20260729T104455083636.json |
| v4 | system_prompt.md: clarify-before-action and no guessing when information is missing | Clarification-first behavior should reduce argument mistakes and boundary errors | case_accuracy | 0.85 | 0.90 | v4_B_base_openai_20260729T105329489158.json |
| v5 | lookup/TOOL.md: use topic=news and avoid putting “news” into the query | Cleaner lookup args should make news lookup and parallel tool use pass end-to-end | case_accuracy | 0.90 | 1.00 | v5_B_base_openai_20260729T112210036785.json |

## B2. Failure analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R03_web_news_routing | wrong_tool / wrong_arg | lookup with query `AI news` and topic=news | The agent used an overly specific query (`AI news`) instead of the expected concise query (`AI`) and did not follow the news lookup contract consistently | Fixed by the later prompt/tool guidance in v3; passed from v3 onward |
| R08_out_of_scope | out_of_scope | an inappropriate tool call or answer attempt for an out-of-scope request | The agent tried to act on a request that should have been rejected or clarified as outside scope | Fixed by the v1 prompt rule to avoid acting on out-of-scope requests; passed from v1 onward |
| R10_missing_handle | missing_info | timeline(...) for a missing handle; later clarify without response_type | Agent guessed a handle instead of asking for the account name, and later missed the required response_type field | Fixed by the v1/v2 prompt rules plus the v3/v4 clarification guidance; fully passed from v4 |
| R11_missing_url | missing_info | fetch(...) for an absent URL; later clarify without response_type | Agent tried to act on a missing URL or asked without the required clarification argument | Fixed by the v1/v2 prompt rules plus the v3/v4/v5 clarification guidance; fully passed from v5 |
| R12_confirm_before_send | wrong_boundary | send(...) before user confirmation | Agent performed a write/send action before asking for yes/no confirmation | Fixed by the v1+ prompt rule to ask before write/send; passed from v1 onward |
| R13_parallel_web_and_tweets | wrong_tool / wrong_arg | lookup with query `AI news` and missing topic | The lookup tool contract was ambiguous; the agent used a malformed query instead of topic=news | Fixed by the v5 lookup/TOOL.md guidance; passed from v5 |
| R14_out_of_scope_coding | out_of_scope | an inappropriate tool call or answer attempt for a coding request | The agent tried to answer or act on a coding request despite the request being outside the intended scope | Fixed by the v1 prompt rule to avoid acting on out-of-scope requests; passed from v1 onward |

## B3. Team eval cases

List the 10 cases added to `data/eval_group.json`:

- 5 single-turn
- 5 multi-turn

This section is for the mandatory team-authored eval set. Optional built-ins do
not belong here.

File template để trống có chủ đích; nhóm phải tự thiết kế đủ 10 case.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
|  |  |  |  |

## B4. Live chat evidence

Use `transcripts/*.transcript.json`.

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Tool capability evidence

Phân loại rõ tool mới bắt buộc, optional built-in và tool đủ điều kiện bonus. Chỉ ghi Telegram/PDF nếu nhóm thực sự dùng; base report không cần chúng.

UI is core deliverable, not bonus. Do not list it here.

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên |  |  |  |
| Optional built-in |  |  |  |
| Bonus: tool mới thứ 4 trở đi |  |  |  |

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?
