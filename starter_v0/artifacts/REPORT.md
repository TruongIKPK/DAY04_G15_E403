# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Xong trước 11:30 để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. Có thể hoàn thiện sau buổi debate để nộp bài.

## Team

- Team: G15_E403
- Members: 
  - Trần Duy Trường - 2A202601247
  - Nguyễn Khánh Toàn - 2A202601843
  - Hồ Văn Thi - 2A202601907
  - Bùi Đặng Quốc An - 2A202601799
  - Nguyễn Quang Huy - 2A202601165
  - Lê Nguyễn Phi Trường - 2A202601541
- Provider/model: OpenRouter (`openai/gpt-4o-mini`)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent hỗ trợ tìm kiếm tin tức công nghệ trên web, tổng hợp bài đăng theo chủ đề/tài khoản trên Twitter, tự động đọc link bài viết và định dạng thành bản tin tổng hợp (digest). Agent có khả năng hỏi lại khi thiếu thông tin và yêu cầu xác nhận trước khi thực hiện hành động nhạy cảm (gửi tin).

**Link dùng thử (truy cập được trong showdown):**

> URL: http://localhost:8501 (Chạy local qua Streamlit UI)

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu thông tin hoặc cần xác nhận Yes/No | Không |
| timeline | Lấy các bài đăng gần đây của một tài khoản Twitter | Không |
| social_search | Tìm bài đăng trên Twitter theo từ khóa và kiểu xếp (Latest/Top) | Không |
| lookup | Tra cứu thông tin trên web / tin tức theo thời gian (day/week/month/year) | Không |
| fetch | Đọc và trích xuất nội dung từ một địa chỉ URL | Không |
| format | Trình bày danh sách item thành bản tin markdown digest | Không |
| send | Gửi văn bản tin tức lên kênh Telegram (cần xác nhận trước khi gửi) | Không |

## A3. Câu hỏi mẫu để thử

1. `Tin tức AI hôm nay trên web có gì nổi bật?`
2. `Mọi người đang bàn luận gì về GPT-5 trên Twitter?`
3. `Tóm tắt 5 tweet mới nhất của Elon Musk.`
4. `Đăng bản tin này lên Telegram giúp mình.`
5. `Viết giúp mình một hàm Python tính Fibonacci bằng đệ quy.` (Thử nghiệm tính năng từ chối ngoài phạm vi - Out of scope)

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| 1. Tra cứu tin tức web hôm nay | `lookup(query="AI", topic="news", timeframe="day")` | v0 bị thừa tool `social_search`; v1 sửa prompt để chỉ gọi `lookup`. | `v0_B_base_openrouter_20260729T100341094116.json` |
| 2. Thiếu thông tin người dùng | `clarify(question="...", response_type="text")` | v0 tự đoán tài khoản Sam Altman; v1 biết hỏi lại user xin tên/handle. | `v0_B_base_openrouter_20260729T103442362584.json` |
| 3. Xác nhận trước khi gửi bài | `clarify(response_type="yes_no")` | v0 tự gọi `send`; v1 tuân thủ Confirmation Boundary hỏi Yes/No trước. | `runs/v0_B_base_openrouter_20260729T103925043393.json` |
| 4. Xử lý câu hỏi ngoài phạm vi | Không gọi tool nào (`no_tool`), trả lời/từ chối trực tiếp | v0 đem câu hỏi code bỏ vào `send`; v1 nhận diện out-of-scope không dùng tool. | `transcripts/*.transcript.json` |


---

# PHẦN B — Chi tiết / Bằng chứng

> Điều kiện metric hợp lệ: `provider_error_cases` phải bằng `0`; `measured_cases` phải bằng `total_cases`; và bất kỳ `tool_results` nào có error đều phải được review thủ công vì routing PASS không chứng minh tool execution đã đúng.

## B1. Version evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | baseline prompt | Baseline ban đầu chưa rõ ràng ranh giới | case_accuracy | 0.70 | 0.70 | `v0_B_base_openrouter_20260729T100341094116.json` |
| v1 | Thêm quy tắc boundary & clarification | Rõ ràng hóa ranh giới hỏi lại khi thiếu URL/username & xác nhận trước khi gửi | case_accuracy | 0.70 | 0.85 | `v0_B_base_openrouter_20260729T103442362584.json` |
| v2 | Tối ưu Confirmation Boundary & Multi-turn | Tách biệt hoàn toàn `send` confirmation boundary & giữ lại timeframe trong multi-turn | case_accuracy | 0.85 | 0.90 | `v0_B_base_openrouter_20260729T103925043393.json` |
| v3 | Tinh chỉnh Single vs Parallel Tool routing | Giới hạn gọi song song `lookup` + `social_search` chỉ khi prompt yêu cầu rõ ràng cả 2 | case_accuracy | 0.90 | 1.00 | `runs/*.json` |

## B2. Failure analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R14_out_of_scope_coding | out_of_scope | `send(text="...")` | Viết đệ quy Fibonacci bị đem nhét vào tool `send` | Bổ sung quy tắc Out-of-scope trong `system_prompt.md`: Không dùng tool cho bài tập code. |
| R10_missing_handle | missing_info | `timeline(screenname="sama")` | Tự đoán tài khoản Sam Altman thay vì hỏi lại user | Bổ sung quy tắc `clarify(response_type="text")` khi thiếu tên tài khoản/handle. |
| R12_confirm_before_send | wrong_boundary | `send(text="Bản tin này")` | Tự động gửi Telegram mà không xin xác nhận | Thêm CRITICAL SAFETY RULE ép buộc gọi `clarify(response_type="yes_no")` trước khi `send`. |
| R03_web_news_routing | wrong_tool | `lookup` + `social_search` | Lỡ gọi dư tool `social_search` khi chỉ hỏi tin web | Sửa prompt: Mặc định gọi 1 tool, chỉ gọi song song khi prompt yêu cầu cả Web lẫn Twitter. |

## B3. Team eval cases

List the 10 cases added to `data/eval_group.json`:

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_single_tech_news | Tìm tin công nghệ mới nhất | `lookup(query="tech", topic="news")` | PASS |
| G02_single_missing_topic | Thiếu chủ đề tra cứu tin tức | `clarify(response_type="text")` | PASS |
| G03_single_send_confirm | Gửi báo cáo định kỳ | `clarify(response_type="yes_no")` | PASS |
| G04_single_math_out_of_scope | Giải phương trình bậc 2 | `no_tool` | PASS |
| G05_single_parallel_request | Web tin tức AI và Tweet về AI | `lookup` + `social_search` | PASS |
| G06_multi_clarify_then_search | Hỏi tin -> bổ sung chủ đề -> tìm kiếm | `lookup(topic="news")` | PASS |
| G07_multi_correct_handle | Nhầm tên tài khoản -> sửa lại | `timeline(screenname="...")` | PASS |
| G08_multi_carryover_limit | Giữ số lượng limit 3 bài | `timeline(limit=3)` | PASS |
| G09_multi_switch_web_to_twitter | Đang tìm web -> chuyển sang Twitter | `social_search` | PASS |
| G10_multi_url_summary | Thiếu URL -> đưa URL -> tóm tắt | `fetch(url="...")` | PASS |

## B4. Live chat evidence

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
| Turn 1: Tin AI hôm nay | v3 | `lookup(query="AI", topic="news", timeframe="day")` | `transcripts/*.transcript.json` | Trả về 5 tin AI nổi bật kèm link trích dẫn |
| Turn 2: Đăng lên Telegram | v3 | `clarify(question="...", response_type="yes_no")` | `transcripts/*.transcript.json` | Dừng lại xin xác nhận của người dùng |
| Turn 3: Đưa link bài báo | v3 | `fetch(url="https://...")` | `transcripts/*.transcript.json` | Đọc nội dung trang web thành công |

## B5. Tool capability evidence

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: UI Streamlit | `starter_v0/app.py` | Giao diện Chat, hiển thị Tool Traces, Versioning tag, và Sanitize API Keys | An toàn không bị lộ API key trên giao diện UI |
| Optional built-in: Telegram send | `tools/send/tool.py` | Trả về cờ `needs_confirmation` để ép agent phải hỏi trước khi gửi | Ngăn ngừa việc gửi tin rác / spam ngoài ý muốn |

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?**: Các điều chỉnh về ranh giới an toàn (Confirmation boundary khi gửi tin), quy tắc xử lý câu ngoài phạm vi (Out-of-scope không dùng tool), và nguyên tắc duy trì ngữ cảnh multi-turn.
- **Which fixes belonged in `tools.yaml`?**: Mô tả chi tiết chức năng từng tool, quy chuẩn các enum cho arguments (`search_type: Latest/Top`, `topic: news/general`).
- **Which failure needed manual review instead of automatic grading?**: Các case kiểm tra kết quả trả về từ `fetch` hoặc `lookup` xem nội dung tóm tắt có bị ảo giác (hallucination) hay không.
- **What would you improve next?**: Tích hợp thêm các bộ lọc phát hiện lặp tool (infinite loop guardrail) và cải thiện tốc độ phản hồi bằng cách cho phép agent gọi nhiều async tool cùng lúc.

