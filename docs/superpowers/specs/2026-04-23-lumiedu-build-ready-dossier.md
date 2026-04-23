# HỒ SƠ TRIỂN KHAI CHI TIẾT LUMIEDU (BUILD-READY)

## 1) Tóm tắt điều hành

**LumiEdu** là nền tảng gia sư AI voice-first, tập trung vào trải nghiệm học 1-1 bằng đối thoại giọng nói tiếng Việt.  
Phiên bản tài liệu này được tối ưu cho mục tiêu **triển khai thực tế MVP** theo định hướng:

- Full self-hosted cho dữ liệu học sinh.
- Đóng gói toàn bộ hạ tầng bằng Docker container.
- MVP tập trung duy nhất vào **Toán lớp 6 (mức độ phức tạp hơn cơ bản)**.
- Quy mô pilot: **1-3 học sinh đồng thời**.

**Slogan gợi ý:** Gia sư AI thế hệ mới - Thấu hiểu qua giọng nói.

---

## 2) Tầm nhìn, sứ mệnh, giá trị cốt lõi

### 2.1 Tầm nhìn
Trở thành nền tảng học tập bằng giọng nói tiếng Việt giúp học sinh học sâu, hiểu bản chất, và duy trì hứng thú học tập mỗi ngày.

### 2.2 Sứ mệnh
Biến mọi cuộc hội thoại học tập thành một trải nghiệm gia sư cá nhân hóa, phản hồi nhanh, bảo mật cao, và có thể mở rộng theo hệ sinh thái giáo viên Việt Nam.

### 2.3 Giá trị cốt lõi
- **Voice-first:** Học bằng nói và nghe, giảm rào cản gõ phím.
- **Self-hosted:** Làm chủ hạ tầng, bảo vệ dữ liệu học sinh.
- **Pedagogy-first:** Ưu tiên giải thích từng bước thay vì trả đáp án ngắn.
- **Low-latency:** Duy trì độ trễ thấp để hội thoại tự nhiên.

---

## 3) Bài toán và cơ hội thị trường

### 3.1 Vấn đề hiện tại
- Học sinh lớp 6 thường thiếu người kèm 1-1 liên tục.
- Học online truyền thống dễ mất tập trung, thụ động.
- Nhiều công cụ AI chỉ trả lời dạng văn bản, ít tương tác bằng lời nói.
- Lo ngại phụ huynh về dữ liệu học tập khi dùng nền tảng cloud bên ngoài.

### 3.2 Cơ hội của LumiEdu
- Tạo trải nghiệm gia sư giọng nói gần với tương tác người thật.
- Cải thiện mức độ tập trung và ghi nhớ qua nhịp hỏi-đáp liên tục.
- Khai thác khoảng trống "AI giáo dục tiếng Việt tự host" trong phân khúc phụ huynh ưu tiên bảo mật.

---

## 4) Phạm vi MVP đã chốt

### 4.1 Đối tượng
- Học sinh lớp 6.
- Phụ huynh cần công cụ kèm học tại nhà.

### 4.2 Năng lực chức năng trong MVP
- Giải thích khái niệm Toán 6 bằng giọng nói.
- Hướng dẫn giải bài theo từng bước.
- Vấn đáp kiểm tra mức hiểu.
- Lưu lịch sử phiên học và tiến độ cơ bản.

### 4.3 Ngoài phạm vi MVP
- Chưa mở marketplace.
- Chưa hỗ trợ đa môn toàn diện.
- Chưa triển khai multi-tenant quy mô lớn.

### 4.4 Tiêu chí hoàn thành MVP
- P95 độ trễ end-to-end <= 2.0 giây với 1-3 phiên đồng thời.
- Tỷ lệ lỗi pipeline voice < 3%/phiên.
- Mức hài lòng người dùng thử >= 4/5.
- 80% phản hồi tuân thủ khung "gợi mở + kiểm tra hiểu".

---

## 5) Kiến trúc công nghệ tổng thể (Docker-first)

## 5.1 Stack đã chốt
- **Frontend:** Next.js (React)
- **Backend/API & Orchestrator:** FastAPI (Python)
- **STT:** Faster-Whisper
- **LLM runtime:** Ollama (Llama 3/Mistral đã lượng tử hóa)
- **TTS:** GPT-SoVITS
- **Database:** PostgreSQL
- **Realtime cache/session/queue nhẹ:** Redis

### 5.2 Mô hình dịch vụ container
- `frontend`: web app cho học sinh/phụ huynh.
- `api`: auth, session management, orchestration, policy, metrics.
- `stt-service`: nhận audio chunk, trả transcript + confidence.
- `llm-service` (Ollama): nhận prompt chuẩn hóa, trả đáp án dạng cấu trúc.
- `tts-service`: tổng hợp giọng phản hồi.
- `postgres`: dữ liệu nghiệp vụ và học tập.
- `redis`: state nóng theo phiên, queue tác vụ ngắn.
- `reverse-proxy` (Nginx/Caddy): gateway nội bộ, TLS, routing.

### 5.3 Nguyên tắc triển khai trên MacBook Pro 2019
- Ưu tiên model nhẹ và quantization để giảm VRAM/RAM pressure.
- Warm-up model khi khởi động để giảm cold-start.
- Giới hạn token đầu ra theo ngữ cảnh bài toán.
- Duy trì queue per-session để tránh tranh chấp tài nguyên.

---

## 6) Thiết kế backend FastAPI (đề xuất build-ready)

### 6.1 Boundary trách nhiệm
- **API layer:** endpoint REST/WebSocket cho frontend.
- **Session Manager:** tạo/đóng phiên, quản lý trạng thái hội thoại.
- **Voice Orchestrator:** điều phối STT -> LLM -> TTS.
- **Pedagogy Engine:** áp dụng chiến lược dạy học Socratic.
- **Content Router:** ánh xạ câu hỏi vào chủ đề Toán 6 và policy.
- **Observability module:** ghi log, metrics, trace cơ bản.

### 6.2 Endpoint nhóm chức năng
- `POST /auth/login`, `POST /auth/refresh`
- `POST /sessions`, `GET /sessions/{id}`, `POST /sessions/{id}/end`
- `POST /voice/transcribe`
- `POST /voice/respond`
- `POST /voice/synthesize`
- `GET /progress/{studentId}`
- `GET /health`, `GET /metrics`

### 6.3 Realtime transport
- Dùng WebSocket cho phiên học trực tiếp để giảm overhead polling.
- Fallback HTTP khi mạng yếu hoặc client không ổn định.

---

## 7) Luồng dữ liệu hội thoại thời gian thực

### 7.1 Luồng chuẩn 1 vòng hội thoại
1. Client gửi audio chunk qua WebSocket đến `api`.
2. `api` chuyển chunk sang `stt-service`.
3. `stt-service` trả transcript + confidence score.
4. `api` chuẩn hóa transcript, cập nhật session context trong Redis.
5. `api` tạo prompt theo "topic + level + lỗi sai gần nhất + mục tiêu bài học".
6. Prompt gửi sang `llm-service` (Ollama).
7. LLM trả về đáp án có cấu trúc: giải thích, câu hỏi gợi mở, câu kiểm tra hiểu.
8. `api` gửi nội dung text qua `tts-service`.
9. `tts-service` trả audio phản hồi.
10. `api` stream audio về client, đồng thời lưu metadata vào PostgreSQL.

### 7.2 Data contract tối thiểu (khuyến nghị)
- Input STT: `session_id`, `audio_chunk`, `language`, `timestamp`.
- Output STT: `transcript`, `confidence`, `noise_level`.
- Input LLM: `learning_goal`, `topic`, `student_state`, `question`.
- Output LLM: `explanation_steps[]`, `check_question`, `hint_level`.
- Input TTS: `text`, `voice_id`, `emotion_profile`.
- Output TTS: `audio_url` hoặc `audio_bytes`.

---

## 8) Chiến lược sư phạm cho Toán lớp 6

### 8.1 Khung phản hồi bắt buộc
Mọi phản hồi LLM phải theo thứ tự:
1. Nhắc lại đề theo ngôn ngữ học sinh.
2. Chia nhỏ thành bước.
3. Gợi ý thay vì đưa đáp án ngay.
4. Kiểm tra hiểu bằng câu hỏi ngắn.
5. Chốt lại "điểm mấu chốt cần nhớ".

### 8.2 Mức hỗ trợ theo năng lực
- **Level 1:** gợi ý nhẹ, học sinh tự hoàn thành.
- **Level 2:** gợi ý có ví dụ tương tự.
- **Level 3:** giải mẫu từng bước, sau đó yêu cầu học sinh làm lại.

### 8.3 Guardrail nội dung
- Không trả lời ngoài chương trình học đã cấu hình.
- Không khẳng định kết quả nếu confidence thấp.
- Khi nghi ngờ: yêu cầu học sinh đọc lại đề hoặc tách dữ kiện.

---

## 9) Thiết kế dữ liệu và lưu trữ

### 9.1 PostgreSQL (dữ liệu bền vững)
Các bảng lõi:
- `users`
- `students`
- `guardians`
- `learning_sessions`
- `session_turns`
- `learning_progress`
- `curriculum_topics`
- `billing_events`

### 9.2 Redis (dữ liệu nóng)
- Session state đang hoạt động.
- Queue lượt xử lý voice theo phiên.
- Cache prompt template và context ngắn hạn.
- Rate limit theo user/device.

### 9.3 Chính sách dữ liệu
- Transcript lưu có kiểm soát thời gian giữ.
- Audio thô có thể bật/tắt lưu tùy cấu hình bảo mật.
- Mã hóa dữ liệu nhạy cảm at-rest và in-transit.

---

## 10) Độ trễ, hiệu năng và ổn định

### 10.1 Ngân sách độ trễ mục tiêu (tham chiếu)
- STT: 300-600ms
- LLM inference: 500-900ms
- TTS: 300-600ms
- Overhead routing/serialization: 100-200ms

### 10.2 Tối ưu hiệu năng bắt buộc
- Giảm độ dài prompt theo ngữ cảnh phiên học.
- Giới hạn max tokens đầu ra theo từng dạng câu hỏi.
- Batching có điều kiện cho tác vụ không realtime.
- Ưu tiên CPU pinning hợp lý trên máy host nếu cần.

### 10.3 Mô hình degrade mềm
- Quá tải nhẹ: giảm chất lượng TTS trước.
- Quá tải vừa: tăng timeout có thông báo "đang xử lý".
- Quá tải nặng: hạ số phiên đồng thời cho đến khi hồi phục.

---

## 11) Bảo mật, quyền riêng tư, tuân thủ

### 11.1 Nguyên tắc
- Dữ liệu học sinh không rời khỏi hạ tầng tự host.
- Quyền truy cập tối thiểu theo vai trò.
- Nhật ký truy cập và thay đổi cấu hình bắt buộc bật.

### 11.2 Biện pháp kỹ thuật
- TLS nội bộ qua reverse proxy.
- JWT + refresh token cho auth.
- Secret quản lý bằng `.env` nội bộ, không hardcode.
- Backup PostgreSQL định kỳ, kiểm tra khôi phục hàng tuần.

### 11.3 Quản trị dữ liệu phụ huynh-học sinh
- Minh bạch chính sách lưu transcript/audio.
- Cho phép yêu cầu xóa dữ liệu theo phiên hoặc theo tài khoản.

---

## 12) Vận hành DevOps cho self-hosted MVP

### 12.1 Chuẩn môi trường
- 1 file `docker-compose.yml` quản lý toàn bộ dịch vụ.
- Profile dev/staging tách cấu hình tài nguyên.
- Healthcheck cho từng container.

### 12.2 Logging và giám sát
- Log tập trung theo `session_id`.
- Dashboard tối thiểu:
  - Tỷ lệ lỗi STT/LLM/TTS
  - Độ trễ P50/P95 từng chặng
  - Số phiên đồng thời
  - Tỷ lệ phiên bị gián đoạn

### 12.3 Quy trình sự cố
- Mức 1: tự retry và ghi nhận.
- Mức 2: fallback response + cảnh báo vận hành.
- Mức 3: cô lập dịch vụ lỗi, duy trì chế độ hạn chế.

---

## 13) Roadmap phát triển sản phẩm

### Giai đoạn 1 - MVP (0-3 tháng)
- Hoàn thiện core voice tutoring Toán 6.
- 1-3 users đồng thời ổn định.
- Báo cáo phiên học cơ bản cho phụ huynh.

### Giai đoạn 2 - Platform (3-9 tháng)
- Cổng giáo viên nạp tài liệu PDF/DOC.
- Mỗi giáo viên tạo "Gia sư Lumi" của riêng mình.
- Bắt đầu multi-tenant ở mức tổ chức nhỏ.

### Giai đoạn 3 - Marketplace (9-18 tháng)
- Chợ nội dung bài giảng tương tác bằng giọng nói.
- Cơ chế phân chia doanh thu cho giáo viên.
- Xếp hạng chất lượng khóa học bằng dữ liệu phiên học.

---

## 14) Mô hình doanh thu và đơn vị kinh tế

### 14.1 Gói học sinh (B2C)
- Gói theo tháng theo số phút hội thoại.
- Gói cao hơn mở rộng số phiên và báo cáo nâng cao.

### 14.2 Phí hạ tầng cho tổ chức (B2B)
- License triển khai self-hosted cho trung tâm giáo dục.
- Phí bảo trì, nâng cấp mô hình, hỗ trợ vận hành.

### 14.3 Doanh thu marketplace
- Trích phần trăm giao dịch khóa học giữa giáo viên-học sinh.
- Gói quảng bá nội dung cho giáo viên.

### 14.4 Nguyên tắc định giá ban đầu
- Dựa trên chi phí compute thực tế theo phút hội thoại.
- Tách rõ phí nền tảng và phí nội dung để minh bạch.

---

## 15) KPI/OKR và nghiệm thu kỹ thuật

### 15.1 KPI sản phẩm
- Tỷ lệ phiên >15 phút.
- Tỷ lệ quay lại tuần kế tiếp.
- Điểm hài lòng phụ huynh/học sinh.
- Mức cải thiện điểm kiểm tra theo chủ đề.

### 15.2 KPI kỹ thuật
- P95 latency end-to-end <= 2.0s.
- Uptime hệ thống voice pipeline >= 99.0% (pilot).
- Lỗi nghiêm trọng ảnh hưởng học sinh < 1% phiên.

### 15.3 KPI vận hành
- MTTR sự cố chính < 30 phút.
- Tỷ lệ backup thành công 100%.
- Tỷ lệ khôi phục thành công khi drill >= 95%.

---

## 16) Rủi ro chính và phương án giảm thiểu

### 16.1 Rủi ro kỹ thuật
- **Model local không đủ chất lượng câu trả lời khó:**  
  -> tinh chỉnh prompt, thu hẹp phạm vi syllabus, kiểm tra ngữ cảnh bắt buộc.
- **Độ trễ tăng khi peak:**  
  -> giới hạn concurrent, tối ưu queue, warm service.
- **STT sai do giọng địa phương hoặc nhiễu:**  
  -> mở rộng từ điển miền, lọc nhiễu, xác nhận lại đề bài.

### 16.2 Rủi ro sản phẩm
- Học sinh lạm dụng hỏi đáp đáp án nhanh:  
  -> bắt buộc flow gợi mở trước, khóa đáp án trực tiếp ở lượt đầu.

### 16.3 Rủi ro vận hành
- Thiếu quy trình incident response:  
  -> xây runbook rõ theo 3 cấp độ, diễn tập định kỳ.

---

## 17) Kế hoạch hành động 30/60/90 ngày

### 30 ngày đầu
- Dựng stack Docker đầy đủ.
- Hoàn thiện login, session, voice loop cơ bản.
- Chạy pilot nội bộ với 3-5 bộ đề Toán 6.

### 60 ngày
- Tối ưu latency theo P95 mục tiêu.
- Hoàn thiện dashboard vận hành và báo cáo phụ huynh cơ bản.
- Chuẩn hóa prompt pedagogy theo từng chủ đề Toán 6.

### 90 ngày
- Pilot thực tế với nhóm học sinh nhỏ.
- Thu thập số liệu KPI sản phẩm và kỹ thuật.
- Chốt backlog để chuyển sang Platform phase.

---

## 18) Kết luận định hướng triển khai

LumiEdu ở phiên bản MVP cần tập trung tuyệt đối vào một lời hứa sản phẩm:  
**Gia sư Toán lớp 6 bằng giọng nói, phản hồi nhanh, dạy theo từng bước, dữ liệu nằm trong hạ tầng sở hữu.**

Việc giữ phạm vi hẹp, vận hành chắc, đo lường rõ sẽ là nền tảng để mở rộng lên Platform và Marketplace mà không đánh đổi chất lượng trải nghiệm cốt lõi.
