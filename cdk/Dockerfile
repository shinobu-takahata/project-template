FROM node:20-alpine

WORKDIR /cdk

# AWS CDK CLIグローバルインストール
RUN npm install -g aws-cdk

# 依存関係インストール用の準備
COPY package*.json ./
RUN npm install

CMD ["sh"]
