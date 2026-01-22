FROM node:20-slim

WORKDIR /cdk

# 必要なツールをインストール
RUN apt-get update && apt-get install -y \
    git \
    bash \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# AWS CLI v2のインストール (ARM64対応)
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then \
        curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"; \
    else \
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"; \
    fi && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf awscliv2.zip aws

# AWS CDK CLIグローバルインストール
RUN npm install -g aws-cdk

# 依存関係インストール用の準備
COPY package*.json ./
RUN npm install

# アプリケーションコードはvolume経由でマウント

CMD ["tail", "-f", "/dev/null"]
