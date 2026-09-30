# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Primary SLO `fast_successful_requests` (latency P95 <= 3000ms)
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` duy trì liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng phải chờ quá lâu trước khi nhận câu trả lời, trải nghiệm tương tác bị chậm trễ
- Ba bước kiểm tra đầu tiên:
  1. **Metrics**: Mở panel `Latency percentiles and TTFT` trên dashboard để xác nhận thời điểm P95 vượt ngưỡng và kiểm tra xem TTFT có tăng tương ứng không.
  2. **Logs**: Lọc `data/logs.jsonl` trong khoảng thời gian bị chậm (`event == "response_sent"` và `latency_ms > 3000`), chọn một request đại diện và lấy `correlation_id`.
  3. **Traces**: Mở Langfuse, tra cứu trace theo `correlation_id`, kiểm tra waterfall xem span `retrieval` hay `generation` kéo dài thời gian.
- Mitigation tạm thời: Kiểm tra độ trễ của vector store, rollback prompt sang version trước nếu latency tăng sau khi đổi prompt, hoặc khởi động lại container API nếu nghẽn tài nguyên.
- Owner: `cuong-2A202602650`

## Alert 2

- Tên: `HighErrorRate`
- Severity: `critical`
- Duration: `3m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Guardrail `error_rate_pct_max <= 2%` và Primary SLO `fast_successful_requests`
- Điều kiện và thời gian duy trì: `error_rate_pct > 2%` duy trì trong 3 phút
- Ảnh hưởng tới người dùng: Người dùng nhận phản hồi lỗi HTTP 500, không hoàn thành được tác vụ hỏi đáp
- Ba bước kiểm tra đầu tiên:
  1. **Metrics**: Mở panel `Error rate and retrieval success` trên dashboard để xác nhận tỷ lệ lỗi và thống kê các loại lỗi `error_type`.
  2. **Logs**: Lọc các dòng log `event == "request_failed"` trong `data/logs.jsonl`, xem thông báo `detail` trong payload và ghi lại `correlation_id`.
  3. **Traces**: Tìm trace có cùng `correlation_id` trên Langfuse, kiểm tra span bị đánh dấu `ERROR` và đọc chi tiết lỗi tại node con.
- Mitigation tạm thời: Bật cơ chế trả lời fallback nếu vector search bị lỗi, hoặc rollback phiên bản deploy gần nhất nếu phát sinh bug mã nguồn.
- Owner: `cuong-2A202602650`

## Alert 3

- Tên: `DegradedRetrievalSuccessRate`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Guardrail `retrieval_success_rate_pct_min >= 90%`
- Điều kiện và thời gian duy trì: `tool_success_rate_pct < 90%` trong 5 phút
- Ảnh hưởng tới người dùng: RAG không trích xuất được văn bản phù hợp, làm giảm độ chính xác của câu trả lời hoặc rơi vào fallback chung chung
- Ba bước kiểm tra đầu tiên:
  1. **Metrics**: Mở panel `Error rate and retrieval success` trên dashboard, đối chiếu tỷ lệ thành công của retrieval với ngưỡng 90%.
  2. **Logs**: Lọc các dòng log có `tool_name == "retrieval"` và `tool_success == false` trong `data/logs.jsonl`, lấy `correlation_id` liên quan.
  3. **Traces**: Mở trace trên Langfuse tương ứng với `correlation_id`, kiểm tra span `retrieval` để xem lỗi kết nối vector store hay không tìm thấy document.
- Mitigation tạm thời: Khởi động lại dịch vụ Vector DB, kiểm tra embedding pipeline và làm mới cache tìm kiếm ngữ nghĩa.
- Owner: `cuong-2A202602650`
