from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.db.models import BatchJob, BatchJobStatus
import uuid
from datetime import datetime

async def create_batch_job(
    db: AsyncSession,
    client_id: int,
    job_type: str,
    total_items: int,
    webhook_url: str = None,
    webhook_secret: str = None,
    metadata: dict = None
) -> BatchJob:
    """Create a new batch job"""
    job = BatchJob(
        job_id=f"batch_{uuid.uuid4().hex[:12]}",
        client_id=client_id,
        job_type=job_type,
        total_items=total_items,
        webhook_url=webhook_url,
        webhook_secret=webhook_secret if webhook_url else None,
        job_metadata=metadata or {}
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job

async def get_batch_job(db: AsyncSession, job_id: str) -> BatchJob | None:
    """Get batch job by job_id"""
    result = await db.execute(
        select(BatchJob).where(BatchJob.job_id == job_id)
    )
    return result.scalar_one_or_none()

async def get_batch_jobs_by_client(
    db: AsyncSession, 
    client_id: int,
    status: BatchJobStatus = None,
    limit: int = 50
) -> list[BatchJob]:
    """Get batch jobs for a client"""
    query = select(BatchJob).where(BatchJob.client_id == client_id)
    if status:
        query = query.where(BatchJob.status == status)
    query = query.order_by(BatchJob.created_at.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())

async def update_batch_job_progress(
    db: AsyncSession,
    job_id: str,
    completed_items: int = None,
    failed_items: int = None,
    item_result: dict = None
) -> BatchJob | None:
    """Update batch job progress"""
    job = await get_batch_job(db, job_id)
    if not job:
        return None
    
    if completed_items is not None:
        job.completed_items = completed_items
    if failed_items is not None:
        job.failed_items = failed_items
    if item_result:
        # Ensure results is a list
        current_results = job.results if isinstance(job.results, list) else []
        job.results = current_results + [item_result]
    
    if job.total_items > 0:
        job.progress_percent = ((job.completed_items + job.failed_items) / job.total_items) * 100
    
    await db.commit()
    await db.refresh(job)
    return job

async def complete_batch_job(
    db: AsyncSession,
    job_id: str,
    status: BatchJobStatus
) -> BatchJob | None:
    """Mark batch job as completed"""
    job = await get_batch_job(db, job_id)
    if not job:
        return None
    
    job.status = status
    job.completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(job)
    return job

async def cancel_batch_job(db: AsyncSession, job_id: str) -> BatchJob | None:
    """Cancel a batch job"""
    job = await get_batch_job(db, job_id)
    if not job:
        return None
    
    if job.status not in [BatchJobStatus.PENDING, BatchJobStatus.PROCESSING]:
        return None  # Can't cancel completed jobs
    
    job.status = BatchJobStatus.CANCELLED
    job.completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(job)
    return job