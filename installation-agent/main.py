import uvicorn
import sys
import os

# Ensure app path is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config.settings import settings

if __name__ == "__main__":
    # Start uvicorn server on localhost port 8000
    print("Launching Installation Discovery Agent FastAPI Web Server...")
    print("Documentation will be available at: http://127.0.0.1:8000/docs")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
