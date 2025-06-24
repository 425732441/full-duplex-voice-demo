#!/bin/bash

# 获取最新的commit hash前7位
COMMIT_HASH=$(git rev-parse --short HEAD)

# 获取当前日期和时间
DATE=$(date +%Y%m%d)
TIME=$(date +%H%M)

# 构建标签
IMAGE_TAG="harbor.lightark.cc/iagent/full-duplex-demo-backend:${COMMIT_HASH}-${DATE}-${TIME}"

# 构建镜像
echo "Building image: ${IMAGE_TAG}"
docker build -t ${IMAGE_TAG} .


echo "Build completed: ${IMAGE_TAG}" 