#!/usr/bin/env python3
"""
Optimized FastAPI server startup script with performance settings
"""
import uvicorn
import os
import multiprocessing

if __name__ == "__main__":
    # Calculate optimal number of workers based on CPU cores
    workers = multiprocessing.cpu_count()
    
    # Performance-optimized uvicorn configuration for Windows
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        workers=1,  # Single worker for Windows (uvloop not available)
        http="httptools",  # Use httptools for better HTTP parsing
        access_log=True,
        log_level="info",
        reload=True,  # Enable auto-reload for development
        reload_dirs=["."],  # Watch current directory for changes
        reload_excludes=["*.pyc", "__pycache__", "*.log"],  # Exclude files from reload
        # Performance tuning
        limit_concurrency=1000,  # Limit concurrent connections
        limit_max_requests=1000,  # Restart workers after this many requests
        timeout_keep_alive=30,  # Keep-alive timeout
        timeout_graceful_shutdown=30,  # Graceful shutdown timeout
    )
