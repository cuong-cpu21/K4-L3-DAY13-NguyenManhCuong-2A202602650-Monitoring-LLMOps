# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Mạnh Cường
- **MSSV:** 2A202602650
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/cuong-cpu21/K4-L3-DAY13-NguyenManhCuong-2A202602650-Monitoring-LLMOps
- **Commit SHA cuối:**
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602650`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Đạt điểm tuyệt đối, đầy đủ schema, correlation ID và enrichment |
| `validate_dashboard.py` | 6/6 panel | 6/6 panel | Đạt chuẩn contract của ban tổ chức |
| `pytest` | 22 passed | 24 passed | 100% pass toàn bộ unit tests và PII tests mới |
| Số traces hợp lệ | 10 | 37 | Đầy đủ span tree: root, retrieval, generation trên Langfuse |
| Số PII leak | 0 | 0 | Đã scrub sạch Email, Phone VN, CCCD, Credit Card |
| Latency P95 / TTFT P95 | 1602ms / 50ms | 1185ms / 50ms | Độ trễ ổn định, TTFT 50ms đáp ứng tốt SLO <= 3000ms |
| Retrieval success rate | 100% | 100% | RAG hoạt động ổn định, không có lỗi vector store |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Trong `app/middleware.py`, middleware gọi `clear_contextvars()` ở đầu mỗi request để ngăn rò rỉ context giữa các HTTP requests. Tiếp theo, trích xuất header `x-request-id` từ client nếu có hoặc tự sinh ID theo chuẩn `req-<8-hex>` (`req-` + `uuid.uuid4().hex[:8]`). Sau đó gọi `bind_contextvars(correlation_id=correlation_id)` và lưu vào `request.state.correlation_id`. Cuối request, middleware gắn `x-request-id` và `x-response-time-ms` vào HTTP response headers.
- **Các metadata được ghi vào structured log:** Mỗi log record chứa `correlation_id`, `user_id_hash` (băm SHA-256 12 ký tự), `session_id`, `feature`, `model`, `env`, `ts`, `level`, `service`, `event`. Đối với response thành công: ghi thêm `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success` và `payload.answer_preview`.
- **Cách bảo đảm PII được scrub trước khi ghi:** Processor `scrub_event` trong `app/logging_config.py` được đăng ký trước `JsonlFileProcessor` và `JSONRenderer`. Hàm `scrub_event` duyệt đệ quy làm sạch các chuỗi bằng bộ regex trong `PII_PATTERNS` (`app/pii.py`), thay thế thông tin cá nhân thành các token an toàn: `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, `[REDACTED_CCCD]`, `[REDACTED_CREDIT_CARD]`.
- **Cách kiểm chứng kết quả:** Chạy `python scripts/validate_logs.py` đạt điểm tuyệt đối 100/100 (0 records thiếu trường, 0 PII leak), kiểm tra trực tiếp các dòng log trong `data/logs.jsonl` và chạy bộ test `pytest tests/test_pii.py` pass 100%.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Traces được ghi trực tiếp vào project cá nhân `day13-k4-l3b-2A202602650` trên Langfuse Cloud thông qua API key của tài khoản `cuong-cpu21`. Các trace mang environment `dev`, tags `["lab", feature, model]` và metadata khớp chính xác với mã `correlation_id` trong log local.
- **Cấu trúc root/retrieval/generation observations:**
  - `day13-agent-request` (trace root)
    - `lab-agent-run` (observation cha - kiểu `agent`)
      - `retrieval` (observation con - kiểu `retriever` đo đạc thời gian truy xuất tài liệu từ corpus)
      - `generation` (observation con - kiểu `generation` ghi nhận model, input/output tokens, cost, prompt template)
- **Cách nối trace với log:** Trường `correlation_id` (ví dụ `req-8356fc51`) được truyền vào `metadata` của trace/span khi gọi `propagate_attributes`. Khi kiểm tra log phát hiện request bất thường, chỉ cần copy `correlation_id` và tìm kiếm trên ô Search của Langfuse để mở đúng trace của request đó.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 1 mang nhãn `baseline` và `production` với 3 biến chuẩn: `Feature={{feature}}`, `Docs={{docs}}`, `Question={{message}}`.
- **Version/label candidate:** Version 2 mang nhãn `candidate`, bổ sung thêm chỉ dẫn định dạng `Trả lời ngắn gọn và súc tích.`.
- **Trace ID của mỗi version:**
  - Trace ID dùng Version 1 (`production` / `baseline`): `db7d04a690a239e0d328139f0c75b68e`
  - Trace ID dùng Version 2 (`candidate` / `production` sau promote): `18505fa141c9ec9d5e587457feb96756`
- **Cách promote và rollback `production`:**
  - *Promote*: Gọi Langfuse API `client.update_prompt(name='day13-chat', version=2, new_labels=['candidate', 'production'])` để trỏ nhãn `production` sang Version 2 mà không sửa code.
  - *Rollback*: Gọi `client.update_prompt(name='day13-chat', version=1, new_labels=['baseline', 'production'])` để dời nhãn `production` quay lại Version 1 an toàn.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Dựng đúng 6 panel theo `config/dashboard.yaml` lưu tại `evidence/11-dashboard-overview.png`:
  1. *Latency*: P50, P95, P99 và TTFT P95 kèm đường threshold P95 <= 3000ms.
  2. *Traffic*: Tần suất requests/phút kèm ngưỡng rate >= 1 req/min.
  3. *Errors*: Tỷ lệ lỗi request (%) và tỷ lệ truy xuất retrieval thành công (%) kèm ngưỡng Error <= 2%, Retrieval >= 90%.
  4. *Cost*: Tổng chi phí tích lũy theo USD kèm ngưỡng <= $2.50.
  5. *Tokens*: Thống kê tokens input và output kèm ngưỡng <= 50,000 tokens.
  6. *Quality*: Điểm đánh giá chất lượng trung bình kèm ngưỡng >= 0.75.
- **SLO và lý do chọn:** Primary SLO `fast_successful_requests` với mục tiêu 99.5% requests hoàn thành thành công và có độ trễ latency <= 3000ms trên chu kỳ trượt 28 ngày. Lý do: Baseline đo được latency P95 khoảng 1185ms và TTFT 50ms, do đó ngưỡng 3000ms là phù hợp để phát hiện sớm các điểm nghẽn (tail latency) mà không gây báo động giả.
- **Cách tính error budget:** SLO 99.5% tương ứng với Error Budget là 0.5%. Nếu hệ thống tiếp nhận 10,000 requests trong cửa sổ 28 ngày, số lượng requests tối đa được phép bị chậm (>3000ms) hoặc bị lỗi (HTTP 500) là:
  $$10,000 \times 0.5\% = 50 \text{ requests}$$
- **Ba alert và runbook tương ứng:**
  1. `HighLatencyP95` (Warning, `p95(latency_ms) > 3000ms` trong 5m, Slack `#k4-l3b-alerts`, runbook `docs/alerts.md#alert-1`).
  2. `HighErrorRate` (Critical, `error_rate_pct > 2%` trong 3m, Slack `#k4-l3b-alerts`, runbook `docs/alerts.md#alert-2`).
  3. `DegradedRetrievalSuccessRate` (Warning, `retrieval_success_rate_pct < 90%` trong 5m, Slack `#k4-l3b-alerts`, runbook `docs/alerts.md#alert-3`).

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** 03:47:07Z đến 03:47:21Z (sau khi sự cố `rag_slow` được kích hoạt lúc 03:46:57Z)
- **Triệu chứng từ metrics:** Panel `Latency percentiles and TTFT` trên dashboard ghi nhận độ trễ server (`latency_ms`) tăng vọt từ mức baseline ~155ms lên **2651ms - 2652ms** (vượt ngưỡng threshold 2000ms của challenge). Trong khi đó, TTFT (Time To First Token) vẫn duy trì ổn định ở mức 50ms, Error rate là 0% (API vẫn trả mã HTTP 200), tokens và cost không có đột biến.
- **Log line và correlation ID liên quan:** Lọc log trong khung giờ sự cố, trích xuất request đại diện có **`correlation_id: req-86a3fb31`** (session_id: `k4-l3b-challenge-s05`, feature: `monitoring`). Log response:
  ```json
  {"service": "api", "event": "response_sent", "correlation_id": "req-86a3fb31", "latency_ms": 2651, "ttft_ms": 50, "tokens_in": 35, "tokens_out": 112, "cost_usd": 0.001785, "quality_score": 0.8, "tool_name": "retrieval", "tool_success": true, "model": "claude-sonnet-4-5", "ts": "2026-09-30T03:47:10.236731Z"}
  ```
- **Trace ID và span gây ảnh hưởng:** Trace ID **`db22b844e52347df188656db10a6e387`** trên Langfuse Cloud (có correlation ID `req-86a3fb31`). Cây waterfall tree phân tích:
  - `day13-agent-request` (2651ms) $\rightarrow$ `lab-agent-run` (2651ms)
  - Span con `retrieval`: **2501ms** (chiếm **94.3%** tổng thời gian request, là điểm nghẽn chính).
  - Span con `generation`: **150ms** (chỉ chiếm **5.7%**, TTFT 50ms, model sinh phản hồi nhanh bình thường).
- **Root cause:** Bước truy xuất tài liệu vector store (`retrieval`) trong luồng RAG của feature `monitoring` bị nghẽn (do kịch bản sự cố `rag_slow` gây độ trễ nhân tạo 2.50s trong `app/mock_rag.py`). Dù mô hình LLM vẫn phản hồi nhanh và trả về mã HTTP 200 thành công, thời gian nghẽn của retrieval đã kéo toàn bộ request lên 2.65s, vi phạm ngưỡng độ trễ 2000ms.
- **Fix action:**
  1. Tắt sự cố bằng lệnh `python scripts/inject_incident.py --disable` (gọi endpoint `/incidents/rag_slow/disable`).
  2. Khởi động lại dịch vụ Vector DB và kiểm tra chỉ mục (index) để giải phóng hàng đợi truy vấn.
- **Preventive measure:**
  1. Cấu hình timeout nghiêm ngặt cho bước retrieval (ví dụ: timeout 1500ms), kích hoạt cơ chế trả lời fallback nếu vector search quá hạn thay vì để request bị treo lâu.
  2. Bổ sung alert `HighLatencyP95` (với duration 5m, ngưỡng 2000ms) để thông báo ngay lập tức qua Slack cho đội ngũ SRE.
  3. Áp dụng semantic caching cho các câu hỏi phổ biến thuộc feature `monitoring` để giảm tải trực tiếp lên vector database.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Đăng ký processor `scrub_event` tại tầng cấu hình tập trung của structlog (`configure_logging`) trước khi serialize và ghi file `JsonlFileProcessor`. Quyết định này bảo đảm 100% mọi log record từ bất kỳ service/endpoint nào đều tự động được quét và làm sạch PII mà không cần lập trình viên phải gọi hàm che dấu thủ công ở từng controller.
- **Một lỗi/blocker đã gặp:** Ở bước đầu, API chưa thể hiện được cấu trúc cây phân nhánh cha-con trên Langfuse và gặp lỗi khi gọi API cũ `GET /api/public/traces` (do Langfuse Cloud đã chuyển sang v4 Observations API từ sau ngày 16/09/2026).
- **Cách tìm nguyên nhân và xử lý:** Kiểm tra log chi tiết từ Langfuse SDK, tham chiếu theo gợi ý trong `README.md` và `tests/test_agent_prompt_trace.py`. Đã gắn decorator `@observe` cho `retrieve` (`as_type="retriever"`) và `FakeLLM.generate` (`as_type="generation"`), đồng thời dùng `propagate_attributes(prompt=...)` để liên kết generation với phiên bản prompt Langfuse một cách tự nhiên.
- **Cách hiểu luồng Metrics → Logs → Traces:**
  - *Metrics*: Giúp người trực vận hành có cái nhìn toàn cảnh, phát hiện hệ thống đang có triệu chứng gì bất thường (ví dụ: latency P95 tăng vọt, retrieval success giảm) và khung giờ xảy ra sự cố.
  - *Logs*: Từ khung giờ sự cố, lọc các sự kiện `request_failed` hoặc các request có `latency_ms` cao, trích xuất chính xác mã định danh duy nhất `correlation_id`.
  - *Traces*: Dùng `correlation_id` mở waterfall trên Langfuse, phân tích từng span con để chỉ ra chính xác bước nào là điểm nghẽn (do vector DB chậm, LLM loop token hay prompt quá dài).
  - *Root cause*: Tổng hợp chuỗi bằng chứng không thể chối cãi từ cả 3 tầng thay vì phỏng đoán cảm tính.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  - Quản lý phiên bản prompt cho phép tách biệt vòng đời của prompt khỏi chu kỳ release code. Thông qua các nhãn (`baseline`, `candidate`, `production`), ta có thể promote phiên bản mới và rollback ngay lập tức nếu prompt mới gây giảm chất lượng hoặc tăng vọt độ trễ.
  - Giám sát Token/Cost ngăn ngừa nguy cơ cạn kiệt ngân sách do prompt injection hoặc model sinh token không kiểm soát.
  - SLO và Error Budget cung cấp thước đo khách quan để đội ngũ kỹ thuật quyết định khi nào nên ưu tiên độ ổn định thay vì deploy vội vã.
- **Điều quan trọng nhất đã học:** Nắm vững phương pháp luận vận hành LLMOps chuẩn SRE: Không tin vào HTTP 200, luôn bảo vệ dữ liệu nhạy cảm của người dùng (PII) trước khi ghi log, và luôn điều tra sự cố theo chuỗi bằng chứng Metrics → Logs → Traces.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Bài lab thực hiện trên môi trường single-instance local; ở quy mô production phân tán đa cụm, hệ thống cần tích hợp bộ thu thập telemetry tập trung (như OpenTelemetry Collector, Prometheus, Loki và Grafana).

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
