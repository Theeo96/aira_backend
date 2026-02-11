# Aira Backend & Frontend

Real-time Audio Chat application using **FastAPI** (Backend) and **Next.js** (Frontend), powered by **Gemini 2.5 Flash Native Audio**.

## Project Structure
- `backend/`: FastAPI Server (WebSocket, Gemini Integration, Memory, Auth)
- `temp_front/`: Next.js Frontend (AudioContext, WebSocket Client, Login UI)
- `start_services.bat`: One-click startup script (Windows)

## 🚀 Team Onboarding Guide (Quick Start)

이 저장소를 클론(Clone) 받은 후, **로컬 환경에서 실행하기 위해 필수적으로 수행해야 하는 단계**입니다.
(`.env` 등 보안 파일과 빌드 아티팩트는 git에 포함되지 않으므로 직접 생성해야 합니다.)

### 1. Prerequisites (필수 환경)
- **Python 3.11** (Conda 권장)
- **Node.js 20+** (LTS 등 최신 버전 권장)
- **Git**
- **Azure Account** (Speech Service, OpenAI, Cosmos DB)
- **Google Cloud Console** (Gemini API)

### 2. Backend 설정 (Python)
```bash
cd backend
# 가상환경 생성 및 활성화 (권장)
# pip install -r requirements.txt
```
**[필수] `.env` 파일 생성**: `backend/` 폴더 안에 `.env` 파일을 만들고 아래 키를 입력하세요.

```ini
# backend/.env

# Google Gemini API
GEMINI_API_KEY=your_google_api_key_here

# Azure Speech Service (STT)
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=koreacentral

# Azure OpenAI (GPT-4o-mini for Memory Summarization)
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# Azure Cosmos DB (NoSQL)
AZURE_COSMOS_DB_ENDPOINT=https://your-cosmos-db.documents.azure.com:443/
AZURE_COSMOS_DB_KEY=your_primary_key
```

### 3. Frontend 설정 (Node.js)
```bash
cd ../temp_front
npm install
npm run build
```
*(주의: `npm run build`를 해야 백엔드에서 프론트엔드 화면을 서빙할 수 있습니다.)*

### 4. 통합 실행 (Integrated Mode)
프로젝트 루트(`aira_backend/`)에서 아래 스크립트를 실행하세요.
```bash
# Windows
start_services.bat
```
- **접속 주소**: `http://localhost:8000` (브라우저)
- **외부 접속**: `ngrok http 8000`

---

## 💡 사용 가이드 (Features)

### 1. Google 로그인 (Login)
- 웹 페이지에 접속하면 **"Google Login"** 버튼이 나타납니다.
- 버튼을 누르면 새 창에서 구글 로그인을 진행하고, **이메일(토큰)**을 복사할 수 있습니다.
- 복사한 이메일을 입력창에 붙여넣고 "Enter Aira"를 누르면 접속됩니다.

### 2. 기억 (Memory) & 회상 (Recall)
- **대화 저장**: 대화를 나누고 **페이지를 새로고침**하거나 **로그아웃**하면, 대화 내용이 자동으로 요약되어 **Azure Cosmos DB**에 저장됩니다.
- **기억하기**: 다음에 다시 로그인하면, AI가 **과거의 모든 요약본**을 읽고 기억합니다. ("지난번에 말씀하신 그 맛집 다녀오셨나요?" 처럼 반응)

---

### 🛠️ 개발 팁 (Development Workflow)
- **Backend 수정 시**: `server.py`는 저장하면 자동 재시작(Reload) 됩니다. 하지만 `start_services.bat`을 재실행해야 완벽하게 반영되는 경우도 있습니다 (특히 환경변수 수정 시).
- **Frontend 수정 시**: UI만 빠르게 보고 싶다면 `cd temp_front && npm run dev` (Port 3000)를 별도로 띄워서 개발하세요. 단, 로그인 로직은 백엔드(8000번)와 연결되어야 정상 작동합니다.