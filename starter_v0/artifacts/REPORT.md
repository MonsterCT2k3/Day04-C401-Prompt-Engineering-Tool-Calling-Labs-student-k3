# Day 04 Lab v2 Report — Research Agent

## Team

- Team: AI20k - Group Research Agent
- Members: Student Team
- Provider/model: NVIDIA NIM / `meta/llama-3.1-70b-instruct`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent hỗ trợ tìm kiếm tin tức trên Web, xem tweet theo tài khoản hoặc từ khóa, tra cứu thời tiết các thành phố, hỏi lại người dùng khi thiếu thông tin, xin xác nhận trước khi gửi tin nhắn Telegram, và trình bày thông tin thành báo cáo Markdown chuyên nghiệp.

**Link dùng thử (truy cập được trong showdown):**
> URL: `http://localhost:8501` (Hoặc chạy Streamlit UI: `streamlit run app.py`)

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi lại người dùng khi thiếu thông tin hoặc xin xác nhận trước hành động nhạy cảm | Không |
| `timeline` | Lấy các bài đăng/tweet mới nhất của một tài khoản Twitter | Không |
| `social_search` | Tìm kiếm bài đăng trên mạng xã hội Twitter theo từ khóa | Không |
| `lookup` | Tra cứu thông tin trên web chung hoặc báo chí thời sự (`topic: news`) | Không |
| `fetch` | Đọc toàn bộ nội dung văn bản từ một đường dẫn URL web | Không |
| `format` | Trình bày các kết quả nghiên cứu thành bản tin/báo cáo Markdown | Không |
| `send` | Gửi tin nhắn đến kênh Telegram (yêu cầu xác nhận qua `clarify`) | Không (Built-in) |
| `policy` | Tra cứu tài liệu chính sách nội bộ công ty | Không (Built-in) |
| `papers` | Tìm kiếm bài báo khoa học trên arXiv | Không (Built-in) |
| `paper_text` | Trích xuất văn bản từ PDF bài báo arXiv | Không (Built-in) |
| `weather` | **Tra cứu thời tiết thực tế hiện tại cho bất kỳ thành phố nào** | **CÓ (Custom Tool)** |

## A3. Câu hỏi mẫu để thử

1. **Tra cứu thời tiết**: "Thời tiết Hà Nội hôm nay thế nào?"
2. **Tìm tin tức AI**: "Tin tức AI hôm nay có gì nổi bật trên web?"
3. **Xem Tweet người nổi tiếng**: "Tweet mới nhất của Sam Altman là gì?"
4. **Kiểm tra Boundary/Xác nhận**: "Đăng bản tin này lên Telegram giúp mình" -> Agent sẽ hỏi lại `clarify(response_type="yes_no")`.
5. **Hỏi thiếu thông tin**: "Tóm tắt 5 tweet mới nhất giúp mình" -> Agent sẽ dùng `clarify` để hỏi xem tweet của ai.

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| **1. Tra cứu tweet Sam Altman** | `timeline(screenname="sama")` | $v0$ tự đoán `samaltman` gây lỗi API -> $v1$ map chuẩn tên thành `sama` | `runs/v1_B_base_nvidia_...json` |
| **2. Xem tin tức thời sự AI** | `lookup(query="AI", topic="news", timeframe="day")` | $v0$ chọn sai tool -> $v1/v2$ trích từ khóa chuẩn `"AI"` và set `topic: news` | `runs/v2_B_base_nvidia_...json` |
| **3. Xác nhận trước khi gửi** | `clarify(question=..., response_type="yes_no")` | $v0$ làm liều không hỏi -> $v1$ dừng hỏi xác nhận trước khi gọi `send` | `runs/v1_B_base_nvidia_...json` |
| **4. Tra cứu thời tiết thành phố** | `weather(city="Hanoi")` | Tool custom mới của nhóm tự thực thi API Open-Meteo trả kết quả thời tiết | `tools/weather/tool.py` |

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version evidence

Dữ liệu tổng hợp từ `artifacts/version_log.csv` và `runs/*.json`:

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | Baseline run; no prompt/tool changes yet | Baseline shows the agent guesses missing handle and uses tools too eagerly | case_accuracy | 0.65 | 0.80 | v0_B_base_openai_20260729T101321700753.json |
| v1 | system_prompt.md: stronger routing rules for tweet questions and no guessing when handle is missing | Clearer routing rules should reduce wrong-tool and missing-info errors | case_accuracy | 0.80 | 0.85 | v1_B_base_openai_20260729T103729522319.json |
| v2 | system_prompt.md: distinguish “tweet of a person” vs “topic search” | Better prompt separation should improve routing and argument correctness | case_accuracy | 0.80 | 0.85 | v2_B_base_openai_20260729T104135763829.json |
| v3 | clarify/TOOL.md: require response_type=text for clarification requests | Explicit tool contract should fix missing-info cases | case_accuracy | 0.85 | 0.85 | v3_B_base_openai_20260729T104455083636.json |
| v4 | system_prompt.md: clarify-before-action and no guessing when information is missing | Clarification-first behavior should reduce argument mistakes and boundary errors | case_accuracy | 0.85 | 0.90 | v4_B_base_openai_20260729T105329489158.json |
| v5 | lookup/TOOL.md: use topic=news and avoid putting “news” into the query | Cleaner lookup args should make news lookup and parallel tool use pass end-to-end | case_accuracy | 0.90 | 1.00 | v5_B_base_openai_20260729T112210036785.json |

## B2. Failure analysis

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

Danh sách 10 test cases được bổ sung vào `data/eval_group.json`:

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| `G01_weather_hanoi` | Single-turn: Tra cứu thời tiết Hà Nội | `weather(city="Hanoi")` | PASS |
| `G02_weather_tokyo` | Single-turn: Tra cứu thời tiết Tokyo | `weather(city="Tokyo")` | PASS |
| `G03_missing_city_weather` | Single-turn: Thiếu tên thành phố khi hỏi thời tiết | `clarify(response_type="text")` | PASS |
| `G04_company_policy_privacy` | Single-turn: Tra cứu quy định bảo mật nội bộ | `policy(query="bảo mật dữ liệu", policy_area="data_privacy")` | PASS |
| `G05_arxiv_papers_search` | Single-turn: Tìm bài báo khoa học LLMs | `papers(query="Large Language Models")` | PASS |
| `GM01_weather_switch_city` | Multi-turn: Đổi thành phố từ Hà Nội sang Đà Nẵng | `weather(city="Da Nang")` | PASS |
| `GM02_weather_to_news` | Multi-turn: Đổi từ xem thời tiết sang xem tin tức AI | `lookup(query="AI", topic="news", timeframe="day")` | PASS |
| `GM03_clarify_then_send` | Multi-turn: Xác nhận gửi tin nhắn sau khi đồng ý | `send(confirmed=true)` | PASS |
| `GM04_cancel_request` | Multi-turn: User hủy yêu cầu giữa chừng | `no_tool` (Không gọi tool) | PASS |
| `GM05_out_of_scope_math` | Multi-turn: Yêu cầu tính toán phép toán | `no_tool` (Trả lời thẳng) | PASS |

## B4. Live chat evidence

Bằng chứng thực thi qua UI / chat loop (`app.py` / `chat.py`):

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
| Tra cứu thời tiết Hà Nội | v1 | `weather(city="Hanoi")` | `transcripts/live_demo.json` | Trả về 29°C, Cloudy/Rain thực tế từ Open-Meteo API |
| Xem tin tức AI thời sự | v1 | `lookup(query="AI", topic="news", timeframe="day")` | `transcripts/live_demo.json` | Trả về 5 tin tức AI thời sự cập nhật trong ngày |
| Hỏi xin xác nhận Telegram | v1 | `clarify(question=..., response_type="yes_no")` | `transcripts/live_demo.json` | Dừng và hiển thị form Yes/No cho người dùng |

## B5. Tool capability evidence

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: Custom Tool mới | `tools/weather/tool.py` | Gọi API Open-Meteo lấy thông tin nhiệt độ/thời tiết thực tế | fallback mặc định nếu API geocoding rỗng |
| Built-in core tools | `tools/lookup/tool.py` | Lấy dữ liệu web/tin tức thực từ Tavily API | giới hạn timeout 10s |
| Action tool guardrail | `tools/send/tool.py` | Kiểm tra cờ `confirmed=True` trước khi thực hiện hành động gửi | Bắt buộc xin phép user qua `clarify` trước |

## B6. Reflection

- **Chỉnh sửa trong `system_prompt.md`**: Phù hợp cho việc điều phối luồng tư duy (routing), đưa ra nguyên tắc bắt buộc gọi `clarify` khi thiếu thông tin, thiết lập quy tắc xác nhận trước hành động nhạy cảm, và quy định mapping tên thành handle.
- **Chỉnh sửa trong `tools.yaml`**: Phù hợp cho việc mô tả chi tiết chức năng của từng tool, quy định kiểu dữ liệu tham số (ép kiểu `integer` cho limit/max_results) và giúp LLM hiểu đúng ý định sử dụng tool.
- **Lỗi cần review thủ công**: Các trường hợp LLM gọi đúng tên tool nhưng truyền tham số dạng string `"5"` thay vì int `5` hoặc trường hợp LLM over-clarify ở các câu toán học/coding out-of-scope.
- **Hướng cải thiện tiếp theo**: Xây dựng cơ chế tự động parse/type-cast tham số ở tầng tool execution để chuyển chuỗi `"5"` thành số `5` trước khi validate, giúp tăng thêm tính ổn định cho Agent.
