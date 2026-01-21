FROM node:20-slim

WORKDIR /cdk

# 必要なツールをインストール
RUN apt-get update && apt-get install -y \
    git \
    bash \
    && rm -rf /var/lib/apt/lists/*

# AWS CDK CLIグローバルインストール
RUN npm install -g aws-cdk

# 依存関係インストール用の準備
COPY package*.json ./
RUN npm install

# アプリケーションコードはvolume経由でマウント

CMD ["tail", "-f", "/dev/null"]
