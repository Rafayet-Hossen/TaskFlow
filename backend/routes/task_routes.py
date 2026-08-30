from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.database import get_db
from backend.models import Task, User
from backend.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskStatusUpdate,
    TaskResponse,
    MessageResponse
)
from backend.auth import get_current_verified_user

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

def enrich_task_data(task: Task) -> dict:
    """Calculates remaining seconds and urgency category based on current UTC time."""
    now = datetime.now(timezone.utc)
    
    # Ensure datetimes have UTC timezone info
    start_dt = task.start_date
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)

    end_dt = task.end_date
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)

    remaining_seconds = (end_dt - now).total_seconds()

    if task.status == "completed":
        urgency = "completed"
    elif remaining_seconds <= 0:
        urgency = "overdue"
    elif remaining_seconds <= 3600:  # <= 1 hour
        urgency = "urgent_red"
    elif remaining_seconds <= 21600:  # <= 6 hours
        urgency = "warning_yellow"
    elif remaining_seconds <= 86400:  # <= 24 hours
        urgency = "today_green"
    else:
        urgency = "normal"

    created_dt = task.created_at
    if created_dt and created_dt.tzinfo is None:
        created_dt = created_dt.replace(tzinfo=timezone.utc)

    updated_dt = task.updated_at
    if updated_dt and updated_dt.tzinfo is None:
        updated_dt = updated_dt.replace(tzinfo=timezone.utc)

    return {
        "id": task.id,
        "user_id": task.user_id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "status": task.status,
        "start_date": start_dt,
        "end_date": end_dt,
        "created_at": created_dt,
        "updated_at": updated_dt,
        "remaining_seconds": remaining_seconds,
        "urgency_category": urgency
    }

@router.get("", response_model=List[TaskResponse])
async def get_tasks(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    query = db.query(Task).filter(Task.user_id == current_user.id)

    if status_filter and status_filter.lower() != "all":
        query = query.filter(Task.status == status_filter.lower())

    if priority_filter and priority_filter.lower() != "all":
        query = query.filter(Task.priority == priority_filter.lower())

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Task.title.ilike(search_term),
                Task.description.ilike(search_term)
            )
        )

    # Sort in ascending order by deadline (closest deadline appears first)
    tasks = query.order_by(Task.end_date.asc()).all()

    return [TaskResponse(**enrich_task_data(t)) for t in tasks]

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    if payload.end_date < payload.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task deadline (end date) cannot be before the start date."
        )

    new_task = Task(
        user_id=current_user.id,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        priority=payload.priority,
        status=payload.status,
        start_date=payload.start_date,
        end_date=payload.end_date
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return TaskResponse(**enrich_task_data(new_task))

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id(
    task_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return TaskResponse(**enrich_task_data(task))

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    if payload.title is not None:
        task.title = payload.title.strip()
    if payload.description is not None:
        task.description = payload.description.strip() if payload.description else None
    if payload.priority is not None:
        task.priority = payload.priority
    if payload.status is not None:
        task.status = payload.status
    if payload.start_date is not None:
        task.start_date = payload.start_date
    if payload.end_date is not None:
        task.end_date = payload.end_date

    if task.end_date < task.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task deadline (end date) cannot be before the start date."
        )

    db.commit()
    db.refresh(task)
    return TaskResponse(**enrich_task_data(task))

@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: int,
    payload: TaskStatusUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    task.status = payload.status
    db.commit()
    db.refresh(task)
    return TaskResponse(**enrich_task_data(task))

@router.delete("/{task_id}", response_model=MessageResponse)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    db.delete(task)
    db.commit()
    return MessageResponse(message="Task deleted successfully.", success=True)

