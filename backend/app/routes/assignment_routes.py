"""Narrow project collaboration: task-level RBAC, not broad file delegation."""
from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, Field
from app.db.supabase_client import db
from app.middlewares.auth import require_auth
from app.services.notification_service import create_notification

router = APIRouter(prefix="/assignments")
Status = Literal["assigned","in_progress","submitted","completed"]

class AssignmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    workspace_id: UUID
    assignee_id: UUID
    title: str = Field(min_length=3,max_length=180)
    discipline: Literal["architecture","structural","mechanical","electrical","plumbing","site","other"]

class AssignmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_status: Status
    status: Status

async def rpc(name,params):
    try:
        res=await run_in_threadpool(lambda:db.rpc(name,params).execute())
        if res is None or not isinstance(res.data,list):
            raise RuntimeError("Invalid task data")
        return res.data
    except Exception as exc:
        raise HTTPException(status_code=503,detail="Project assignments unavailable") from exc

@router.get("/")
async def list_tasks(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0,le=10000),user=Depends(require_auth)):
    return await rpc("krafzen_list_project_tasks",{"p_actor":user["user_id"],"p_limit":limit,"p_offset":offset})

@router.post("/",status_code=201)
async def create_task(body:AssignmentCreate,user=Depends(require_auth)):
    if len(body.title.strip())<3:
        raise HTTPException(status_code=422,detail="Enter a task title")
    rows=await rpc("krafzen_assign_project_task",{"p_actor":user["user_id"],"p_project":str(body.project_id),"p_workspace":str(body.workspace_id),"p_assignee":str(body.assignee_id),"p_title":body.title,"p_discipline":body.discipline})
    if not rows:
        raise HTTPException(status_code=403,detail="Requires an active owned personal project, owned workspace and current contributing member")
    row=rows[0]
    await create_notification(str(body.assignee_id),"project_assignment","A project task was assigned to you.",metadata={"assignment_id":row["id"]})
    return row

@router.patch("/{task_id}")
async def change_task(task_id:UUID,body:AssignmentUpdate,user=Depends(require_auth)):
    rows=await rpc("krafzen_update_project_task",{"p_actor":user["user_id"],"p_task":str(task_id),"p_expected":body.expected_status,"p_status":body.status})
    if not rows:
        raise HTTPException(status_code=409,detail="Task not accessible or transition not permitted")
    row=rows[0]
    target=row["assigned_by"] if user["user_id"]==row["assignee_id"] else row["assignee_id"]
    await create_notification(target,"project_assignment","A project task status changed.",metadata={"assignment_id":row["id"],"status":row["status"]})
    return row

@router.delete("/{task_id}")
async def revoke_task(task_id:UUID,user=Depends(require_auth)):
    rows=await rpc("krafzen_revoke_project_task",{"p_actor":user["user_id"],"p_task":str(task_id)})
    if not rows:
        raise HTTPException(status_code=404,detail="Owned task not found")
    return {"revoked":True}
