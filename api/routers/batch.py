from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from api.db.session import get_async_db
from api.core.security import get_api_key_client, require_permission
from api.db.models import ServiceClient
from api.db.batch_crud import (
    create_batch_job, get_batch_job, get_batch_jobs_by_client, cancel_batch_job
)
from api.services.batch_service import batch_processing_service
from api.models import (
    BatchGenerateRequest, BatchGenerateResponse, 
    BatchStatusResponse, BatchJobInfo
)

router = APIRouter(prefix="/api/v1/batch", tags=["Batch Operations"])

@router.post("/generate", response_model=BatchGenerateResponse)
async def create_batch_job_endpoint(
    request: BatchGenerateRequest,
    background_tasks: BackgroundTasks,
    client: ServiceClient = Depends(require_permission("batch:generate")),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Submit a batch content generation job.
    
    Creates a batch job that will process multiple content generation
    requests asynchronously. Progress and completion are reported via
    webhook if configured.
    
    Authentication: API Key with batch:generate permission
    """
    if len(request.items) == 0:
        return BatchGenerateResponse(
            success=False,
            job=None,
            message="No items provided",
            error="items list cannot be empty"
        )
    
    if len(request.items) > 100:
        return BatchGenerateResponse(
            success=False,
            job=None,
            message="Too many items",
            error="Maximum 100 items per batch"
        )
    
    # Validate all items have item_id
    for idx, item in enumerate(request.items):
        if 'item_id' not in item:
            item['item_id'] = f"item_{idx}"
    
    try:
        # Create batch job
        job = await create_batch_job(
            db=db,
            client_id=client.id,
            job_type=request.content_type.value,
            total_items=len(request.items),
            webhook_url=request.webhook_url,
            webhook_secret=request.webhook_secret,
            metadata={'items': request.items, 'priority': request.priority}
        )
        
        # Start background processing
        background_tasks.add_task(
            batch_processing_service.process_batch_job,
            job.job_id
        )
        
        return BatchGenerateResponse(
            success=True,
            job=BatchJobInfo(
                job_id=job.job_id,
                status=job.status.value,
                content_type=job.job_type,
                total_items=job.total_items,
                completed_items=job.completed_items,
                failed_items=job.failed_items,
                progress_percent=job.progress_percent,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at
            ),
            message=f"Batch job created with {len(request.items)} items"
        )
        
    except Exception as e:
        return BatchGenerateResponse(
            success=False,
            job=None,
            message="Failed to create batch job",
            error=str(e)
        )

@router.get("/{job_id}", response_model=BatchStatusResponse)
async def get_batch_status(
    job_id: str,
    include_results: bool = False,
    client: ServiceClient = Depends(get_api_key_client),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get status of a batch job.
    
    Returns current progress and optionally results if completed.
    
    Authentication: API Key
    """
    job = await get_batch_job(db, job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")
    
    if job.client_id != client.id:
        raise HTTPException(status_code=403, detail="Access denied to this job")
    
    return BatchStatusResponse(
        job=BatchJobInfo(
            job_id=job.job_id,
            status=job.status.value,
            content_type=job.job_type,
            total_items=job.total_items,
            completed_items=job.completed_items,
            failed_items=job.failed_items,
            progress_percent=job.progress_percent,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at
        ),
        results=job.results if include_results else None
    )

@router.post("/{job_id}/cancel")
async def cancel_batch_job_endpoint(
    job_id: str,
    client: ServiceClient = Depends(get_api_key_client),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Cancel a pending or processing batch job.
    
    Authentication: API Key
    """
    job = await get_batch_job(db, job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")
    
    if job.client_id != client.id:
        raise HTTPException(status_code=403, detail="Access denied to this job")
    
    updated = await cancel_batch_job(db, job_id)
    
    if not updated:
        raise HTTPException(
            status_code=400, 
            detail="Cannot cancel job in current status"
        )
    
    return {"message": "Job cancelled", "job_id": job_id}

@router.get("/", response_model=list[BatchJobInfo])
async def list_batch_jobs(
    status: str = None,
    limit: int = 50,
    client: ServiceClient = Depends(get_api_key_client),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List batch jobs for the current client.
    
    Authentication: API Key
    """
    from api.db.models import BatchJobStatus
    
    status_enum = None
    if status:
        try:
            status_enum = BatchJobStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    jobs = await get_batch_jobs_by_client(db, client.id, status_enum, limit)
    
    return [
        BatchJobInfo(
            job_id=job.job_id,
            status=job.status.value,
            content_type=job.job_type,
            total_items=job.total_items,
            completed_items=job.completed_items,
            failed_items=job.failed_items,
            progress_percent=job.progress_percent,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at
        )
        for job in jobs
    ]