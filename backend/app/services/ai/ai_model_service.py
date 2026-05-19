# -*- coding: utf-8 -*-
"""
Phase 5 - AI 模型配置服务
支持 MiniMax / OpenAI / Anthropic 等多模型接入
"""
import os
import json
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.base import Base
from app.models.ai_model_config import AIModelConfig
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Index
from sqlalchemy.sql import func


class AIModelProvider:
    """AI 模型供应商定义"""

    PROVIDERS = {
        "minimax": {
            "name": "MiniMax",
            "models": ["MiniMax-M2.7"],
            "supports_temperature": True,
            "supports_system": True,
            "requires_group_id": True,
            "default_base_url": "https://api.minimax.chat/v1",
            "auth_type": "bearer",
            "param_format": "minimax",
        },
        "openai": {
            "name": "OpenAI",
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            "supports_temperature": True,
            "supports_system": True,
            "requires_group_id": False,
            "default_base_url": "https://api.openai.com/v1",
            "auth_type": "bearer",
            "param_format": "openai",
        },
        "anthropic": {
            "name": "Anthropic Claude",
            "models": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"],
            "supports_temperature": True,
            "supports_system": True,
            "requires_group_id": False,
            "default_base_url": "https://api.anthropic.com/v1",
            "auth_type": "anthropic",
            "param_format": "anthropic",
        },
        "deepseek": {
            "name": "DeepSeek",
            "models": ["deepseek-chat", "deepseek-coder"],
            "supports_temperature": True,
            "supports_system": True,
            "requires_group_id": False,
            "default_base_url": "https://api.deepseek.com/v1",
            "auth_type": "bearer",
            "param_format": "openai",
        },
        "custom": {
            "name": "自定义",
            "models": [],
            "supports_temperature": True,
            "supports_system": True,
            "requires_group_id": False,
            "default_base_url": "",
            "auth_type": "bearer",
            "param_format": "openai",
        },
    }

    @classmethod
    def get_providers(cls) -> dict:
        """获取所有供应商定义（不含敏感信息）"""
        return cls.PROVIDERS


class AIModelService:
    """AI 模型配置与调用服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 配置管理 ====================

    def get_configs(self, include_disabled: bool = False) -> List[dict]:
        """获取所有模型配置"""
        query = self.db.query(AIModelConfig)
        if not include_disabled:
            query = query.filter(AIModelConfig.enabled == True)
        configs = query.order_by(AIModelConfig.is_default.desc(), AIModelConfig.id).all()
        return [self._serialize(c, include_secret=True) for c in configs]

    def get_default_config(self) -> Optional[dict]:
        """获取默认模型配置"""
        config = self.db.query(AIModelConfig).filter(
            AIModelConfig.is_default == True,
            AIModelConfig.enabled == True,
        ).first()
        if not config:
            config = self.db.query(AIModelConfig).filter(
                AIModelConfig.enabled == True,
            ).first()
        return self._serialize(config) if config else None

    def get_config(self, config_id: int) -> Optional[dict]:
        config = self.db.query(AIModelConfig).filter(AIModelConfig.id == config_id).first()
        return self._serialize(config, include_secret=True) if config else None

    def get_providers(self) -> dict:
        return AIModelProvider.get_providers()

    def create_config(self, **kwargs) -> dict:
        """创建模型配置"""
        try:
            # 如果设为默认，先取消其他默认
            if kwargs.get("is_default"):
                self.db.query(AIModelConfig).filter(
                    AIModelConfig.is_default == True
                ).update({"is_default": False})

            config = AIModelConfig(**kwargs)
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)

            # 如果是第一个配置，设为默认
            count = self.db.query(AIModelConfig).count()
            if count == 1:
                config.is_default = True
                self.db.commit()

            return {"success": True, "config_id": config.id}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def update_config(self, config_id: int, **kwargs) -> dict:
        """更新模型配置"""
        try:
            config = self.db.query(AIModelConfig).filter(AIModelConfig.id == config_id).first()
            if not config:
                return {"success": False, "error": "Config not found"}

            # 如果设为默认，先取消其他默认
            if kwargs.get("is_default"):
                self.db.query(AIModelConfig).filter(
                    AIModelConfig.is_default == True,
                    AIModelConfig.id != config_id,
                ).update({"is_default": False})

            for key, value in kwargs.items():
                if value is not None or key in ["enabled"]:
                    setattr(config, key, value)

            self.db.commit()
            return {"success": True}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def delete_config(self, config_id: int) -> dict:
        """删除模型配置"""
        try:
            config = self.db.query(AIModelConfig).filter(AIModelConfig.id == config_id).first()
            if not config:
                return {"success": False, "error": "Config not found"}
            self.db.delete(config)
            self.db.commit()
            return {"success": True}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def set_default(self, config_id: int) -> dict:
        """设为默认模型"""
        try:
            self.db.query(AIModelConfig).filter(
                AIModelConfig.is_default == True
            ).update({"is_default": False})

            config = self.db.query(AIModelConfig).filter(AIModelConfig.id == config_id).first()
            if not config:
                return {"success": False, "error": "Config not found"}

            config.is_default = True
            config.enabled = True
            self.db.commit()
            return {"success": True}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def test_connection(self, config_id: int) -> dict:
        """测试模型连接"""
        config = self.db.query(AIModelConfig).filter(AIModelConfig.id == config_id).first()
        if not config:
            return {"success": False, "error": "Config not found"}

        try:
            result = self._call_llm(
                config=config,
                messages=[{"role": "user", "content": "Say 'OK' in exactly one word."}],
                timeout=15,
            )
            if result.get("success"):
                return {"success": True, "response": result.get("content", "OK")}
            else:
                return {"success": False, "error": result.get("error", "Unknown error")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== LLM 调用 ====================

    def chat(
        self,
        messages: List[dict],
        config_id: int = None,
        model: str = None,
        temperature: int = None,
        max_tokens: int = None,
        timeout: int = 30,
    ) -> dict:
        """
        调用 LLM 生成回复
        messages: [{"role": "user"/"assistant"/"system", "content": "..."}]
        """
        if config_id:
            config = self.db.query(AIModelConfig).filter(AIModelConfig.id == config_id).first()
        else:
            config = self.db.query(AIModelConfig).filter(
                AIModelConfig.is_default == True,
                AIModelConfig.enabled == True,
            ).first()

        if not config:
            return {"success": False, "error": "No AI model configured"}

        return self._call_llm(
            config=config,
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

    def _call_llm(
        self,
        config: AIModelConfig,
        messages: List[dict],
        model: str = None,
        temperature: int = None,
        max_tokens: int = None,
        timeout: int = 30,
    ) -> dict:
        """实际调用 LLM API"""
        provider = AIModelProvider.PROVIDERS.get(config.provider, {})
        fmt = provider.get("param_format", "openai")
        base_url = config.base_url or provider.get("default_base_url", "")

        try:
            if fmt == "minimax":
                return self._call_minimax(config, messages, base_url, model, temperature, timeout)
            elif fmt == "anthropic":
                return self._call_anthropic(config, messages, base_url, temperature, timeout)
            else:
                return self._call_openai_compatible(config, messages, base_url, model, temperature, timeout)
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timeout"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection failed, check base_url"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _call_minimax(
        self,
        config: AIModelConfig,
        messages: list,
        base_url: str,
        model: str,
        temperature: int,
        timeout: int,
    ) -> dict:
        """调用 MiniMax 原生 API"""
        url = f"{base_url}/text/chatcompletion_v2"
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }
        actual_temp = temperature if temperature is not None else config.temperature
        payload = {
            "model": model or config.model,
            "group_id": config.group_id or "",
            "messages": messages,
            "temperature": actual_temp / 10 if actual_temp else 0.7,
            "tokens_to_generate": config.max_tokens or 4096,
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if resp.status_code != 200:
            return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}

        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            return {"success": False, "error": f"Empty response: {data}"}

        content = choices[0].get("message", {}).get("content", "")
        return {
            "success": True,
            "content": content,
            "model": data.get("model", config.model),
            "usage": data.get("usage", {}),
            "id": data.get("id", ""),
        }

    def _call_anthropic(
        self,
        config: AIModelConfig,
        messages: list,
        base_url: str,
        temperature: int,
        timeout: int,
    ) -> dict:
        """调用 Anthropic / MiniMax Anthropic兼容模式 API"""
        url = f"{base_url}/messages"
        headers = {
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        # MiniMax group_id（通过专用 header）
        if config.group_id:
            headers["x-gm-api-key"] = config.group_id

        # 从 messages 中提取 system
        system = ""
        filtered_messages = []
        for m in messages:
            if m.get("role") == "system":
                system = m.get("content", "")
            else:
                filtered_messages.append({"role": m["role"], "content": m["content"]})

        actual_temp = temperature if temperature is not None else config.temperature
        payload = {
            "model": config.model,
            "messages": filtered_messages,
            "max_tokens": config.max_tokens or 4096,
        }
        if system:
            payload["system"] = system
        if actual_temp is not None and actual_temp > 0:
            payload["temperature"] = actual_temp / 10

        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if resp.status_code != 200:
            return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}

        data = resp.json()
        return {
            "success": True,
            "content": data.get("content", [{}])[0].get("text", ""),
            "model": data.get("model", config.model),
            "usage": data.get("usage", {}),
            "id": data.get("id", ""),
        }

    def _call_openai_compatible(
        self,
        config: AIModelConfig,
        messages: list,
        base_url: str,
        model: str,
        temperature: int,
        timeout: int,
    ) -> dict:
        """调用 OpenAI 兼容格式 API (OpenAI/DeepSeek/等)"""
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }
        actual_temp = temperature if temperature is not None else config.temperature
        payload = {
            "model": model or config.model,
            "messages": messages,
            "max_tokens": config.max_tokens or 4096,
        }
        if actual_temp is not None and actual_temp > 0:
            payload["temperature"] = actual_temp / 10

        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if resp.status_code != 200:
            return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}

        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            return {"success": False, "error": f"Empty response: {data}"}

        content = choices[0].get("message", {}).get("content", "")
        return {
            "success": True,
            "content": content,
            "model": data.get("model", config.model),
            "usage": data.get("usage", {}),
            "id": data.get("id", ""),
        }

    def _serialize(self, config: AIModelConfig, include_secret: bool = False) -> dict:
        if not config:
            return None
        result = {
            "id": config.id,
            "name": config.name,
            "provider": config.provider,
            "provider_name": AIModelProvider.PROVIDERS.get(config.provider, {}).get("name", config.provider),
            "model": config.model,
            "base_url": config.base_url,
            "group_id": config.group_id,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "enabled": config.enabled,
            "is_default": config.is_default,
            "extra_config": config.extra_config or {},
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None,
        }
        if include_secret and config.api_key:
            result["api_key"] = config.api_key
            result["api_key_masked"] = config.api_key[:12] + "***" + config.api_key[-4:] if len(config.api_key) > 16 else "***"
        return result
