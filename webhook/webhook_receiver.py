#!/usr/bin/env python3
"""
GitHub Webhook Receiver for Personal AI Assistant
Validates GitHub signatures and triggers deployment on push to main
"""

import os
import sys
import hmac
import hashlib
import json
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

# Configuration
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "thisisasecret")
DEPLOY_SCRIPT = os.getenv("DEPLOY_SCRIPT", "/mnt/data2-pool/andy-ai/app/scripts/deploy.sh")
LOG_DIR = Path(os.getenv("LOG_DIR", "/mnt/data2-pool/andy-ai/app/logs/deployments"))

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
log_file = LOG_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()


def verify_github_signature(body: bytes, signature: str) -> bool:
    """
    Verify that the webhook signature came from GitHub.
    GitHub sends X-Hub-Signature-256 header with format: sha256=<signature>
    """
    if not signature.startswith("sha256="):
        logger.warning(f"invalid signature format: {signature}")
        return False
    
    expected_signature = signature.split("=")[1]
    computed_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed_signature, expected_signature)


def trigger_deployment() -> Dict[str, Any]:
    """
    Trigger the deployment script and return results
    """
    logger.info("=== DEPLOYMENT TRIGGERED ===")
    logger.info(f"calling deployment script: {DEPLOY_SCRIPT}")
    
    try:
        result = subprocess.run(
            ["/bin/bash", DEPLOY_SCRIPT],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        logger.info("=== DEPLOYMENT STDOUT ===")
        logger.info(result.stdout)
        
        if result.stderr:
            logger.error("=== DEPLOYMENT STDERR ===")
            logger.error(result.stderr)
        
        if result.returncode == 0:
            logger.info("✅ deployment completed successfully")
            return {
                "status": "success",
                "message": "deployment completed successfully",
                "log_file": str(log_file)
            }
        else:
            logger.error(f"❌ deployment failed with return code {result.returncode}")
            return {
                "status": "failed",
                "message": f"deployment failed with return code {result.returncode}",
                "log_file": str(log_file)
            }
    
    except subprocess.TimeoutExpired:
        logger.error("❌ deployment timed out after 10 minutes")
        return {
            "status": "timeout",
            "message": "deployment timed out after 10 minutes",
            "log_file": str(log_file)
        }
    
    except Exception as e:
        logger.error(f"❌ deployment failed with exception: {str(e)}")
        return {
            "status": "error",
            "message": f"deployment failed: {str(e)}",
            "log_file": str(log_file)
        }


@app.post("/webhook")
async def github_webhook(request: Request):
    """
    GitHub webhook endpoint
    Receives push events and triggers deployment if push is to main branch
    """
    logger.info("=== WEBHOOK RECEIVED ===")
    
    # Get the raw body and signature
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    
    logger.info(f"signature present: {bool(signature)}")
    
    # Verify signature
    if not verify_github_signature(body, signature):
        logger.warning("❌ webhook signature verification failed")
        raise HTTPException(status_code=401, detail="signature verification failed")
    
    logger.info("✅ signature verified")
    
    # Parse payload
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        logger.error("❌ invalid json payload")
        raise HTTPException(status_code=400, detail="invalid json")
    
    # Check if this is a push event
    event_type = request.headers.get("X-GitHub-Event", "")
    if event_type != "push":
        logger.info(f"ignoring non-push event: {event_type}")
        return JSONResponse(
            status_code=200,
            content={"message": f"ignoring {event_type} event"}
        )
    
    # Check if push is to main branch
    ref = payload.get("ref", "")
    logger.info(f"push to branch: {ref}")
    
    if ref != "refs/heads/main":
        logger.info(f"ignoring push to non-main branch: {ref}")
        return JSONResponse(
            status_code=200,
            content={"message": f"ignoring push to {ref}"}
        )
    
    # Check if deploy script exists
    if not Path(DEPLOY_SCRIPT).exists():
        logger.error(f"❌ deploy script not found: {DEPLOY_SCRIPT}")
        raise HTTPException(status_code=500, detail="deploy script not found")
    
    logger.info("✅ push to main branch detected, triggering deployment")
    
    # Trigger deployment
    result = trigger_deployment()
    
    if result["status"] == "success":
        return JSONResponse(status_code=200, content=result)
    else:
        return JSONResponse(status_code=500, content=result)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "webhook-receiver"}
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse(
        status_code=200,
        content={
            "service": "GitHub Webhook Receiver",
            "version": "0.1.0",
            "endpoints": {
                "POST /webhook": "GitHub webhook endpoint",
                "GET /health": "Health check",
                "GET /": "This endpoint"
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    logger.info("starting webhook receiver on 0.0.0.0:9002")
    uvicorn.run(app, host="0.0.0.0", port=9002, log_config=None)
