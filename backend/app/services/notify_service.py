"""
Notify Service - 通知服务
支持钉钉、飞书、邮件、Webhook 通知
"""
import asyncio
import json
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any
import httpx

logger = logging.getLogger(__name__)


class NotifyService:
    """通知服务"""

    def __init__(self):
        pass

    async def send(
        self,
        channel_type: str,
        config: dict,
        message: dict
    ) -> bool:
        """
        发送通知
        channel_type: dingtalk / feishu / email / webhook
        config: 渠道配置（webhook_url, smtp配置等）
        message: 消息内容 {title, status, summary, details, report_url}
        返回: 是否发送成功
        """
        try:
            if channel_type == "dingtalk":
                return await self._send_dingtalk(config, message)
            elif channel_type == "feishu":
                return await self._send_feishu(config, message)
            elif channel_type == "email":
                return await self._send_email(config, message)
            elif channel_type == "webhook":
                return await self._send_webhook(config, message)
            else:
                logger.warning(f"Unknown channel type: {channel_type}")
                return False
        except Exception as e:
            logger.error(f"Failed to send notification via {channel_type}: {e}")
            return False

    async def notify_execution_result(
        self,
        result: dict,
        channels: list
    ):
        """
        发送执行结果通知
        result: 执行结果 {title, status, summary, details, report_url}
        channels: 渠道列表，每个元素为 {type, config}
        """
        tasks = []
        for channel in channels:
            channel_type = channel.get("type")
            config = channel.get("config", {})
            if channel_type:
                tasks.append(self.send(channel_type, config, result))

        # 并发发送所有通知
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_dingtalk(self, config: dict, message: dict) -> bool:
        """发送钉钉通知"""
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            logger.error("DingTalk webhook_url is required")
            return False

        title = message.get("title", "测试通知")
        status = message.get("status", "unknown")
        summary = message.get("summary", {})
        details = message.get("details", "")
        report_url = message.get("report_url", "")

        # 状态 emoji
        status_emoji = {
            "success": "✅",
            "failure": "❌",
            "error": "⚠️",
            "unknown": "❓"
        }.get(status, "❓")

        total = summary.get("total", 0)
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        rate = summary.get("rate", 0)

        # 构建 Markdown 消息
        details_section = ""
        if details:
            details_section = f"### 详情\n{details}\n"

        report_section = ""
        if report_url:
            report_section = f"### 报告\n[查看报告]({report_url})\n"

        markdown_content = f"""## {status_emoji} {title}

### 执行结果

| 指标 | 数值 |
|------|------|
| 总数 | {total} |
| 通过 | {passed} |
| 失败 | {failed} |
| 通过率 | {rate}% |

### 状态: {status.upper()}

{details_section}{report_section}"""

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": markdown_content
            }
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(webhook_url, json=payload)
                result = resp.json()
                return result.get("errcode", 1) == 0
        except Exception as e:
            logger.error(f"Failed to send DingTalk message: {e}")
            return False

    async def _send_feishu(self, config: dict, message: dict) -> bool:
        """发送飞书通知"""
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            logger.error("Feishu webhook_url is required")
            return False

        title = message.get("title", "测试通知")
        status = message.get("status", "unknown")
        summary = message.get("summary", {})
        details = message.get("details", "")
        report_url = message.get("report_url", "")

        status_emoji = {
            "success": "✅",
            "failure": "❌",
            "error": "⚠️",
            "unknown": "❓"
        }.get(status, "❓")

        total = summary.get("total", 0)
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        rate = summary.get("rate", 0)

        # 构建飞书消息
        details_line = ""
        if details:
            details_line = f"**详情**: {details}\n"

        report_line = ""
        if report_url:
            report_line = f"[查看报告]({report_url})\n"

        content = f"""**{status_emoji} {title}**

**执行结果**
- 总数: {total}
- 通过: {passed}
- 失败: {failed}
- 通过率: {rate}%

**状态**: {status.upper()}
{details_line}{report_line}"""

        payload = {
            "msg_type": "text",
            "content": {
                "text": content
            }
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(webhook_url, json=payload)
                result = resp.json()
                return result.get("code", 1) == 0
        except Exception as e:
            logger.error(f"Failed to send Feishu message: {e}")
            return False

    async def _send_email(self, config: dict, message: dict) -> bool:
        """发送邮件通知"""
        smtp_host = config.get("smtp_host", "smtp.gmail.com")
        smtp_port = config.get("smtp_port", 587)
        smtp_user = config.get("smtp_user")
        smtp_password = config.get("smtp_password")
        from_addr = config.get("from", smtp_user)
        to_addrs = config.get("to_addrs", [])

        if not smtp_user or not smtp_password:
            logger.error("SMTP user and password are required")
            return False
        if not to_addrs:
            logger.error("At least one recipient is required")
            return False

        title = message.get("title", "测试通知")
        status = message.get("status", "unknown")
        summary = message.get("summary", {})
        details = message.get("details", "")
        report_url = message.get("report_url", "")

        total = summary.get("total", 0)
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        rate = summary.get("rate", 0)

        # 颜色
        title_color = "#4CAF50" if status == "success" else "#F44336"
        title_icon = "✅" if status == "success" else "❌"

        # 详情和报告
        details_section = ""
        if details:
            details_section = f'<p style="margin-top: 16px;"><strong>详情:</strong><br>{details}</p>'

        report_section = ""
        if report_url:
            report_section = f'<p style="margin-top: 16px;"><a href="{report_url}" style="color: #2196F3;">查看详细报告</a></p>'

        # 构建 HTML 邮件内容
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: {title_color};">
                {title_icon} {title}
            </h2>
            <table style="border-collapse: collapse; width: 100%; max-width: 400px;">
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>总数</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{total}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>通过</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #4CAF50;">{passed}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>失败</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #F44336;">{failed}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>通过率</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>{rate}%</strong></td>
                </tr>
            </table>
            <p style="margin-top: 16px;"><strong>状态:</strong> <span style="color: {title_color};">{status.upper()}</span></p>
            {details_section}
            {report_section}
        </body>
        </html>
        """

        # 同步发送邮件（在异步函数中用线程池）
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._send_email_sync,
            smtp_host, smtp_port, smtp_user, smtp_password,
            from_addr, to_addrs, title, html_content
        )
        return True

    def _send_email_sync(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_addr: str,
        to_addrs: list,
        subject: str,
        html_content: str
    ):
        """同步发送邮件"""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_addr
            msg["To"] = ", ".join(to_addrs) if isinstance(to_addrs, list) else to_addrs

            msg.attach(MIMEText(html_content, "html", "utf-8"))

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(from_addr, to_addrs, msg.as_string())

            logger.info(f"Email sent successfully to {to_addrs}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise

    async def _send_webhook(self, config: dict, message: dict) -> bool:
        """发送 Webhook 通知"""
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            logger.error("Webhook URL is required")
            return False

        method = config.get("method", "POST").upper()
        headers = config.get("headers", {})

        # 包装消息
        payload = {
            "event": "execution_result",
            "data": message
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                kwargs = {"json": payload}
                if headers:
                    kwargs["headers"] = headers

                if method == "GET":
                    resp = await client.get(webhook_url, **kwargs)
                else:
                    resp = await client.post(webhook_url, **kwargs)

                return resp.status_code < 400
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            return False
