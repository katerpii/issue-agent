#!/bin/bash
# rollback.sh - 이전 버전으로 롤백하는 스크립트

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ENVIRONMENT=${1:-production}
PREVIOUS_TAG=${2}

if [ -z "$PREVIOUS_TAG" ]; then
    echo -e "${RED}Error: 이전 이미지 태그를 지정해주세요.${NC}"
    echo "사용법: ./rollback.sh [environment] [previous_tag]"
    echo "예시: ./rollback.sh production v1.0.0"
    exit 1
fi

echo -e "${YELLOW}=== 롤백 시작 ===${NC}"
echo "환경: ${ENVIRONMENT}"
echo "이전 태그: ${PREVIOUS_TAG}"
echo ""

# 환경 변수 로드
if [ -f ".env.${ENVIRONMENT}" ]; then
    export $(cat .env.${ENVIRONMENT} | grep -v '^#' | xargs)
fi

export IMAGE_TAG=${PREVIOUS_TAG}
export GITHUB_REPOSITORY=${GITHUB_REPOSITORY:-caterpii/issue-agent}

echo -e "${YELLOW}현재 실행 중인 컨테이너 중지...${NC}"
docker-compose -f docker-compose.prod.yml down

echo -e "${YELLOW}이전 버전 이미지 확인...${NC}"
docker-compose -f docker-compose.prod.yml pull

echo -e "${YELLOW}이전 버전으로 컨테이너 시작...${NC}"
docker-compose -f docker-compose.prod.yml up -d

echo -e "${YELLOW}서비스 시작 대기 중...${NC}"
sleep 10

echo -e "${YELLOW}서비스 상태 확인...${NC}"
docker-compose -f docker-compose.prod.yml ps

# Health check
echo -e "${YELLOW}헬스 체크...${NC}"
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health || echo "000")

if [ "$response" = "200" ]; then
    echo -e "${GREEN}✓ 롤백 완료! 서비스가 정상 작동 중입니다.${NC}"
else
    echo -e "${RED}✗ 헬스 체크 실패 (응답 코드: ${response})${NC}"
    echo "로그 확인:"
    docker-compose -f docker-compose.prod.yml logs backend
    exit 1
fi
