# Day 04 Lab v2 Report — Research Agent

## Team
- **Team Name**: AI20k - Group Research Agent
- **Provider/Model**: NVIDIA NIM / `meta/llama-3.1-70b-instruct`

**Members:**
1. Nguyễn Đăng Nam - 2A202601307
2. Nguyễn Hữu Tuyền - 2A202601605
3. Tống Nguyễn Minh Khang - 2A202601101
4. Đậu Quốc Duy - 2A202601445
5. Lê Chí Anh Tuấn - 2A202601149

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
|---|---|---|---:|---:|---:|---|
| **v0** | starter_defaults | Baseline prompt xúi đoán bừa và không dùng clarify làm phát sinh nhiều lỗi | case_accuracy | 0.00 | **0.30** | `runs/v0_B_base_nvidia_20260729T100943461328.json` |
| **v1** | system_prompt.md + tools.yaml | Bổ sung quy tắc clarify cho thông tin rỗng/xác nhận send và mapping handle sama | case_accuracy | 0.30 | **0.70** | `runs/v1_B_base_nvidia_20260729T102421659361.json` |
| **v2** | system_prompt.md + tools.yaml | Thêm quy tắc query clean (lọc bỏ từ thời gian) và mô tả kiểu số nguyên cho limit | case_accuracy | 0.70 | **0.65** | `runs/v2_B_base_nvidia_20260729T103706595091.json` |
| **v3** | system_prompt.md + tools.yaml | Surgical fix: thêm STRICT JSON Argument Types (ép integer), query cleaning, và ví dụ clarify cụ thể khi thiếu handle — sửa R03/R09/R10/R11/R12/R14 mà không gây tác dụng phụ | case_accuracy | 0.65 | **0.80** | `runs/v3_B_base_nvidia_20260729T145815559416.json` |

## B2. Failure analysis

**Các lỗi đã sửa được qua các version:**

| Case ID | Version phát hiện | Failure Type | What Failed | Fix Applied | Kết quả |
|---|---|---|---|---|---|
| `R01_user_tweets_routing` | $v0$ | `wrong_tool` | Model đoán bừa handle `samaltman` | Thêm rule mapping `Sam Altman -> sama` | ✅ PASS từ $v1$ |
| `R03_web_news_routing` | $v1$ | `wrong_tool` | Query dính từ rác `"Tin túc AI hôm nay"` | Thêm quy tắc Query Cleaning | ✅ PASS từ $v3$ |
| `R10_missing_handle` | $v0$ | `missing_info` | Gọi `social_search(query="")` thay vì hỏi lại | Thêm ví dụ clarify cụ thể khi thiếu handle | ✅ PASS từ $v3$ |
| `R12_confirm_before_send` | $v0$ | `wrong_boundary` | Tự gửi tin nhắn không xin phép | Yêu cầu `clarify(response_type="yes_no")` trước `send` | ✅ PASS từ $v1$ |

**Các lỗi còn lại ở $v3$ (model-level, không sửa được bằng prompt):**

| Case ID | Failure Type | Expected | Actual | Root Cause |
|---|---|---|---|---|
| `R05_limit_arg` | `wrong_arg_value` | `timeline(limit=10)` | `timeline(limit="10")` | Llama-3.1-70B serialize số thành string trong JSON tool call |
| `M01_clarify_then_fill` | `wrong_arg_value` | `timeline(limit=5)` | `timeline(limit="5")` | Cùng nguyên nhân — integer bị quote thành string |
| `M03_correction_handle` | `wrong_arg_value` | `timeline(limit=3)` | `timeline(limit="3")` | Cùng nguyên nhân — integer bị quote thành string |
| `M05_correction_limit` | `wrong_arg_value` | `timeline(limit=3)` | `timeline(limit="3")` | Cùng nguyên nhân — integer bị quote thành string |

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
| Tra cứu thời tiết Hà Nội | v3 | `weather(city="Hanoi")` | `transcripts/live_demo.json` | Trả về 29°C, Cloudy/Rain thực tế từ Open-Meteo API |
| Xem tin tức AI thời sự | v3 | `lookup(query="AI", topic="news", timeframe="day")` | `transcripts/live_demo.json` | Trả về 5 tin tức AI thời sự cập nhật trong ngày |
| Hỏi xin xác nhận Telegram | v3 | `clarify(question=..., response_type="yes_no")` | `transcripts/live_demo.json` | Dừng và hiển thị form Yes/No cho người dùng |

## B5. Tool capability evidence

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: Custom Tool mới | `tools/weather/tool.py` | Gọi API Open-Meteo lấy thông tin nhiệt độ/thời tiết thực tế | fallback mặc định nếu API geocoding rỗng |
| Built-in core tools | `tools/lookup/tool.py` | Lấy dữ liệu web/tin tức thực từ Tavily API | giới hạn timeout 10s |
| Action tool guardrail | `tools/send/tool.py` | Kiểm tra cờ `confirmed=True` trước khi thực hiện hành động gửi | Bắt buộc xin phép user qua `clarify` trước |

## B6. Reflection

- **Chỉnh sửa trong `system_prompt.md`**: Phù hợp cho việc điều phối luồng tư duy (routing), đưa ra nguyên tắc bắt buộc gọi `clarify` khi thiếu thông tin, thiết lập quy tắc xác nhận trước hành động nhạy cảm, và quy định mapping tên thành handle.
- **Chỉnh sửa trong `tools.yaml`**: Phù hợp cho việc mô tả chi tiết chức năng của từng tool, quy định kiểu dữ liệu tham số (ép kiểu `integer` cho limit/max_results) và giúp LLM hiểu đúng ý định sử dụng tool.
- **Bài học từ v2/v3 cũ**: Over-constraining (hạn chế clarify quá mức cho math/coding) gây tác dụng phụ nghiêm trọng — model ngưng luôn cả clarify ở các trường hợp thực sự cần hỏi lại (R10, R11, R12). Chiến lược "surgical fix" (sửa phẫu thuật chính xác, chỉ thêm quy tắc nhắm trúng lỗi cụ thể) hiệu quả hơn nhiều so với thêm nhiều ràng buộc cùng lúc.
- **Lỗi còn lại (model-level)**: 4 case FAIL còn lại (R05, M01, M03, M05) đều do Llama-3.1-70B serialize `limit` dưới dạng string `"5"` thay vì integer `5` trong JSON tool call. Đây là hạn chế cố hữu của model, không thể sửa hoàn toàn bằng prompt engineering.
- **Hướng cải thiện tiếp theo**: Xây dựng cơ chế tự động parse/type-cast tham số ở tầng tool execution để chuyển chuỗi `"5"` thành số `5` trước khi validate, giúp tăng thêm tính ổn định cho Agent.
