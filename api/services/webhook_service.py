import httpx
import hmac
import hashlib
import json
import asyncio
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class WebhookService:
    """Service for sending webhook notifications"""
    
    def __init__(self):
        self.timeout = 30.0  # seconds
        self.max_retries = 3
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC-SHA256 signature for payload"""
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def send_webhook(
        self,
        url: str,
        event_type: str,
        payload: dict,
        secret: Optional[str] = None
    ) -> bool:
        """
        Send webhook notification.
        Returns True if successful, False otherwise.
        """
        try:
            body = {
                "event": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": payload
            }
            body_str = json.dumps(body, default=str)
            
            headers = {
                "Content-Type": "application/json",
                "X-TPA-Event": event_type,
                "X-TPA-Timestamp": datetime.utcnow().isoformat()
            }
            
            if secret:
                signature = self._generate_signature(body_str, secret)
                headers["X-TPA-Signature"] = f"sha256={signature}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for attempt in range(self.max_retries):
                    try:
                        response = await client.post(url, content=body_str, headers=headers)
                        if response.status_code in [200, 201, 202, 204]:
                            logger.info(f"Webhook sent successfully to {url}")
                            return True
                        else:
                            logger.warning(f"Webhook returned {response.status_code}: {response.text}")
                    except httpx.RequestError as e:
                        logger.warning(f"Webhook attempt {attempt + 1} failed: {e}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            logger.error(f"All webhook attempts failed for {url}")
            return False
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return False
    
    async def notify_batch_progress(
        self,
        webhook_url: str,
        webhook_secret: Optional[str],
        job_id: str,
        progress_percent: float,
        completed_items: int,
        failed_items: int,
        total_items: int
    ) -> bool:
        """Send batch progress notification"""
        return await self.send_webhook(
            url=webhook_url,
            event_type="batch.progress",
            payload={
                "job_id": job_id,
                "progress_percent": progress_percent,
                "completed_items": completed_items,
                "failed_items": failed_items,
                "total_items": total_items
            },
            secret=webhook_secret
        )
    
    async def notify_batch_completed(
        self,
        webhook_url: str,
        webhook_secret: Optional[str],
        job_id: str,
        status: str,
        results: list,
        total_items: int,
        completed_items: int,
        failed_items: int
    ) -> bool:
        """Send batch completion notification"""
        return await self.send_webhook(
            url=webhook_url,
            event_type="batch.completed",
            payload={
                "job_id": job_id,
                "status": status,
                "total_items": total_items,
                "completed_items": completed_items,
                "failed_items": failed_items,
                "results": results
            },
            secret=webhook_secret
        )

# Singleton instance
webhook_service = WebhookService()