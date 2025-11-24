"""Main entry point for TRPG-LLM server"""

import uvicorn
from pathlib import Path
from typing import Optional

from .api.server import create_app
from .utils.logger import get_logger


logger = get_logger(__name__)


def main(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
):
    """
    Start the TRPG-LLM server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload on code changes
    """
    logger.info("Starting TRPG-LLM server", host=host, port=port)
    
    app = create_app()
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="TRPG-LLM Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    main(host=args.host, port=args.port, reload=args.reload)
