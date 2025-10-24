#!/usr/bin/env python3
"""
Facebook Account Checker - REST API Server (FastAPI)
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
import asyncio
import threading
import uuid
import json
from datetime import datetime
from queue import Queue
import logging

import os, base64, tkinter as tk, tkinter.messagebox as mb
from cryptography.fernet import Fernet
import sys
import uuid as _uuid

from main import (
    process_phone_numbers,
    ensure_directories
)
import proxy_injector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

jobs: Dict[str, 'VerificationJob'] = {}
jobs_lock = threading.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting API Server...")
    ensure_directories()

    proxy_thread = threading.Thread(
        target=proxy_injector.start_proxy_server,
        args=(9080, 9081),
        daemon=True
    )
    proxy_thread.start()
    await asyncio.sleep(1)
    
    logger.info("API Server ready at http://localhost:8000")

    yield

    logger.info("Shutting down...")
    with jobs_lock:
        for job in jobs.values():
            if job.status == 'running':
                job.is_running = False
                job.status = 'stopped'


app = FastAPI(
    title="Facebook Account Checker API",
    description="REST API for phone number verification on Facebook",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProxyConfig(BaseModel):
    enabled: bool = False
    server: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None

    @field_validator('port')
    @classmethod
    def validate_port(cls, v: Optional[int], info) -> Optional[int]:
        if info.data.get('enabled') and v is not None:
            if v < 1 or v > 65535:
                raise ValueError('Port must be between 1 and 65535')
        return v

    @field_validator('server')
    @classmethod
    def validate_server(cls, v: Optional[str], info) -> Optional[str]:
        if info.data.get('enabled') and not v:
            raise ValueError('Server address is required when proxy is enabled')
        return v


class LicenseValidateRequest(BaseModel):
    license_key: str = Field(..., min_length=1, description="License key to validate")


class CreateJobRequest(BaseModel):
    phone_numbers: List[str] = Field(..., min_length=1, description="List of phone numbers to verify")
    workers: int = Field(default=5, ge=1, le=100, description="Number of concurrent workers")
    headless: bool = Field(default=False, description="Run browsers in headless mode")
    proxy: Optional[ProxyConfig] = Field(default=None, description="Proxy configuration for this job")
    license_key: Optional[str] = Field(default=None, description="License key for validation")

    @field_validator('phone_numbers')
    @classmethod
    def validate_phone_numbers(cls, v: List[str]) -> List[str]:
        valid_numbers = [num.strip() for num in v if num.strip()]
        if not valid_numbers:
            raise ValueError('At least one valid phone number is required')
        return valid_numbers


class JobStatusResponse(BaseModel):
    success: bool = True
    job_id: str
    status: str
    total_numbers: int
    processed_count: int
    successful_count: int
    failed_count: int


class JobResultItem(BaseModel):
    phone: str
    status: str
    message: str


class JobDetailResponse(BaseModel):
    success: bool = True
    job: Dict[str, Any]


class VerificationJob:
    def __init__(self, job_id: str, phone_numbers: List[str], workers: int = 5, headless: bool = False):
        self.job_id = job_id
        self.phone_numbers = phone_numbers
        self.workers = workers
        self.headless = headless
        self.status = "pending"
        self.total_numbers = len(phone_numbers)
        self.processed_count = 0
        self.successful_numbers: List[str] = []
        self.failed_numbers: List[str] = []
        self.results: List[Dict[str, str]] = []
        self.logs: List[str] = []
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.is_running = False
        self.results_queue = Queue()

    def add_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)

    def add_result(self, result: Dict[str, str]):
        self.results.append(result)
        self.processed_count += 1

        if result['status'] == 'success':
            self.successful_numbers.append(result['phone'])
        else:
            self.failed_numbers.append(result['phone'])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'job_id': self.job_id,
            'status': self.status,
            'total_numbers': self.total_numbers,
            'processed_count': self.processed_count,
            'successful_count': len(self.successful_numbers),
            'failed_count': len(self.failed_numbers),
            'successful_numbers': self.successful_numbers,
            'failed_numbers': self.failed_numbers,
            'results': self.results,
            'logs': self.logs,
            'workers': self.workers,
            'headless': self.headless,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }


@app.get("/api/health")
async def health_check():
    return {
        'status': 'healthy',
        'service': 'Facebook Account Checker API',
        'timestamp': datetime.now().isoformat()
    }


@app.get("/api/status")
async def get_status():
    return {
        'active_jobs': len([j for j in jobs.values() if j.status == 'running'])
    }

f = Fernet("1WvpfsEvFd4ffCFsyQy-y8zoNA_nTHkrd4sd8qvQWMw=")

def get_system_uuid():
    # Try Windows MachineGuid
    try:
        if sys.platform.startswith("win"):
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Microsoft\Cryptography")
            machineguid, _ = winreg.QueryValueEx(key, "MachineGuid")
            return machineguid.strip()
    except Exception:
        pass
    # Try Linux machine-id
    try:
        for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
            if os.path.exists(path):
                with open(path, "r") as f:
                    return f.read().strip()
    except Exception:
        pass
    # Fallback to MAC-based value (not perfect but usable)
    mac = _uuid.getnode()
    return f"{mac:x}"

def verify_token(token):
    try:
        data = json.loads(f.decrypt(token.encode()).decode())
    except Exception as e:
        return False, "invalid token #3984"
    # expiry check
    try:
        if datetime.datetime.now(datetime.timezone.utc) > datetime.datetime.strptime(data["expiry"], "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc):
            return False, "invalid token #2934"
    except Exception:
        return False, "invalid token #3984"
    # uuid check
    sys_uuid = get_system_uuid()
    if data.get("uuid") != sys_uuid:
        return False, f"invalid token #9238"

    secure_data = {k: v for k, v in data.items() if k != 'uuid'}
    return True, secure_data


def validate_license_key(license_key: str) -> Dict[str, Any]:
    ok, info = verify_token(license_key)
    if ok:
        return {
            'success': ok,
            'data': info
        }
    else:
        return {
            'success': False,
            'message': 'Invalid license key or license has expired'
        }


@app.post("/api/license/validate")
async def validate_license(request: LicenseValidateRequest):
    """
    Validate license key.
    Currently uses dummy validation - will be implemented later.
    """
    try:
        result = validate_license_key(request.license_key)
        return result
    except Exception as e:
        logger.error(f"License validation error: {str(e)}")
        return {
            'success': False,
            'message': 'Failed to validate license'
        }


@app.get("/api/jobs")
async def list_jobs():
    with jobs_lock:
        job_list = []
        for job in jobs.values():
            job_list.append({
                'job_id': job.job_id,
                'status': job.status,
                'total_numbers': job.total_numbers,
                'processed_count': job.processed_count,
                'successful_count': len(job.successful_numbers),
                'failed_count': len(job.failed_numbers),
                'created_at': job.created_at.isoformat(),
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None
            })

        return {
            'success': True,
            'jobs': job_list,
            'total': len(job_list)
        }


@app.post("/api/jobs", status_code=201)
async def create_job(request: CreateJobRequest, background_tasks: BackgroundTasks):
    # Validate license if provided
    if request.license_key:
        validation_result = validate_license_key(request.license_key)
        if not validation_result['success']:
            raise HTTPException(
                status_code=403, 
                detail=validation_result.get('message', 'Invalid license key')
            )
        logger.info(f"License validated for: {validation_result['data']['name']}")
    else:
        raise HTTPException(
                status_code=403, 
                detail="License key is required"
            )
    
    # Configure proxy if provided
    if request.proxy:
        proxy_injector.configure_proxy(
            server=request.proxy.server if request.proxy.server else None,
            port=request.proxy.port if request.proxy.port else None,
            username=request.proxy.username if request.proxy.username else None,
            password=request.proxy.password if request.proxy.password else None,
            enabled=request.proxy.enabled
        )
        logger.info(f"Proxy configured for job: enabled={request.proxy.enabled}")
    
    job_id = str(uuid.uuid4())
    job = VerificationJob(job_id, request.phone_numbers, request.workers, request.headless)

    with jobs_lock:
        jobs[job_id] = job

    job.add_log(f"Job created with {len(request.phone_numbers)} phone numbers, {request.workers} workers")
    if request.proxy and request.proxy.enabled:
        job.add_log(f"Proxy enabled: {request.proxy.server}:{request.proxy.port}")
    else:
        job.add_log("Direct connection mode (no proxy)")
    
    background_tasks.add_task(run_verification_job, job_id)

    return {
        'success': True,
        'job_id': job_id,
        'message': f'Verification job created with {len(request.phone_numbers)} phone numbers',
        'job': {
            'job_id': job_id,
            'status': 'pending',
            'total_numbers': len(request.phone_numbers),
            'workers': request.workers,
            'headless': request.headless
        }
    }


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail='Job not found')

        return {
            'success': True,
            'job': job.to_dict()
        }


@app.get("/api/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail='Job not found')

        return JobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            total_numbers=job.total_numbers,
            processed_count=job.processed_count,
            successful_count=len(job.successful_numbers),
            failed_count=len(job.failed_numbers)
        )


@app.get("/api/jobs/{job_id}/results")
async def get_job_results(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail='Job not found')

        return {
            'success': True,
            'job_id': job.job_id,
            'results': job.results,
            'successful_numbers': job.successful_numbers,
            'failed_numbers': job.failed_numbers,
            'successful_count': len(job.successful_numbers),
            'failed_count': len(job.failed_numbers)
        }


@app.get("/api/jobs/{job_id}/logs")
async def get_job_logs(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail='Job not found')

        return {
            'success': True,
            'job_id': job.job_id,
            'logs': job.logs
        }


@app.post("/api/jobs/{job_id}/stop")
async def stop_job(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail='Job not found')

        if job.status != 'running':
            raise HTTPException(
                status_code=400,
                detail=f'Job is not running (current status: {job.status})'
            )

        job.is_running = False
        job.status = 'stopped'
        job.add_log("Job stopped by user request")
        job.completed_at = datetime.now()

        return {
            'success': True,
            'message': 'Job stopped successfully',
            'job_id': job_id
        }


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail='Job not found')

        if job.status == 'running':
            job.is_running = False

        del jobs[job_id]

        return {
            'success': True,
            'message': 'Job deleted successfully',
            'job_id': job_id
        }


@app.get("/api/jobs/{job_id}/stream")
async def stream_job_progress(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail='Job not found')

    async def event_generator():
        last_processed = 0
        try:
            while True:
                with jobs_lock:
                    job = jobs.get(job_id)
                    if not job:
                        yield f"data: {{'error': 'Job not found'}}\n\n"
                        break

                    if job.processed_count > last_processed:
                        last_processed = job.processed_count
                        data = {
                            'status': job.status,
                            'processed_count': job.processed_count,
                            'total_numbers': job.total_numbers,
                            'successful_count': len(job.successful_numbers),
                            'failed_count': len(job.failed_numbers)
                        }
                        yield f"data: {json.dumps(data)}\n\n"

                    if job.status in ['completed', 'stopped', 'error']:
                        yield f"data: {json.dumps({'status': 'done'})}\n\n"
                        break

                await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Error in event generator: {e}")
            yield f"data: {{'error': '{str(e)}'}}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


def run_verification_job(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return

    try:
        job.status = 'running'
        job.is_running = True
        job.started_at = datetime.now()
        job.add_log(f"Starting verification for {job.total_numbers} numbers with {job.workers} workers")

        def result_callback(result: Dict[str, str]):
            if job.is_running:
                with jobs_lock:
                    job.add_result(result)
                    phone = result['phone']
                    status = result['status']
                    message = result['message']

                    if status == 'success':
                        job.add_log(f"✅ SUCCESS: {phone} - {message}")
                    else:
                        job.add_log(f"❌ FAILED: {phone} - {message}")

        results = process_phone_numbers(
            job.phone_numbers,
            num_workers=job.workers,
            headless=job.headless,
            callback=result_callback
        )

        with jobs_lock:
            if job.is_running:
                job.status = 'completed'
                job.completed_at = datetime.now()
                job.add_log(f"✅ All checks completed! Success: {len(job.successful_numbers)}, Failed: {len(job.failed_numbers)}")

    except Exception as e:
        logger.error(f"Error in job {job_id}: {e}", exc_info=True)
        with jobs_lock:
            job.status = 'error'
            job.error_message = str(e)
            job.completed_at = datetime.now()
            job.add_log(f"❌ Error: {str(e)}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
