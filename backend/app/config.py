# -*- coding: utf-8 -*-
"""
Phase 4 - 共享配置
"""
import os

# JWT 配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 调试台在服务端执行请求时，遇到前端开发代理地址需要回写到真实后端地址
DEBUG_PROXY_ORIGIN = os.getenv("DEBUG_PROXY_ORIGIN", "http://localhost:3000")
DEBUG_API_ORIGIN = os.getenv("DEBUG_API_ORIGIN", "http://localhost:8000")
