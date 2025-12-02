# CI/CD 설정 가이드

## 요약

✅ **GitHub Secrets/Variables만 설정하면 자동 배포 가능**
❌ **`.env.prod` 파일은 서버에서 수동 배포할 때만 필요**

---

## GitHub Actions 자동 배포 설정 (5분)

### 1단계: GitHub Secrets 설정 (민감한 정보)

Repository > Settings > Secrets and variables > Actions > New repository secret

```bash
# 배포 서버 정보
DEPLOY_HOST          # 예: 123.456.789.0
DEPLOY_USER          # 예: ubuntu
DEPLOY_SSH_KEY       # SSH private key 전체 내용

# API Keys
BROWSER_USE_API_KEY  # Browser Use API 키
GOOGLE_API_KEY       # Google API 키

# SMTP (이메일 발송용)
SMTP_USERNAME        # 예: your-email@gmail.com
SMTP_PASSWORD        # Gmail 앱 비밀번호
SENDER_EMAIL         # 예: your-email@gmail.com
```

### 2단계: GitHub Variables 설정 (일반 설정)

Repository > Settings > Secrets and variables > Actions > Variables

```bash
# 포트 설정 (기본값 사용 시 생략 가능)
FRONTEND_PORT=8080
BACKEND_PORT=5000
REDIS_PORT=6379

# SMTP 설정 (기본값 사용 시 생략 가능)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_NAME=Issue Agent Bot

# 배포 경로 (기본값 사용 시 생략 가능)
DEPLOY_PATH=/opt/issue-agent
DEPLOY_PORT=22
```

### 3단계: SSH 키 생성 및 설정

```bash
# 로컬에서 SSH 키 생성
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions

# Public key를 서버에 추가
ssh-copy-id -i ~/.ssh/github_actions.pub user@your-server-ip

# 또는 수동으로
cat ~/.ssh/github_actions.pub
# 서버의 ~/.ssh/authorized_keys에 추가

# Private key를 GitHub Secret에 등록
cat ~/.ssh/github_actions
# 전체 내용을 복사하여 DEPLOY_SSH_KEY에 등록
```

### 4단계: 서버 초기 설정

```bash
# 서버에 SSH 접속
ssh user@your-server-ip

# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 배포 디렉토리 생성
sudo mkdir -p /opt/issue-agent
sudo chown $USER:$USER /opt/issue-agent

# 저장소 클론
cd /opt/issue-agent
git clone https://github.com/YOUR_USERNAME/issue-agent.git .
```

### 5단계: 배포 테스트

```bash
# main 브랜치에 푸시하면 자동 배포
git push origin main

# 또는 GitHub Actions 탭에서 수동 실행
# Actions > Continuous Deployment > Run workflow
```

---

## 배포 흐름

### 자동 배포 (GitHub Actions)

```
1. main 브랜치에 코드 푸시
   ↓
2. CI 워크플로우 실행
   - 린팅
   - 테스트
   - 보안 스캔
   ↓
3. CD 워크플로우 자동 실행
   - Docker 이미지 빌드
   - GitHub Container Registry에 푸시
   - SSH로 서버 접속
   - docker-compose로 배포
   - Health check
   ↓
4. 배포 완료 알림
```

### 수동 배포 (서버에서)

서버에서 직접 배포할 때만 `.env.prod` 파일 필요:

```bash
# 서버에 SSH 접속
ssh user@your-server-ip
cd /opt/issue-agent

# .env.prod 파일 생성
cp .env.prod.example .env.prod
nano .env.prod  # 값 입력

# 배포 스크립트 실행
./scripts/deploy.sh production latest
```

---

## 자주 묻는 질문 (FAQ)

### Q1: `.env.prod` 파일이 꼭 필요한가요?
**A:** 아니요! GitHub Actions 자동 배포를 사용하면 **GitHub Secrets/Variables만으로 충분**합니다. `.env.prod` 파일은 서버에서 수동 배포할 때만 필요합니다.

### Q2: GitHub Secrets와 Variables의 차이는?
**A:**
- **Secrets**: 암호화되어 저장, 민감한 정보 (API 키, 비밀번호, SSH 키)
- **Variables**: 평문으로 저장, 일반 설정 (포트, 서버 이름 등)

### Q3: 배포 후 확인 방법은?
**A:**
```bash
# 서비스 상태 확인
curl http://your-server-ip:5000/health
curl http://your-server-ip:8080/

# 로그 확인
ssh user@your-server-ip
cd /opt/issue-agent
docker-compose -f docker-compose.prod.yml logs -f
```

### Q4: 롤백은 어떻게 하나요?
**A:**
```bash
# 서버에서
ssh user@your-server-ip
cd /opt/issue-agent
./scripts/rollback.sh production v1.0.0

# 또는
export IMAGE_TAG=v1.0.0
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Q5: SMTP 설정이 안 되면?
**A:** Gmail 사용 시:
1. Google 계정 > 보안 > 2단계 인증 활성화
2. Google 계정 > 보안 > 앱 비밀번호 생성
3. 생성된 16자리 비밀번호를 `SMTP_PASSWORD`에 사용

---

## 모니터링

### Health Check

```bash
# Backend
curl http://your-server-ip:5000/health

# Frontend
curl http://your-server-ip:8080/

# Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

### 로그 확인

```bash
# 모든 서비스
docker-compose -f docker-compose.prod.yml logs -f

# 특정 서비스
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f scheduler
```

### 리소스 사용량

```bash
# 컨테이너 리소스
docker stats

# 디스크 사용량
docker system df
```

---

## 트러블슈팅

### 배포 실패 시

1. **GitHub Actions 로그 확인**
   - Actions 탭 > 실패한 워크플로우 클릭
   - 각 단계의 로그 확인

2. **서버 로그 확인**
   ```bash
   ssh user@your-server-ip
   cd /opt/issue-agent
   docker-compose -f docker-compose.prod.yml logs backend
   ```

3. **SSH 연결 문제**
   ```bash
   # 로컬에서 SSH 테스트
   ssh -i ~/.ssh/github_actions user@your-server-ip

   # 서버의 authorized_keys 확인
   cat ~/.ssh/authorized_keys
   ```

4. **환경 변수 누락**
   - GitHub Secrets/Variables 확인
   - 모든 필수 값이 설정되었는지 확인

---

## 보안 권장사항

1. **SSH 키 보호**
   - Private key는 절대 공개하지 않기
   - GitHub Secrets에만 저장

2. **방화벽 설정**
   ```bash
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 80/tcp   # HTTP
   sudo ufw allow 443/tcp  # HTTPS
   sudo ufw enable
   ```

3. **정기 업데이트**
   ```bash
   # 베이스 이미지 업데이트
   docker-compose -f docker-compose.prod.yml pull
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Secrets 로테이션**
   - API 키 정기적으로 변경
   - SMTP 비밀번호 정기적으로 변경

---

## 추가 리소스

- 상세 배포 가이드: [DEPLOYMENT.md](DEPLOYMENT.md)
- 프로젝트 README: [README.md](README.md)
- GitHub Actions 문서: https://docs.github.com/en/actions
- Docker Compose 문서: https://docs.docker.com/compose/

---

**문의사항**: GitHub Issues에 남겨주세요!
