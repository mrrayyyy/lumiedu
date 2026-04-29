# Roadmap phat trien LumiEdu

## Trang thai hien tai (MVP - v0.1)

### Da hoan thanh
- Voice pipeline STT -> LLM -> TTS hoat dong end-to-end
- Giao dien web: Login, Dashboard, Phien hoc (text + voice), Tien do
- 6 chu de Toan lop 6: phan_so, so_thap_phan, so_nguyen, hinh_hoc, phep_tinh, ti_so
- Socratic method trong LLM prompt
- JWT authentication + rate limiting
- Docker Compose full stack (8 containers)
- Provider pattern cho STT/LLM/TTS (de thay doi provider)
- Mock mode cho LLM (test khong can Ollama)
- Audio caching cho TTS (LRU, MD5 hash)
- Multi-stage Docker builds
- Nginx reverse proxy voi audio proxy + WebSocket
- Backup/restore scripts cho PostgreSQL

### Con thieu (MVP backlog)
- [ ] Alembic database migrations (hien tai dung raw SQL, khong co version tracking)
- [ ] Unit tests va integration tests
- [ ] FastAPI dependency injection cho SessionManager, VoiceOrchestrator
- [ ] Pydantic Settings cho microservices (hien tai dung plain class)
- [ ] Shared library (`packages/shared/`) cho common patterns giua services
- [ ] Token counting cho LLM context window management
- [ ] Pagination cho sessions list
- [ ] TLS/SSL configuration

---

## Giai doan 1 - Hoan thien MVP (1-2 thang)

### 1.1 Chat luong code
- [ ] Them test suite: unit tests (pytest), integration tests, frontend tests (vitest)
- [ ] Setup CI/CD pipeline (GitHub Actions)
- [ ] Database migrations voi Alembic
- [ ] Dependency injection pattern cho backend
- [ ] Error tracking (Sentry hoac tuong duong)

### 1.2 Trai nghiem hoc sinh
- [ ] Cai thien STT cho tieng Viet (fine-tune Whisper hoac dung model lon hon)
- [ ] Them giong noi tu nhien hon (GPT-SoVITS thay gTTS)
- [ ] Streaming response (hien text tung phan thay vi doi het)
- [ ] Luu lich su phien hoc da ket thuc (hien tai chi xem active sessions)
- [ ] Phan hoi bang hinh anh (ve hinh hoc, bieu do)

### 1.3 Quan tri
- [ ] Dashboard bao cao cho phu huynh/giao vien
- [ ] Quan ly hoc sinh (CRUD)
- [ ] Cau hinh chu de va muc do qua UI
- [ ] Export du lieu hoc tap (CSV/PDF)

---

## Giai doan 2 - Platform (3-6 thang)

### 2.1 Multi-user
- [ ] He thong roles: admin, giao vien, hoc sinh, phu huynh
- [ ] Moi giao vien tao "gia su Lumi" voi prompt rieng
- [ ] Multi-tenant co ban (nhieu to chuc tren 1 instance)
- [ ] SSO/OAuth login (Google, Microsoft)

### 2.2 Noi dung
- [ ] Cong giao vien nap tai lieu PDF/DOC
- [ ] RAG (Retrieval-Augmented Generation) tu tai lieu nap vao
- [ ] Them mon hoc: Tieng Viet, Tieng Anh, Khoa hoc
- [ ] Ngan hang cau hoi + bai kiem tra

### 2.3 Ha tang
- [ ] Kubernetes deployment option
- [ ] Horizontal scaling cho microservices
- [ ] Centralized logging (ELK/Loki)
- [ ] Prometheus + Grafana monitoring
- [ ] CDN cho audio files

---

## Giai doan 3 - Marketplace (6-12 thang)

### 3.1 Marketplace
- [ ] Cho noi dung bai giang tuong tac
- [ ] Giao vien tao va ban khoa hoc
- [ ] Rating va review khoa hoc
- [ ] Thanh toan va phan chia doanh thu

### 3.2 AI nang cao
- [ ] Adaptive learning path (tu dong dieu chinh do kho)
- [ ] Phan tich cam xuc tu giong noi (phat hien hoc sinh gap kho khan)
- [ ] Multi-modal: nhan dien bai lam qua camera
- [ ] Personalized learning model cho tung hoc sinh

### 3.3 Mo rong
- [ ] Mobile app (React Native)
- [ ] Offline mode (toan bo chay local)
- [ ] API public cho 3rd-party integration

---

## Nguyen tac phat trien

1. **Voice-first**: Moi tinh nang moi phai ho tro tuong tac giong noi
2. **Self-hosted**: Du lieu hoc sinh luon nam trong ha tang so huu
3. **Incremental**: Ship nho, thuong xuyen, do luong tac dong
4. **Backward compatible**: Khong break API/data khi nang cap
5. **Provider agnostic**: Moi thanh phan AI (STT, LLM, TTS) phai thay doi duoc ma khong anh huong he thong
