# 배포 가이드 (Deployment Guide)

이 문서는 Issue Agent를 Docker Compose와 GitHub Actions를 사용하여 배포하는 방법을 설명합니다.

## 목차

1. [아키텍처](#아키텍처)
2. [사전 요구사항](#사전-요구사항)
3. [초기 서버 설정](#초기-서버-설정)
4. [환경 변수 설정](#환경-변수-설정)
5. [배포 방법](#배포-방법)
6. [CI/CD 파이프라인](#cicd-파이프라인)
7. [모니터링 및 관리](#모니터링-및-관리)
8. [트러블슈팅](#트러블슈팅)

---

## 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                     Docker Compose                       │
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐ │
│  │ Frontend │  │ Backend  │  │  Redis  │  │Scheduler │ │
│  │ (Tomcat) │─▶│ (FastAPI)│─▶│ (DB)    │◀─│ (Python) │ │
│  │  :8080   │  │  :5000   │  │ :6379   │  │          │ │
│  └──────────┘  └──────────┘  └─────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────┘
```

**구성 요소:**
- **Frontend**: JSP 기반 웹 인터페이스 (Tomcat 9.0)
- **Backend**: FastAPI 기반 REST API 서버
- **Redis**: 구독 정보 및 캐시 저장소
- **Scheduler**: 주기적으로 구독 상태 확인 및 이메일 발송

---

## 사전 요구사항

### 소프트웨어
- Docker 20.10+
- Docker Compose 2.0+
- Git
- (선택) GitHub CLI (`gh`)

### 서버 사양 (최소)
- CPU: 2 cores
- RAM: 4GB
- Disk: 20GB
- OS: Ubuntu 20.04+ / Debian 11+ / CentOS 8+

---

## 초기 서버 설정

### 1. Docker 설치

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 프로젝트 클론

```bash
# 배포 디렉토리 생성
sudo mkdir -p /opt/issue-agent
sudo chown $USER:$USER /opt/issue-agent

# 저장소 클론
cd /opt/issue-agent
git clone https://github.com/caterpii/issue-agent.git .
```

### 3. 방화벽 설정

```bash
# UFW 사용 시
sudo ufw allow 8080/tcp  # Frontend
sudo ufw allow 5000/tcp  # Backend (선택사항, 프록시 사용 시 불필요)
```

---

## 환경 변수 설정

환경 변수 설정은 배포 방식에 따라 다릅니다:

### 방법 1: GitHub Actions 자동 배포 (권장) ✅

**GitHub Secrets/Variables만 사용** - `.env.prod` 파일 불필요

Repository Settings > Secrets and variables에서 설정:

**Secrets** (민감한 정보):
```
DEPLOY_HOST=your.server.ip
DEPLOY_USER=deploy_user
DEPLOY_SSH_KEY=<SSH private key>
BROWSER_USE_API_KEY=your_api_key
GOOGLE_API_KEY=your_api_key
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SENDER_EMAIL=your_email@gmail.com
```

**Variables** (일반 설정):
```
FRONTEND_PORT=8080
BACKEND_PORT=5000
REDIS_PORT=6379
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_NAME=Issue Agent Bot
DEPLOY_PATH=/opt/issue-agent
```

### 방법 2: 서버에서 수동 배포 (선택사항)

**`.env.prod` 파일 사용**

```bash
# 1. 템플릿 복사
cp .env.prod.example .env.prod

# 2. 파일 편집
nano .env.prod
```

필수 설정 항목:
```env
# GitHub Container Registry
GITHUB_REPOSITORY=your-username/issue-agent
IMAGE_TAG=latest

# API Keys
BROWSER_USE_API_KEY=your_actual_api_key
GOOGLE_API_KEY=your_actual_api_key

# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SENDER_EMAIL=your_email@gmail.com
SENDER_NAME=Issue Agent Bot
```

### GitHub Container Registry 인증

```bash
# GitHub Personal Access Token 생성 (Settings > Developer settings > Personal access tokens)
# Permissions: read:packages

echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

---

## 배포 방법

### 방법 1: 자동 배포 스크립트 사용 (권장)

```bash
# 프로덕션 환경에 latest 태그로 배포
./scripts/deploy.sh production latest

# 특정 버전으로 배포
./scripts/deploy.sh production v1.0.0
```

### 방법 2: 수동 배포

```bash
# 환경 변수 로드
export $(cat .env.prod | grep -v '^#' | xargs)

# 이미지 다운로드
docker-compose -f docker-compose.prod.yml pull

# 서비스 시작
docker-compose -f docker-compose.prod.yml up -d

# 상태 확인
docker-compose -f docker-compose.prod.yml ps
```

### 방법 3: 로컬 빌드 후 배포

```bash
# 이미지 빌드
docker-compose -f docker-compose.prod.yml build

# 서비스 시작
docker-compose -f docker-compose.prod.yml up -d
```

---

## CI/CD 파이프라인

### GitHub Actions 워크플로우

프로젝트는 3개의 주요 워크플로우를 제공합니다:

#### 1. CI (Continuous Integration) - `ci.yml`

**트리거**: Pull Request → `main` 또는 `develop` 브랜치

**작업**:
- 코드 린팅
- 통합 테스트 실행
- 보안 스캔 (Trivy)

```yaml
# PR 생성 시 자동 실행
on:
  pull_request:
    branches: [main, develop]
```

#### 2. Build & Push - `build-and-push.yml`

**트리거**:
- `develop` 브랜치에 push
- 태그 push (`v*.*.*`)

**작업**:
- Docker 이미지 빌드
- GitHub Container Registry에 푸시

```bash
# 태그 생성 및 푸시로 이미지 빌드 트리거
git tag v1.0.0
git push origin v1.0.0
```

#### 3. CD (Continuous Deployment) - `cd.yml`

**트리거**:
- `main` 브랜치에 push
- 태그 push
- 수동 실행 (workflow_dispatch)

**작업**:
1. 모든 서비스 이미지 빌드 & 푸시
2. SSH로 서버 접속
3. 최신 코드 pull
4. Docker Compose로 서비스 재시작
5. Health check
6. 배포 상태 알림

### GitHub Secrets/Variables 설정

Repository Settings > Secrets and variables > Actions에서 설정:

#### Secrets (민감한 정보)
```
# 배포 서버 정보
DEPLOY_HOST=your.server.ip.address
DEPLOY_USER=deploy_user
DEPLOY_SSH_KEY=-----BEGIN OPENSSH PRIVATE KEY-----...

# API Keys
BROWSER_USE_API_KEY=your_key
GOOGLE_API_KEY=your_key

# SMTP
SMTP_USERNAME=your_email
SMTP_PASSWORD=your_app_password
SENDER_EMAIL=your_email@example.com
```

#### Variables (일반 설정)
```
# 포트 설정
FRONTEND_PORT=8080
BACKEND_PORT=5000
REDIS_PORT=6379

# SMTP 설정
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_NAME=Issue Agent Bot

# 배포 경로
DEPLOY_PATH=/opt/issue-agent
DEPLOY_PORT=22
```

> **참고**: GitHub Actions는 이 Secrets/Variables를 사용하므로 `.env.prod` 파일이 불필요합니다.

### 수동 배포 트리거

GitHub Actions 탭에서 "Continuous Deployment" 워크플로우 선택 후 "Run workflow" 버튼 클릭

---

## 모니터링 및 관리

### 로그 확인

```bash
# 모든 서비스 로그
docker-compose -f docker-compose.prod.yml logs -f

# 특정 서비스 로그
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f redis
docker-compose -f docker-compose.prod.yml logs -f scheduler
```

### 서비스 상태 확인

```bash
# 컨테이너 상태
docker-compose -f docker-compose.prod.yml ps

# 리소스 사용량
docker stats

# Health check
curl http://localhost:5000/health
curl http://localhost:8080/
```

### 서비스 재시작

```bash
# 모든 서비스
docker-compose -f docker-compose.prod.yml restart

# 특정 서비스
docker-compose -f docker-compose.prod.yml restart backend
```

### Redis 데이터 확인

```bash
# Redis CLI 접속
docker-compose -f docker-compose.prod.yml exec redis redis-cli

# Redis 명령어
> KEYS *
> GET subscription:user@example.com
> DBSIZE
```

### 이미지 업데이트

```bash
# 최신 이미지 다운로드
docker-compose -f docker-compose.prod.yml pull

# 재시작
docker-compose -f docker-compose.prod.yml up -d
```

### 롤백

```bash
# 이전 버전으로 롤백
./scripts/rollback.sh production v1.0.0

# 또는 수동으로
export IMAGE_TAG=v1.0.0
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### 서비스 중지

```bash
# 서비스 중지 (데이터 보존)
docker-compose -f docker-compose.prod.yml stop

# 서비스 중지 및 컨테이너 제거 (데이터 보존)
docker-compose -f docker-compose.prod.yml down

# 서비스 중지 및 볼륨까지 제거 (데이터 삭제!)
docker-compose -f docker-compose.prod.yml down -v
```

---

## 트러블슈팅

### 1. 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker-compose -f docker-compose.prod.yml logs backend

# 일반적인 원인:
# - 환경 변수 누락 → .env.prod 확인
# - 포트 충돌 → 사용 중인 포트 확인 (lsof -i :5000)
# - 이미지 다운로드 실패 → 네트워크 및 인증 확인
```

### 2. Health check 실패

```bash
# 백엔드 로그 확인
docker-compose -f docker-compose.prod.yml logs backend

# 수동 health check
curl -v http://localhost:5000/health

# 컨테이너 내부 접속
docker-compose -f docker-compose.prod.yml exec backend bash
```

### 3. Redis 연결 실패

```bash
# Redis 상태 확인
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping

# Redis 로그
docker-compose -f docker-compose.prod.yml logs redis

# 네트워크 확인
docker-compose -f docker-compose.prod.yml exec backend ping redis
```

### 4. 이메일 발송 실패

```bash
# Scheduler 로그 확인
docker-compose -f docker-compose.prod.yml logs scheduler

# SMTP 설정 확인
# - Gmail의 경우 "앱 비밀번호" 사용 필요
# - 2단계 인증 활성화 필요
```

### 5. 디스크 공간 부족

```bash
# 사용하지 않는 이미지 정리
docker image prune -a

# 사용하지 않는 볼륨 정리
docker volume prune

# 전체 정리 (주의!)
docker system prune -a --volumes
```

### 6. GitHub Container Registry 인증 실패

```bash
# 로그인 다시 시도
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin

# 토큰 권한 확인 (read:packages 필요)

# 수동 이미지 pull 테스트
docker pull ghcr.io/caterpii/issue-agent/backend:latest
```

---

## 보안 권장사항

1. **환경 변수 보호**
   ```bash
   chmod 600 .env.prod
   ```

2. **정기적인 업데이트**
   ```bash
   # 베이스 이미지 업데이트
   docker-compose -f docker-compose.prod.yml pull
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **방화벽 설정**
   - 필요한 포트만 열기
   - Reverse proxy (Nginx/Caddy) 사용 권장

4. **백업**
   ```bash
   # Redis 데이터 백업
   docker-compose -f docker-compose.prod.yml exec redis redis-cli SAVE
   cp /var/lib/docker/volumes/issue-agent_redis-data/_data/dump.rdb ./backup/
   ```

---

## 추가 리소스

- [Docker Compose 문서](https://docs.docker.com/compose/)
- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/)

---

## 문의 및 지원

문제가 발생하면 [GitHub Issues](https://github.com/caterpii/issue-agent/issues)에 제보해주세요.
