# LumiEdu Frontend

Giao dien web cho nen tang gia su AI LumiEdu. Xay dung tren Next.js voi React va TypeScript.

## Cau truc

```
app/
├── (app)/                  # Route group voi Sidebar layout
│   ├── dashboard/page.tsx  # Trang chu: metrics, danh sach phien, tao phien moi
│   ├── progress/page.tsx   # Theo doi tien do hoc sinh
│   └── layout.tsx          # Sidebar + main content wrapper
├── login/page.tsx          # Trang dang nhap
├── session/page.tsx        # Giao dien chat tutoring (full-screen, khong sidebar)
├── page.tsx                # Redirect -> /login
└── layout.tsx              # Root layout (AuthProvider, fonts, metadata)

components/
├── chat/
│   ├── chat-bubble.tsx     # Tin nhan hoc sinh/AI voi audio playback
│   ├── chat-input.tsx      # Text input + mic button + send button
│   ├── session-header.tsx  # Header: topic, learner, WebSocket status, end
│   └── typing-indicator.tsx # Animation khi AI dang tra loi
├── ui/
│   ├── loading-spinner.tsx # Loading animation
│   ├── error-alert.tsx     # Error message display
│   ├── stat-card.tsx       # Dashboard metric card
│   └── session-card.tsx    # Session list item card
├── sidebar.tsx             # Navigation sidebar (Dashboard, Tien do, Dang xuat)
└── icons.tsx               # SVG icon components

lib/
├── api.ts                  # Centralized API client (fetch, error handling)
├── auth-context.tsx        # React Context: JWT token, login/logout, localStorage
├── types.ts                # TypeScript interfaces (Session, Turn, Progress, etc.)
└── hooks/
    ├── use-require-auth.ts # Hook: redirect ve /login neu chua dang nhap
    ├── use-poll.ts         # Hook: polling interval cho metrics refresh
    └── use-voice-recorder.ts # Hook: Web Audio API recording + base64 encoding
```

## Chay development

```bash
npm install
npm run dev
# -> http://localhost:3000
```

Luu y: Frontend goi API qua duong dan tuong doi `/api`. Khi chay ngoai Docker, can nginx hoac proxy de route `/api` toi backend API (port 8000).

**Khuyen nghi**: Chay toan bo stack qua Docker Compose tu thu muc goc:
```bash
cd ../..
docker compose up --build -d
# -> http://localhost (qua nginx)
```

## Cac lenh

```bash
npm run dev       # Development server voi hot reload
npm run build     # Production build
npm run start     # Chay production build
npm run lint      # ESLint check
```

## Luong chinh

1. **Login** (`/login`): Nhap email + password -> nhan JWT -> luu localStorage
2. **Dashboard** (`/dashboard`): Xem metrics, danh sach phien, click "Phien hoc moi"
3. **Session** (`/session?id=...`): Chat text hoac voice voi AI tutor
4. **Progress** (`/progress`): Nhap ma hoc sinh -> xem tien do, chu de da hoc

## API Client

Tat ca API calls di qua `lib/api.ts`:

```typescript
import { login, createSession, submitTurn, listSessions, getProgress } from '@/lib/api';

// Login
const { access_token } = await login(email, password);

// Tao phien hoc
const session = await createSession(token, learnerId, topic);

// Gui cau hoi
const turn = await submitTurn(token, sessionId, { text_input: "1/2 + 1/3?" });

// Xem tien do
const progress = await getProgress(token, learnerId);
```

## Voice Recording

Hook `useVoiceRecorder` su dung Web Audio API:
- MediaRecorder de ghi am tu microphone
- FileReader de encode sang base64 (khong bi crash voi audio lon)
- Gui audio_base64 qua `submitTurn` API
