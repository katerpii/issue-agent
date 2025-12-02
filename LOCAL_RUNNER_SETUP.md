# WSL2에서 Self-hosted Runner 설정 가이드

## 빠른 설정 (5분)

### 1단계: GitHub에서 Linux Runner 설정 복사

1. GitHub 레포 > Settings > Actions > Runners > **New self-hosted runner**
2. **Linux** 선택 (Windows ❌)
3. Architecture: **x64** 선택

### 2단계: WSL2에서 Runner 설치

```bash
# 홈 디렉토리로 이동
cd ~

# Runner 폴더 생성
mkdir actions-runner && cd actions-runner

# Runner 다운로드 (GitHub에서 제공하는 명령어 복사해서 실행)
curl -o actions-runner-linux-x64-2.329.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.329.0/actions-runner-linux-x64-2.329.0.tar.gz

# 압축 해제
tar xzf ./actions-runner-linux-x64-2.329.0.tar.gz

# 설정 (GitHub에서 제공하는 토큰 사용!)
./config.sh --url https://github.com/katerpii/issue-agent --token YOUR_TOKEN_HERE

# 프롬프트 응답:
# - Enter the name of the runner group: [Enter] (기본값)
# - Enter the name of runner: [Enter] (기본값 사용)
# - Enter any additional labels: [Enter] (건너뛰기)
# - Enter name of work folder: [Enter] (기본값)
```

### 3단계: Runner 실행

```bash
# 현재 터미널에서 실행 (테스트용)
./run.sh

# 백그라운드 서비스로 실행 (권장)
sudo ./svc.sh install
sudo ./svc.sh start

# 상태 확인
sudo ./svc.sh status
```

### 4단계: GitHub Secrets 설정

Repository > Settings > Secrets and variables > Actions

**Secrets:**
```
BROWSER_USE_API_KEY=your_key
GOOGLE_API_KEY=your_key
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SENDER_EMAIL=your_email@gmail.com
```

**Variables:**
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_NAME=Issue Agent Bot
```

### 5단계: 테스트

```bash
# main 브랜치에 푸시
git add .
git commit -m "test: self-hosted runner"
git push origin main

# GitHub Actions 탭에서 "CD - Local Deployment" 워크플로우 확인
```

---

## Runner 관리 명령어

### 서비스 관리

```bash
cd ~/actions-runner

# 시작
sudo ./svc.sh start

# 중지
sudo ./svc.sh stop

# 상태 확인
sudo ./svc.sh status

# 제거
sudo ./svc.sh uninstall
```

### 로그 확인

```bash
# Runner 로그
cd ~/actions-runner
tail -f _diag/Runner_*.log

# Docker Compose 로그
cd /home/caterpii/2025/opensource/issue-agent
docker-compose logs -f
```

---

## 워크플로우 설명

### cd-local.yml (Self-hosted)
- `runs-on: self-hosted` 사용
- 로컬 WSL2에서 실행
- `docker-compose up` 으로 배포

### cd.yml (Cloud)
- `runs-on: ubuntu-latest` 사용
- GitHub 클라우드에서 실행
- SSH로 원격 서버 배포

---

## 트러블슈팅

### Q1: Runner가 offline 상태
```bash
# Runner 재시작
cd ~/actions-runner
sudo ./svc.sh restart

# 또는 수동 실행
./run.sh
```

### Q2: Permission denied
```bash
# Docker 그룹에 추가
sudo usermod -aG docker $USER

# 로그아웃 후 재로그인 또는
newgrp docker
```

### Q3: 포트 충돌 (8080, 5000)
```bash
# 사용 중인 포트 확인
sudo lsof -i :8080
sudo lsof -i :5000

# 기존 컨테이너 중지
docker-compose down
```

### Q4: GitHub Token 만료
```bash
# Runner 재설정
cd ~/actions-runner
./config.sh remove
./config.sh --url https://github.com/katerpii/issue-agent --token NEW_TOKEN
```

---

## 보안 주의사항

⚠️ **Public Repository에서 Self-hosted Runner 사용 시 주의!**

1. **Fork에서 악성 코드 실행 가능**
   - PR을 통해 악의적인 코드가 로컬에서 실행될 수 있음

2. **보안 강화 방법:**
   ```bash
   # Repository를 Private으로 변경 (권장)
   # Settings > General > Change repository visibility > Private

   # 또는 PR에서 자동 실행 비활성화
   # Settings > Actions > Fork pull request workflows
   # "Require approval for first-time contributors" 선택
   ```

3. **민감한 정보 보호:**
   - `.env` 파일 git에 커밋하지 않기
   - GitHub Secrets 사용

---

## 배포 흐름

```
1. 코드 푸시 (main 브랜치)
   ↓
2. GitHub Actions 트리거
   ↓
3. Self-hosted Runner (WSL2)에서 실행
   ↓
4. .env 파일 생성 (Secrets에서)
   ↓
5. docker-compose up -d
   ↓
6. Health check
   ↓
7. 배포 완료!
   - Frontend: http://localhost:8080
   - Backend: http://localhost:5000
```

---

## 대안: 로컬 개발 환경

Self-hosted runner 설정이 복잡하다면:

```bash
# 그냥 직접 실행 (더 간단!)
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

---

## 다음 단계

- [ ] Runner 설치 완료
- [ ] GitHub Secrets 설정
- [ ] 첫 배포 테스트
- [ ] 서비스로 실행 (`./svc.sh install`)
- [ ] 로그 모니터링

---

**문의:** GitHub Issues
