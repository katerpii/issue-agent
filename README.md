# Issue Agent System

AI 기반 개인화 맞춤형 이슈 알림 시스템

[![CI](https://github.com/katerpii/issue-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/katerpii/issue-agent/actions/workflows/ci.yml)
[![CD](https://github.com/katerpii/issue-agent/actions/workflows/cd-local.yml/badge.svg)](https://github.com/katerpii/issue-agent/actions/workflows/cd-local.yml)

## 📌 개요

**Issue Agent**는 사용자의 관심 키워드를 기반으로 다양한 플랫폼(Google, Reddit, GitHub, ASEC, Apple 등)에서 이슈를 수집하고, **LLM을 활용해 관련도가 높은 결과만 필터링**하여 **이메일로 자동 전송**하는 시스템입니다.

### 핵심 특징

- 🤖 **AI 기반 필터링**: Gemini/Claude LLM을 사용한 지능형 결과 필터링
- 📧 **이메일 알림**: SMTP를 통한 HTML 포맷 이메일 자동 발송
- ⏰ **스케줄링**: 사용자 지정 시간에 자동 실행되는 구독 기능
- 🌐 **멀티 플랫폼**: Google, Reddit, GitHub, ASEC, Apple 등 5개 이상 플랫폼 지원
- 🔧 **동적 에이전트 생성**: 미지원 플랫폼도 LLM이 자동으로 크롤러 생성
- 🎯 **개인화**: 사용자 선호도 기반 결과 요약 및 추천
- 🐳 **컨테이너화**: Docker Compose 기반 간편한 배포
- 🚀 **CI/CD**: GitHub Actions 기반 자동화된 빌드/배포 파이프라인

---

## 🏗️ 시스템 아키텍처

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Frontend   │ ───▶ │   Backend    │ ───▶ │    Redis     │
│  (Tomcat)    │      │  (FastAPI)   │      │   (구독저장)  │
│  Port 8080   │      │  Port 5000   │      │  Port 6379   │
└──────────────┘      └──────┬───────┘      └──────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
              ┌─────▼──────┐   ┌───────▼────────┐
              │ Controller │   │   Scheduler    │
              │   Agent    │   │  (백그라운드)   │
              └─────┬──────┘   └────────────────┘
                    │
        ┌───────────┼───────────┬──────────┐
        │           │           │          │
    ┌───▼────┐ ┌───▼────┐ ┌───▼────┐ ┌──▼──────┐
    │ Google │ │ Reddit │ │ GitHub │ │ ASEC... │
    │ Agent  │ │ Agent  │ │ Agent  │ │ Agent   │
    └───┬────┘ └───┬────┘ └───┬────┘ └──┬──────┘
        └──────────┴───────────┴──────────┘
                    │
            ┌───────▼────────┐
            │ Result         │
            │ Processor      │
            │ (LLM Filter)   │
            └───────┬────────┘
                    │
            ┌───────▼────────┐
            │ Email Sender   │
            │ (SMTP)         │
            └────────────────┘
```

---

## ✨ 구현된 주요 기능

### 1. 멀티 플랫폼 크롤링
- ✅ **Google 검색**: browser-use 클라우드 기반 크롤링
- ✅ **Reddit**: 서브레딧 및 검색 결과 수집
- ✅ **GitHub**: 이슈, PR, 릴리즈 정보 수집
- ✅ **ASEC**: 보안 취약점 정보 크롤링
- ✅ **Apple Security**: 애플 보안 업데이트 정보
- ✅ **동적 에이전트 생성**: LLM이 자동으로 새로운 플랫폼 크롤러 생성

### 2. AI 기반 지능형 필터링 (result_processor.py)
```python
# 2단계 LLM 파이프라인
1. 필터링: 관련도 점수 0-10점 부여 (5점 이상만 통과)
2. 요약: 전체 결과를 2-3문장으로 요약

# 지원 LLM
- Gemini 2.0 Flash Lite (무료, 기본)
- Claude 3.5 Sonnet (유료, 대체)
```

### 3. 이메일 알림 시스템 (email_sender.py)
- HTML 템플릿 기반 보기 좋은 이메일
- 상위 10개 결과만 발송
- 관련도 점수 및 이유 표시
- SMTP 연동 (Gmail 지원)

### 4. 구독 관리 (subscription_checker.py)
```python
# Redis 기반 구독 저장
- 이메일 기반 구독 관리
- 사용자 지정 시간 알림 (예: 매일 09:00)
- 백그라운드 스케줄러 (cron-like)
- 구독 생성/조회/삭제/테스트 API
```

### 5. REST API (main.py)
```python
POST   /api/run                           # 즉시 검색 실행
POST   /api/subscriptions                 # 구독 생성
GET    /api/subscriptions/{email}         # 구독 목록 조회
DELETE /api/subscriptions/{email}/{id}    # 구독 삭제
POST   /api/subscriptions/{email}/{id}/test  # 구독 테스트
GET    /health                             # 헬스 체크
```

### 6. 웹 인터페이스 (frontend/)
- JSP 기반 심플한 UI
- 키워드/플랫폼 입력 폼
- 실시간 결과 표시
- 구독 생성 모달

---

## 🚀 빠른 시작

### Docker Compose로 실행 (권장)

```bash
# 1. 환경 변수 설정
cp .env.example .env
nano .env  # API 키 입력

# 2. 서비스 시작
docker compose up -d

# 3. 접속
# Frontend: http://localhost:8080
# Backend:  http://localhost:5000
```

### 로컬 실행 (개발용)

```bash
# Python 3.11+ 필요
pip install -r requirements.txt

# 환경 변수 설정
export BROWSER_USE_API_KEY=your_key
export GOOGLE_API_KEY=your_gemini_key

# CLI 모드
python main.py

# API 서버 모드
uvicorn main:app --host 0.0.0.0 --port 5000
```

---

## 📁 프로젝트 구조

```
issue-agent/
├── main.py                       # FastAPI 서버 + CLI 진입점
├── controller.py                 # 플랫폼 에이전트 오케스트레이션
├── result_processor.py           # LLM 기반 필터링/요약
├── email_sender.py               # 이메일 발송
├── subscription_checker.py       # 백그라운드 스케줄러
│
├── agents/                       # 플랫폼 크롤링 에이전트
│   ├── base_agent.py
│   ├── google_agent.py           # Google 검색
│   ├── reddit_agent.py           # Reddit 크롤링
│   ├── github_agent.py           # GitHub 이슈/PR
│   ├── asec_agent.py             # 보안 취약점
│   ├── apple_agent.py            # Apple 보안
│   ├── agent_template.py         # 자동 생성 템플릿
│   └── selector_extractor.py     # LLM 기반 셀렉터 추출
│
├── models/
│   └── user_form.py              # 사용자 입력 모델
│
├── config/
│   └── settings.py               # 시스템 설정
│
├── utils/
│   ├── logger.py
│   └── retry.py
│
├── frontend/                     # JSP 기반 웹 인터페이스
│   ├── Dockerfile
│   └── webapp/
│       ├── index.jsp
│       └── css/style.css
│
├── .github/workflows/            # CI/CD 파이프라인
│   ├── ci.yml                    # Pull Request 검증
│   ├── cd.yml                    # 클라우드 배포
│   └── cd-local.yml              # 로컬 배포
│
├── docker-compose.yml            # 개발 환경
├── docker-compose.prod.yml       # 프로덕션 환경
├── Dockerfile.backend
└── requirements.txt
```

---

## 🔧 환경 변수 설정

### 필수 환경 변수

```bash
# API Keys
BROWSER_USE_API_KEY=your_browser_use_api_key    # browser-use 클라우드
GOOGLE_API_KEY=your_gemini_api_key              # Gemini LLM

# SMTP (이메일 발송)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password                 # Gmail 앱 비밀번호
SENDER_EMAIL=your_email@gmail.com
SENDER_NAME=Issue Agent Bot

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
```

### Gmail 앱 비밀번호 생성

1. Google 계정 > 보안 > 2단계 인증 활성화
2. 앱 비밀번호 생성: https://myaccount.google.com/apppasswords
3. 생성된 16자리 비밀번호를 `SMTP_PASSWORD`에 사용

---

## 💻 사용 예시

### CLI 모드

```bash
$ python main.py

ISSUE AGENT SYSTEM v0.1
Available platforms: google, reddit, github, asec, apple

Keywords (comma-separated): python security vulnerability
Platforms (comma-separated): google,reddit
Detail: Focus on CVE and security best practices

[GOOGLE] Starting crawl... Found 25 results
[REDDIT] Starting crawl... Found 18 results

[PROCESSOR] Filtering 43 results...
[PROCESSOR] Filtered to 12 relevant results (score >= 5)

Summary: Found 12 highly relevant results on Python security
vulnerabilities, focusing on recent CVEs and mitigation strategies.

Total Results: 12
```

### API 호출

```bash
# 즉시 검색
curl -X POST http://localhost:5000/api/run \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["python", "security"],
    "platforms": ["google", "reddit"],
    "detail": "Focus on CVE"
  }'

# 구독 생성
curl -X POST http://localhost:5000/api/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "notification_time": "09:00",
    "keywords": ["python", "AI"],
    "platforms": ["google", "reddit"],
    "detail": "Focus on tutorials"
  }'
```

---

## 🎯 핵심 기술 스택

### Backend
- **Framework**: FastAPI (Python)
- **Web Crawling**: browser-use (클라우드 브라우저 자동화)
- **HTML Parsing**: BeautifulSoup4
- **LLM**: Gemini 2.0 Flash Lite / Claude 3.5 Sonnet
- **Email**: smtplib (SMTP)
- **Scheduler**: schedule (cron-like)
- **Storage**: Redis (구독 관리)

### Frontend
- **Server**: Apache Tomcat 9.0
- **Template**: JSP (Java Server Pages)
- **UI**: Vanilla JavaScript + CSS

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Image Registry**: GitHub Container Registry (GHCR)

---

## 📊 실행 흐름

### 1. 즉시 검색 (Interactive)

```
사용자 입력 → Controller Agent → 플랫폼 에이전트들 병렬 실행
→ 결과 수집 → LLM 필터링 → LLM 요약 → 결과 반환
```

### 2. 구독 알림 (Scheduled)

```
Scheduler 실행 (09:00) → Redis에서 구독 로드
→ Controller Agent 실행 → 결과 필터링
→ 이메일 발송 (HTML 포맷) → 타임스탬프 업데이트
```

---

## 🔐 보안 및 인증

- Redis 기반 구독 저장 (영구 저장 X)
- 이메일 기반 구독 (계정 시스템 없음)
- SMTP TLS 연결
- 환경 변수로 민감 정보 관리
- Docker Secrets 지원

---

## 🚢 배포

### Docker Compose (프로덕션)

```bash
# 프로덕션 환경 시작
docker compose -f docker-compose.prod.yml up -d

# 로그 확인
docker compose -f docker-compose.prod.yml logs -f

# 서비스 재시작
docker compose -f docker-compose.prod.yml restart

# 중지
docker compose -f docker-compose.prod.yml down
```

### CI/CD 파이프라인

```
PR 생성 → CI (Lint, Test, Security Scan)
   ↓
Merge → CD (Docker 빌드 & 푸시 & 배포)
   ↓
Health Check → 배포 완료
```

자세한 내용: [DEPLOYMENT.md](DEPLOYMENT.md) | [CICD_SETUP.md](CICD_SETUP.md)

---

## 📈 확장 가능성

### 새로운 플랫폼 추가

```python
# 1. 직접 구현
from agents.base_agent import BaseAgent

class MyPlatformAgent(BaseAgent):
    def __init__(self):
        super().__init__(platform_name="myplatform")

    async def crawl(self, keywords, detail=""):
        # 크롤링 로직 구현
        return results

# 2. 또는 LLM이 자동 생성
# controller가 자동으로 새 플랫폼 감지 & 에이전트 생성
```

### LLM 백엔드 변경

```python
# result_processor.py
# Gemini, Claude 외에도 추가 가능:
# - OpenAI GPT-4
# - Anthropic Claude
# - Cohere
# - Local LLM (Ollama)
```

---

## 🧪 테스트

```bash
# 단위 테스트
pytest tests/unit/

# 통합 테스트
pytest tests/integration/

# 이메일 연결 테스트
python -c "from email_sender import test_email_connection; test_email_connection()"
```

---

## 📝 라이선스

MIT License

---

## 🤝 기여

이슈 및 풀 리퀘스트를 환영합니다!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📧 문의

프로젝트 관련 문의사항이 있으시면 [GitHub Issues](https://github.com/katerpii/issue-agent/issues)에 등록해주세요.

---

## 🌟 Star History

프로젝트가 도움이 되었다면 ⭐️ Star를 눌러주세요!
