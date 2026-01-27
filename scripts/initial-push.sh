#!/bin/bash

# 初回のDockerイメージをECRにプッシュするスクリプト
# GitHub Actionsデプロイ前に、ECSサービスが起動できるようにイメージを用意します

set -e

COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_BLUE='\033[0;34m'
COLOR_RESET='\033[0m'

echo -e "${COLOR_BLUE}================================================${COLOR_RESET}"
echo -e "${COLOR_BLUE}初回Dockerイメージプッシュ${COLOR_RESET}"
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
ECR_REPOSITORY="backend-${ENV}"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
ECR_REPOSITORY_URI="${ECR_REGISTRY}/${ECR_REPOSITORY}"

echo -e "${COLOR_YELLOW}ECRにログインしています...${COLOR_RESET}"
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${ECR_REGISTRY}

echo -e "${COLOR_GREEN}✅ ECRログイン成功${COLOR_RESET}"
echo ""

# Dockerイメージのビルド
echo -e "${COLOR_YELLOW}Dockerイメージをビルドしています...${COLOR_RESET}"
cd "$(dirname "$0")/../backend"

# AMD64/x86_64向けにビルド（ECS Fargateで実行するため）
docker build --platform linux/amd64 -t ${ECR_REPOSITORY_URI}:initial -f Dockerfile.dev .
docker tag ${ECR_REPOSITORY_URI}:initial ${ECR_REPOSITORY_URI}:latest

echo -e "${COLOR_GREEN}✅ イメージビルド完了${COLOR_RESET}"
echo ""

# ECRにプッシュ
echo -e "${COLOR_YELLOW}ECRにイメージをプッシュしています...${COLOR_RESET}"
docker push ${ECR_REPOSITORY_URI}:initial
docker push ${ECR_REPOSITORY_URI}:latest

echo -e "${COLOR_GREEN}✅ イメージプッシュ完了${COLOR_RESET}"
echo ""

echo -e "${COLOR_BLUE}================================================${COLOR_RESET}"
echo -e "${COLOR_BLUE}プッシュされたイメージ${COLOR_RESET}"
echo -e "${COLOR_BLUE}================================================${COLOR_RESET}"
echo ""
echo -e "Repository: ${COLOR_GREEN}${ECR_REPOSITORY_URI}${COLOR_RESET}"
echo -e "Tags: ${COLOR_GREEN}initial, latest${COLOR_RESET}"
echo ""

# ECSサービスのdesiredCountを更新するか確認
echo -e "${COLOR_YELLOW}次のステップ${COLOR_RESET}"
echo ""
echo "1. CDKの設定でECSのdesiredCountを更新"
echo "   cdk/lib/config/${ENV}.ts を編集："
echo ""
echo "   ecs: {"
echo "     desiredCount: 2,  // 0 → 2 に変更"
echo "     minCapacity: 2,   // 0 → 2 に変更"
echo "   }"
echo ""
echo "2. CDKスタックを再デプロイ"
echo "   cd cdk && npx cdk deploy ComputeStack-${ENV}"
echo ""
echo "3. GitHub Actionsでの自動デプロイが有効になります"
echo ""

echo -e "${COLOR_GREEN}初回セットアップ完了！🎉${COLOR_RESET}"
