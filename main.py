# main.py

import os
import json
import shutil
import traceback
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
# Add this import for CORS
from fastapi.middleware.cors import CORSMiddleware

from document_parser import extract_text_from_document
from processor import get_structured_data

# Load environment variables (e.g., API keys) when the server starts
load_dotenv()

# Initialize FastAPI application
app = FastAPI()

# --- Add this entire block for CORS ---
# This allows your frontend (from any origin "*") to make requests to your backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)
# ------------------------------------


def clear_output_file(file_path: str = "output.json"):
    """
    Clears the content of the specified file for privacy.
    It writes an empty JSON array to the file.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("[]")  # Write an empty JSON array to clear the file
        print(f"--- ✅ Privacy cleanup: Cleared {file_path} ---")
    except Exception as e:
        print(f"--- ❌ ERROR: Failed to clear {file_path}. Reason: {e} ---")


# --- Root Endpoint ---
@app.get("/")
async def root():
    """Confirms that the server is running."""
    return {"message": "Server is running"}


# --- API Endpoint to Process Uploaded Files ---
@app.post("/process")
async def process_uploaded_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """
    Receives files, processes them, returns the structured JSON data,
    and clears the output file in the background for privacy.
    """
    uploads_dir = "uploads"
    os.makedirs(uploads_dir, exist_ok=True)
    all_detailed_data = []

    for file in files:
        file_path = os.path.join(uploads_dir, file.filename)
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            raw_text = extract_text_from_document(file_path)
            detailed_ai_data = get_structured_data(raw_text)

            detailed_ai_data['fileName'] = file.filename
            all_detailed_data.append(detailed_ai_data)

        except Exception as e:
            print(f"--- ❌ PIPELINE FAILED for {file.filename} ---")
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while processing {file.filename}: {e}"
            )
        finally:
            if not file.file.closed:
                file.file.close()
            if os.path.exists(file_path):
                os.remove(file_path)

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(all_detailed_data, f, indent=2, ensure_ascii=False)

    background_tasks.add_task(clear_output_file)

    return all_detailed_data
