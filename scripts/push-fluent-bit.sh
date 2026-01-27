#!/bin/bash

# Fluent Bit Dockerイメージをビルドし、ECRにプッシュするスクリプト

set -e

COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_BLUE='\033[0;34m'
COLOR_RESET='\033[0m'

echo -e "${COLOR_BLUE}================================================${COLOR_RESET}"
echo -e "${COLOR_BLUE}Fluent Bit Dockerイメージプッシュ${COLOR_RESET}"
echo -e "${COLOR_BLUE}================================================${COLOR_RESET}"
echo ""

# 環境の選択
echo "デプロイ先の環境を選択してください："
echo "1) dev"
echo "2) prod"
read -p "選択 (1 or 2): " ENV_CHOICE

case $ENV_CHOICE in
    1)
        ENV="dev"
        ;;
    2)
        ENV="prod"
        ;;
    *)
        echo -e "${COLOR_RED}❌ 無効な選択です${COLOR_RESET}"
        exit 1
        ;;
esac

echo -e "${COLOR_GREEN}✅ 環境: ${ENV}${COLOR_RESET}"
echo ""

# AWSアカウントIDの取得
echo -e "${COLOR_YELLOW}AWSアカウントIDを取得しています...${COLOR_RESET}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION="ap-northeast-1"

echo -e "${COLOR_GREEN}✅ AWSアカウントID: ${AWS_ACCOUNT_ID}${COLOR_RESET}"
echo ""

# ECRリポジトリ名
ECR_REPOSITORY="fluent-bit-custom-${ENV}"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
ECR_REPOSITORY_URI="${ECR_REGISTRY}/${ECR_REPOSITORY}"

echo -e "${COLOR_YELLOW}ECRにログインしています...${COLOR_RESET}"
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${ECR_REGISTRY}

echo -e "${COLOR_GREEN}✅ ECRログイン成功${COLOR_RESET}"
echo ""

# Dockerイメージのビルド
echo -e "${COLOR_YELLOW}Fluent Bit Dockerイメージをビルドしています...${COLOR_RESET}"
cd "$(dirname "$0")/../cdk/docker/fluent-bit"

# 設定ファイルの存在確認
if [ ! -f "fluent-bit.conf" ]; then
    echo -e "${COLOR_RED}❌ fluent-bit.conf が見つかりません${COLOR_RESET}"
    exit 1
fi

if [ ! -f "parsers.conf" ]; then
    echo -e "${COLOR_RED}❌ parsers.conf が見つかりません${COLOR_RESET}"
    exit 1
fi

# AMD64/x86_64向けにビルド（ECS Fargateで実行するため）
docker build --platform linux/amd64 -t ${ECR_REPOSITORY_URI}:latest .

# バージョンタグも作成（日付ベース）
VERSION_TAG=$(date +%Y%m%d-%H%M%S)
docker tag ${ECR_REPOSITORY_URI}:latest ${ECR_REPOSITORY_URI}:${VERSION_TAG}

echo -e "${COLOR_GREEN}✅ イメージビルド完了${COLOR_RESET}"
echo ""

# ECRにプッシュ
echo -e "${COLOR_YELLOW}ECRにイメージをプッシュしています...${COLOR_RESET}"
docker push ${ECR_REPOSITORY_URI}:latest
docker push ${ECR_REPOSITORY_URI}:${VERSION_TAG}

echo -e "${COLOR_GREEN}✅ イメージプッシュ完了${COLOR_RESET}"
echo ""

echo -e "${COLOR_BLUE}================================================${COLOR_RESET}"
echo -e "${COLOR_BLUE}プッシュされたイメージ${COLOR_RESET}"
echo -e "${COLOR_BLUE}================================================${COLOR_RESET}"
echo ""
echo -e "Repository: ${COLOR_GREEN}${ECR_REPOSITORY_URI}${COLOR_RESET}"
echo -e "Tags: ${COLOR_GREEN}latest, ${VERSION_TAG}${COLOR_RESET}"
echo ""

echo -e "${COLOR_YELLOW}次のステップ${COLOR_RESET}"
echo ""
echo "1. CDKでこのイメージを参照するように設定"
echo "   cdk/lib/stacks/compute-stack.ts で："
echo ""
echo "   const fluentBitRepository = ecr.Repository.fromRepositoryName("
echo "     this, 'FluentBitRepository',"
echo "     '${ECR_REPOSITORY}'"
echo "   );"
echo ""
echo "2. CDKスタックを再デプロイ"
echo "   cd cdk && npx cdk deploy ComputeStack-${ENV}"
echo ""
echo "3. ECSタスクでFluent Bitログルーターが起動します"
echo ""

echo -e "${COLOR_GREEN}Fluent Bitイメージのプッシュ完了！🎉${COLOR_RESET}"
