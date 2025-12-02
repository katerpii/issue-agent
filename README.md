# Issue Agent System

AI agent 기반 개인화 맞춤형 이슈 알림 시스템

## 개요

Issue Agent는 사용자의 관심사에 맞춘 이슈를 다양한 플랫폼에서 수집하고 필터링하여 제공하는 AI 기반 시스템입니다.

## 시스템 파이프라인

### 전체 파이프라인 (계획)

1. **Controller Agent** - 유저 폼 입력 및 플랫폼 에이전트 실행
2. **Platform Agents** - 각 플랫폼별 크롤링 (domains.txt 기반)
3. **Dynamic Agent Generation** - 미지원 도메인에 대한 LLM 기반 에이전트 생성
4. **Multi-tier Filtering**
   - 1차 필터: 제목 기반 (비즈니스 로직)
   - 2차 필터: 키워드 기반 HTML body 분석
   - 3차 필터: LLM 기반 유저 선호도 분석 (결과 5개 이하일 때만)
5. **Result Delivery** - 수집된 데이터 제공

### 현재 구현 상태 (Pipeline 1-2 완료)

현재 **파이프라인 1-2번**까지 구현되어 있습니다:

✅ **Pipeline 1 - Controller Agent**
- 사용자 폼 입력 받기 (키워드, 플랫폼, 기간, 디테일)
- Controller Agent가 요청된 플랫폼 에이전트들을 실행

✅ **Pipeline 2 - Platform Agents (실제 크롤링)**
- **Google Agent**: requests + BeautifulSoup을 사용한 Google 검색 크롤링
  - 날짜 범위 필터링 지원
  - 제목, URL, 스니펫 추출
  - Fallback 메커니즘
- **Reddit Agent**: PRAW (공식 API) 또는 웹 스크래핑
  - Reddit API 사용 시 더 안정적이고 빠른 크롤링
  - API 미설정 시 웹 스크래핑으로 자동 전환
  - 제목, URL, 내용, 스코어, 댓글 수 등 추출

## 프로젝트 구조

```
issue-agent/
├── main.py                    # 메인 실행 파일
├── controller.py              # Controller Agent
├── requirements.txt           # 의존성 패키지
├── README.md                  # 프로젝트 문서
│
├── agents/                    # 플랫폼 에이전트
│   ├── __init__.py
│   ├── base_agent.py         # 베이스 에이전트 클래스
│   ├── google_agent.py       # Google 크롤링 에이전트
│   └── reddit_agent.py       # Reddit 크롤링 에이전트
│
├── models/                    # 데이터 모델
│   ├── __init__.py
│   └── user_form.py          # 유저 폼 모델
│
├── config/                    # 설정
│   ├── __init__.py
│   └── settings.py           # 시스템 설정
│
├── utils/                     # 유틸리티
│   ├── __init__.py
│   ├── logger.py             # 로깅 유틸리티
│   └── retry.py              # 재시도 로직
│
└── data/                      # 데이터
    └── domains.txt           # 지원 도메인 목록
```

## 설치 및 실행

### 요구사항

- Python 3.8 이상

### 설치

```bash
# 저장소 클론 (또는 프로젝트 디렉토리로 이동)
cd issue-agent

# 의존성 설치
pip install -r requirements.txt

# 또는 가상환경 사용 권장
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Reddit API 설정 (선택사항, 권장)

Reddit Agent를 더 안정적으로 사용하려면 Reddit API 인증 정보를 설정하세요:

1. Reddit 앱 생성:
   - https://www.reddit.com/prefs/apps 방문
   - "create another app..." 클릭
   - 앱 이름 입력, "script" 타입 선택
   - redirect uri에 `http://localhost:8080` 입력
   - "create app" 클릭

2. 환경 변수 설정:
   ```bash
   # .env 파일 생성
   cp .env.example .env

   # .env 파일을 열어서 아래 정보 입력:
   # REDDIT_CLIENT_ID=your_client_id_here
   # REDDIT_CLIENT_SECRET=your_client_secret_here
   # REDDIT_USER_AGENT=IssueAgent/1.0
   ```

**참고**: Reddit API를 설정하지 않아도 웹 스크래핑으로 동작하지만, API 사용이 더 안정적입니다.

### 실행

```bash
python main.py
```

또는 실행 권한 부여 후:

```bash
chmod +x main.py
./main.py
```

### 사용 예시

```
Keywords (comma-separated): python, AI, machine learning
Platforms (comma-separated, e.g., google,reddit): google,reddit
Start date (YYYY-MM-DD): 2025-01-01
End date (YYYY-MM-DD): 2025-11-01
Detail (additional preferences): Focus on technical tutorials and best practices
```

실행 결과 예시:
```
[GOOGLE] Starting crawl...
  Keywords: python, AI, machine learning
  Period: 2025-01-01 ~ 2025-11-01
  Found 15 results

[REDDIT] Starting crawl...
  Keywords: python, AI, machine learning
  Period: 2025-01-01 ~ 2025-11-01
  Found 23 results

Total results collected: 38
```

## 주요 구성 요소

### 1. UserForm (models/user_form.py)

사용자 입력을 받아 검증하는 데이터 모델:
- keywords: 검색 키워드 리스트
- platforms: 플랫폼 이름 리스트
- start_date: 검색 시작 날짜
- end_date: 검색 종료 날짜
- detail: 추가 선호도 정보

### 2. ControllerAgent (controller.py)

플랫폼 에이전트들을 조율하는 중앙 컨트롤러:
- 사용자 입력 받기
- 적절한 플랫폼 에이전트 선택 및 실행
- 결과 수집 및 반환

### 3. Platform Agents (agents/)

각 플랫폼별 크롤링 에이전트:
- **BaseAgent**: 모든 에이전트의 추상 베이스 클래스
- **GoogleAgent**: Google 검색 크롤링
- **RedditAgent**: Reddit 포스트 크롤링

### 4. Configuration (config/settings.py)

시스템 설정 관리:
- 파일 경로 설정
- 타임아웃 설정
- 필터링 임계값 설정
- 지원 도메인 로드 및 검증

## 다음 단계 (향후 구현)

### ~~Pipeline 2: Platform Agents 구현~~ ✅ 완료
- [x] 실제 크롤링 로직 구현 (requests/BeautifulSoup)
- [x] domains.txt 기반 도메인 검증
- [x] 에러 핸들링 및 재시도 로직
- [x] Google 검색 크롤링 (날짜 필터 포함)
- [x] Reddit 크롤링 (PRAW API + 웹 스크래핑 fallback)

### Pipeline 3: Dynamic Agent Generation
- [ ] Platform Agent (LLM 기반) 구현
- [ ] HTML 파싱 및 크롤링 코드 생성
- [ ] 생성된 에이전트 저장 및 재사용

### Pipeline 4: Multi-tier Filtering
- [ ] 1차 필터: 제목 기반 필터링
- [ ] 2차 필터: 키워드 기반 본문 분석
- [ ] 3차 필터: LLM 기반 선호도 분석

### Pipeline 5: Result Delivery
- [ ] 결과 포맷팅 및 출력
- [ ] 결과 저장 (JSON/CSV)
- [ ] 이메일/알림 전송 (선택사항)

## 확장 가능성

### 새로운 플랫폼 에이전트 추가

```python
from agents.base_agent import BaseAgent

class MyCustomAgent(BaseAgent):
    def __init__(self):
        super().__init__(platform_name="mycustom")

    def crawl(self, keywords, start_date, end_date, detail=""):
        # 크롤링 로직 구현
        pass

    def is_supported_domain(self, domain):
        # 도메인 검증 로직
        pass

# controller.py에 등록
controller.add_agent('mycustom', MyCustomAgent())
```

## 배포 (Deployment)

### Docker Compose를 사용한 배포

이 프로젝트는 Docker Compose를 사용하여 쉽게 배포할 수 있습니다.

#### 빠른 시작

```bash
# 1. 환경 변수 설정
cp .env.prod.example .env.prod
nano .env.prod  # 필수 값들을 채워넣으세요

# 2. 배포 실행
./scripts/deploy.sh production latest
```

#### 포함된 서비스

- **Frontend**: JSP 기반 웹 인터페이스 (포트 8080)
- **Backend**: FastAPI 기반 REST API (포트 5000)
- **Redis**: 데이터 저장소 (포트 6379)
- **Scheduler**: 주기적 구독 확인 및 이메일 발송

#### CI/CD 파이프라인

GitHub Actions를 통한 자동 배포:

1. **CI (Pull Request)**: 린팅, 테스트, 보안 스캔
2. **Build & Push**: Docker 이미지 빌드 및 GitHub Container Registry에 푸시
3. **CD (Main branch)**: 서버에 자동 배포

자세한 배포 가이드는 [DEPLOYMENT.md](DEPLOYMENT.md)를 참조하세요.

### 주요 배포 명령어

```bash
# 서비스 시작
docker-compose -f docker-compose.prod.yml up -d

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f

# 서비스 중지
docker-compose -f docker-compose.prod.yml down

# 이전 버전으로 롤백
./scripts/rollback.sh production v1.0.0
```

## 라이선스

MIT License

## 기여

이슈 및 풀 리퀘스트를 환영합니다.

## 문의

프로젝트 관련 문의사항이 있으시면 이슈를 등록해주세요.
