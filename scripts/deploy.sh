#!/bin/bash
# deploy.sh - 수동 배포 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 환경 변수 기본값
ENVIRONMENT=${1:-production}
IMAGE_TAG=${2:-latest}

echo -e "${GREEN}=== Issue Agent 배포 스크립트 ===${NC}"
echo "환경: ${ENVIRONMENT}"
echo "이미지 태그: ${IMAGE_TAG}"
echo ""

# .env 파일 확인
if [ ! -f ".env.${ENVIRONMENT}" ]; then
    echo -e "${RED}Error: .env.${ENVIRONMENT} 파일이 없습니다.${NC}"
    echo "먼저 .env.${ENVIRONMENT} 파일을 생성해주세요."
    exit 1
fi

# Docker 및 Docker Compose 설치 확인
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker가 설치되어 있지 않습니다.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose가 설치되어 있지 않습니다.${NC}"
    exit 1
fi

# 환경 변수 로드
export $(cat .env.${ENVIRONMENT} | grep -v '^#' | xargs)
export IMAGE_TAG=${IMAGE_TAG}
export GITHUB_REPOSITORY=${GITHUB_REPOSITORY:-caterpii/issue-agent}

echo -e "${YELLOW}이전 컨테이너 중지...${NC}"
docker-compose -f docker-compose.prod.yml down

echo -e "${YELLOW}최신 이미지 다운로드...${NC}"
docker-compose -f docker-compose.prod.yml pull

echo -e "${YELLOW}컨테이너 시작...${NC}"
docker-compose -f docker-compose.prod.yml up -d

echo -e "${YELLOW}서비스 시작 대기 중...${NC}"
sleep 10

echo -e "${YELLOW}서비스 상태 확인...${NC}"
docker-compose -f docker-compose.prod.yml ps

# Health check
echo -e "${YELLOW}백엔드 헬스 체크...${NC}"
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health || echo "000")

    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓ 백엔드가 정상적으로 실행 중입니다!${NC}"
        break
    fi

    attempt=$((attempt + 1))
    echo "헬스 체크 시도 ${attempt}/${max_attempts}... (응답 코드: ${response})"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}✗ 백엔드 헬스 체크 실패${NC}"
    echo "로그 확인:"
    docker-compose -f docker-compose.prod.yml logs backend
    exit 1
fi

echo -e "${YELLOW}프론트엔드 헬스 체크...${NC}"
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ || echo "000")

if [ "$response" = "200" ]; then
    echo -e "${GREEN}✓ 프론트엔드가 정상적으로 실행 중입니다!${NC}"
else
    echo -e "${YELLOW}⚠ 프론트엔드 응답 코드: ${response}${NC}"
fi

echo ""
echo -e "${GREEN}=== 배포 완료! ===${NC}"
echo "프론트엔드: http://localhost:8080"
echo "백엔드: http://localhost:5000"
echo ""
echo "로그 확인: docker-compose -f docker-compose.prod.yml logs -f"
echo "중지: docker-compose -f docker-compose.prod.yml down"
