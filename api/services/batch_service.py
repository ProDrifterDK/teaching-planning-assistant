import asyncio
from typing import List, Dict, Any
from datetime import datetime
import logging

from api.db.session import AsyncSessionLocal
from api.db.batch_crud import (
    get_batch_job, update_batch_job_progress, complete_batch_job
)
from api.db.models import BatchJobStatus
from api.services.content_generation_service import content_generation_service
from api.services.curriculum_service import curriculum_service
from api.services.webhook_service import webhook_service
from api.models import (
    GenerateQuizRequest, GenerateActivityRequest, 
    GenerateExamRequest, GenerateReinforcementRequest,
    StructuredPlanRequest
)

logger = logging.getLogger(__name__)

class BatchProcessingService:
    """Service for processing batch content generation jobs"""
    
    def __init__(self):
        self.max_concurrent = 3  # Max concurrent item processing
    
    async def process_batch_job(self, job_id: str) -> None:
        """
        Process a batch job in the background.
        This is called after job creation and runs asynchronously.
        """
        async with AsyncSessionLocal() as db:
            job = await get_batch_job(db, job_id)
            if not job:
                logger.error(f"Batch job {job_id} not found")
                return
            
            # Update status to processing
            job.status = BatchJobStatus.PROCESSING
            job.started_at = datetime.utcnow()
            await db.commit()
            
            # Need to refresh to get metadata
            await db.refresh(job)
            items = job.metadata.get('items', [])
            job_type = job.job_type
            webhook_url = job.webhook_url
            webhook_secret = job.webhook_secret
            total_items = job.total_items
        
        # Process items with limited concurrency
        semaphore = asyncio.Semaphore(self.max_concurrent)
        tasks = []
        
        for item in items:
            task = asyncio.create_task(
                self._process_item_with_semaphore(
                    semaphore, job_id, job_type, item, webhook_url, webhook_secret
                )
            )
            tasks.append(task)
        
        # Wait for all items to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Determine final status
        async with AsyncSessionLocal() as db:
            job = await get_batch_job(db, job_id)
            if job.failed_items == 0:
                final_status = BatchJobStatus.COMPLETED
            elif job.completed_items > 0:
                final_status = BatchJobStatus.PARTIAL
            else:
                final_status = BatchJobStatus.FAILED
            
            await complete_batch_job(db, job_id, final_status)
            
            # Send completion webhook
            if job.webhook_url:
                await webhook_service.notify_batch_completed(
                    webhook_url=job.webhook_url,
                    webhook_secret=job.webhook_secret,
                    job_id=job_id,
                    status=final_status.value,
                    results=job.results,
                    total_items=job.total_items,
                    completed_items=job.completed_items,
                    failed_items=job.failed_items
                )
    
    async def _process_item_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        job_id: str,
        job_type: str,
        item: dict,
        webhook_url: str = None,
        webhook_secret: str = None
    ) -> None:
        """Process a single item with semaphore for rate limiting"""
        async with semaphore:
            await self._process_single_item(
                job_id, job_type, item, webhook_url, webhook_secret
            )
    
    async def _process_single_item(
        self,
        job_id: str,
        job_type: str,
        item: dict,
        webhook_url: str = None,
        webhook_secret: str = None
    ) -> None:
        """Process a single item in the batch"""
        item_id = item.get('item_id', 'unknown')
        
        try:
            async with AsyncSessionLocal() as db:
                # Get curriculum data
                curriculum_data = await curriculum_service.get_oas_by_ids(
                    db,
                    item.get('oa_ids', []),
                    item.get('grade_level', ''),
                    item.get('subject', '')
                )
                
                # Generate content based on job type
                result = await self._generate_content(job_type, item, curriculum_data)
                
                # Update progress
                job = await update_batch_job_progress(
                    db, job_id,
                    completed_items=None,  # Will be calculated
                    item_result={
                        'item_id': item_id,
                        'status': 'success',
                        'result': result.model_dump() if hasattr(result, 'model_dump') else result
                    }
                )
                
                # Increment completed
                job.completed_items += 1
                await db.commit()
                
                # Send progress webhook every few items
                if webhook_url and job.completed_items % 5 == 0:
                    await webhook_service.notify_batch_progress(
                        webhook_url, webhook_secret,
                        job_id, job.progress_percent,
                        job.completed_items, job.failed_items, job.total_items
                    )
                    
        except Exception as e:
            logger.error(f"Error processing item {item_id}: {e}")
            async with AsyncSessionLocal() as db:
                job = await update_batch_job_progress(
                    db, job_id,
                    item_result={
                        'item_id': item_id,
                        'status': 'error',
                        'error': str(e)
                    }
                )
                job.failed_items += 1
                await db.commit()
    
    async def _generate_content(
        self, 
        job_type: str, 
        item: dict, 
        curriculum_data: dict
    ) -> Any:
        """Generate content based on job type"""
        if job_type == 'quiz':
            request = GenerateQuizRequest(**item)
            return await content_generation_service.generate_quiz(request, curriculum_data)
        elif job_type == 'activity':
            request = GenerateActivityRequest(**item)
            return await content_generation_service.generate_activity(request, curriculum_data)
        elif job_type == 'exam':
            request = GenerateExamRequest(**item)
            return await content_generation_service.generate_exam(request, curriculum_data)
        elif job_type == 'reinforcement':
            request = GenerateReinforcementRequest(**item)
            return await content_generation_service.generate_reinforcement(request, curriculum_data)
        elif job_type == 'lesson':
            request = StructuredPlanRequest(**item)
            return await content_generation_service.generate_structured_lesson(request, curriculum_data)
        else:
            raise ValueError(f"Unknown job type: {job_type}")

# Singleton instance
batch_processing_service = BatchProcessingService()