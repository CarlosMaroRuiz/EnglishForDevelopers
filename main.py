"""Development entrypoint for the English Tutor application.

Run with::

    python main.py

which starts uvicorn with auto-reload on http://127.0.0.1:5000.
"""
import uvicorn

from app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
