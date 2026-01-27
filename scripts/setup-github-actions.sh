#!/bin/bash

# GitHub Actions デプロイ設定スクリプト
# このスクリプトは、GitHub ActionsからECSへのデプロイに必要な設定を確認・実行します

set -e

COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_BLUE='\033[0;34m'
COLOR_RESET='\033[0m'

echo -e "${COLOR_BLUE}================================================${COLOR_RESET}"
echo -e "${COLOR_BLUE}GitHub Actions ECS デプロイセットアップ${COLOR_RESET}"
echo -e "${COLOR_BLUE}================================================${COLOR_RESET}"
echo ""

# AWSアカウントIDの取得
echo -e "${COLOR_YELLOW}AWSアカウントIDを取得しています...${COLOR_RESET}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${COLOR_RED}❌ AWSアカウントIDの取得に失敗しました${COLOR_RESET}"
    echo "AWS CLIが正しく設定されているか確認してください"
    exit 1
fi

echo -e "${COLOR_GREEN}✅ AWSアカウントID: ${AWS_ACCOUNT_ID}${COLOR_RESET}"
echo ""

# リージョンの確認
AWS_REGION=$(aws configure get region)
if [ -z "$AWS_REGION" ]; then
    AWS_REGION="ap-northeast-1"
fi
echo -e "${COLOR_GREEN}✅ リージョン: ${AWS_REGION}${COLOR_RESET}"
echo ""

# CDKスタックの出力値を確認
echo -e "${COLOR_YELLOW}CDKスタックの出力値を確認しています...${COLOR_RESET}"

ENVIRONMENTS=("dev" "prod")

for ENV in "${ENVIRONMENTS[@]}"; do
    echo ""
    echo -e "${COLOR_BLUE}--- ${ENV}環境 ---${COLOR_RESET}"
    
    # GitHub Actions Role ARN
    ROLE_ARN=$(aws cloudformation describe-stacks \
        --stack-name ComputeStack-${ENV} \
        --query "Stacks[0].Outputs[?ExportName=='${ENV}-GithubActionsRoleArn'].OutputValue" \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$ROLE_ARN" ]; then
        echo -e "${COLOR_YELLOW}⚠️  GitHub Actions Role: 未作成${COLOR_RESET}"
    else
        echo -e "${COLOR_GREEN}✅ GitHub Actions Role: ${ROLE_ARN}${COLOR_RESET}"
    fi
    
    # ECR Repository
    ECR_REPO=$(aws cloudformation describe-stacks \
        --stack-name ComputeStack-${ENV} \
        --query "Stacks[0].Outputs[?ExportName=='${ENV}-EcrRepositoryUri'].OutputValue" \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$ECR_REPO" ]; then
        echo -e "${COLOR_YELLOW}⚠️  ECR Repository: 未作成${COLOR_RESET}"
    else
        echo -e "${COLOR_GREEN}✅ ECR Repository: ${ECR_REPO}${COLOR_RESET}"
    fi
    
    # ECS Cluster
    ECS_CLUSTER=$(aws cloudformation describe-stacks \
        --stack-name ComputeStack-${ENV} \
        --query "Stacks[0].Outputs[?ExportName=='${ENV}-EcsClusterName'].OutputValue" \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$ECS_CLUSTER" ]; then
        echo -e "${COLOR_YELLOW}⚠️  ECS Cluster: 未作成${COLOR_RESET}"
    else
        echo -e "${COLOR_GREEN}✅ ECS Cluster: ${ECS_CLUSTER}${COLOR_RESET}"
    fi
    
    # ECS Service
    ECS_SERVICE=$(aws cloudformation describe-stacks \
        --stack-name ComputeStack-${ENV} \
        --query "Stacks[0].Outputs[?ExportName=='${ENV}-EcsServiceName'].OutputValue" \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$ECS_SERVICE" ]; then
        echo -e "${COLOR_YELLOW}⚠️  ECS Service: 未作成${COLOR_RESET}"
    else
        echo -e "${COLOR_GREEN}✅ ECS Service: ${ECS_SERVICE}${COLOR_RESET}"
    fi
done

echo ""
echo -e "${COLOR_BLUE}================================================${COLOR_RESET}"
echo -e "${COLOR_BLUE}GitHub Secrets設定${COLOR_RESET}"
echo -e "${COLOR_BLUE}================================================${COLOR_RESET}"
echo ""

echo "GitHub Actionsで使用するSecretは以下の1つだけです："
echo ""
echo -e "${COLOR_YELLOW}Settings > Secrets and variables > Actions > New repository secret${COLOR_RESET}"
echo ""
echo -e "Secret名: ${COLOR_GREEN}AWS_ACCOUNT_ID${COLOR_RESET}"
echo -e "値: ${COLOR_GREEN}${AWS_ACCOUNT_ID}${COLOR_RESET}"
echo ""
echo -e "${COLOR_BLUE}💡 OIDC認証を使用するため、AWS Access KeyやSecret Keyは不要です${COLOR_RESET}"
echo ""

# GitHub CLIがインストールされている場合、Secretを自動設定
if command -v gh &> /dev/null; then
    echo ""
    read -p "GitHub CLIを使用してSecretを自動設定しますか？ (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${COLOR_YELLOW}GitHub Secretを設定しています...${COLOR_RESET}"
        
        gh secret set AWS_ACCOUNT_ID -b "${AWS_ACCOUNT_ID}"
        
        echo -e "${COLOR_GREEN}✅ Secretの設定が完了しました${COLOR_RESET}"
    fi
else
    echo -e "${COLOR_YELLOW}💡 Tip: GitHub CLIをインストールすると、Secretの設定を自動化できます${COLOR_RESET}"
    echo "   https://cli.github.com/"
fi

echo ""
echo -e "${COLOR_BLUE}================================================${COLOR_RESET}"
echo -e "${COLOR_BLUE}次のステップ${COLOR_RESET}"
echo -e "${COLOR_BLUE}================================================${COLOR_RESET}"
echo ""
echo "1. GitHub Secretsが設定されていることを確認"
echo "2. CDKスタックをデプロイ（未デプロイの場合）"
echo "   cd cdk && npx cdk deploy --all"
echo "3. 初回のDockerイメージをビルド＆プッシュ"
echo "   ./scripts/initial-push.sh"
echo "4. mainまたはdevelopブランチにコミット＆プッシュしてデプロイ"
echo ""
echo -e "${COLOR_GREEN}セットアップ完了！🎉${COLOR_RESET}"
