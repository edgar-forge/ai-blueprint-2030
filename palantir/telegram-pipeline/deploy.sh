#!/bin/bash
# Lambda 배포 패키지 생성 스크립트
# boto3는 Lambda 런타임에 기본 포함이므로 별도 패키징 불필요

set -e

FUNCTION_NAME="obsidian-telegram-pipeline"
REGION="us-east-1"
ZIP_FILE="lambda_package.zip"

echo "=== Lambda 배포 패키지 생성 ==="

# 기존 zip 삭제
rm -f "$ZIP_FILE"

# Python 모듈 패키징 (boto3는 Lambda에 내장)
zip "$ZIP_FILE" lambda_function.py system_prompt.py bridge_keywords.py

echo "=== 패키지 생성 완료: $ZIP_FILE ==="

# Lambda 함수가 이미 있으면 업데이트, 없으면 안내
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" 2>/dev/null; then
    echo "=== 기존 함수 업데이트 ==="
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://$ZIP_FILE" \
        --region "$REGION"
    echo "=== 업데이트 완료 ==="
else
    echo ""
    echo "Lambda 함수가 아직 없습니다. 아래 단계를 따라 생성하세요:"
    echo ""
    echo "1. AWS 콘솔 → Lambda → 함수 생성"
    echo "   - 함수 이름: $FUNCTION_NAME"
    echo "   - 런타임: Python 3.12"
    echo "   - 아키텍처: arm64 (비용 절감)"
    echo "   - 타임아웃: 90초 (Opus 깊은 사고 시간 필요)"
    echo "   - 메모리: 256MB"
    echo ""
    echo "2. 환경변수 설정:"
    echo "   - TELEGRAM_BOT_TOKEN: (텔레그램 봇 토큰)"
    echo "   - GITHUB_TOKEN: (GitHub Personal Access Token)"
    echo "   - GITHUB_REPO: your-username/your-vault-repo"
    echo "   - BEDROCK_MODEL_ID: anthropic.claude-sonnet-4-20250514"
    echo "   - AWS_BEDROCK_REGION: us-east-1"
    echo ""
    echo "3. IAM 역할에 Bedrock 권한 추가:"
    echo '   { "Effect": "Allow", "Action": "bedrock:InvokeModel", "Resource": "*" }'
    echo ""
    echo "4. API Gateway (HTTP API) 트리거 추가"
    echo ""
    echo "5. 텔레그램 Webhook 등록:"
    echo '   curl "https://api.telegram.org/bot{TOKEN}/setWebhook?url={API_GATEWAY_URL}"'
fi
