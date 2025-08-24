# backend/main.py

import os
import json
import shutil
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import traceback

# CORRECTED IMPORT: Import directly from sibling files in the 'backend' directory
from document_parser import extract_text_from_document
from processor import get_structured_data

# Load environment variables (e.g., API keys) when the server starts
load_dotenv()

# Initialize FastAPI application
app = FastAPI()

# CORRECTED PATH: Point to the sibling 'frontend' directory
# The path "../frontend" means "go up one level from where this script is, then go into frontend"
app.mount("/static", StaticFiles(directory="../frontend"), name="static")


# --- API Routes to Serve HTML Pages ---
@app.get("/")
async def serve_index():
    # This path is correct because it's relative to the 'backend' folder
    return FileResponse('../frontend/index.html')


@app.get("/upload")
async def serve_upload_page():
    return FileResponse('../frontend/upload.html')


@app.get("/data")
async def serve_data_page():
    return FileResponse('../frontend/data.html')


# --- API Endpoint to Process Uploaded Files ---
@app.post("/process")
async def process_uploaded_files(files: List[UploadFile] = File(...)):
    """
    Receives files, saves them, runs the processing pipeline, and returns the
    FULL, detailed JSON response.
    """
    # This will create an 'uploads' folder inside your 'backend' directory
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
            raise HTTPException(status_code=500, detail=f"An error occurred while processing {file.filename}.")
        finally:
            file.file.close()

    # This will create 'output.json' inside your 'backend' directory
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(all_detailed_data, f, indent=2, ensure_ascii=False)

    return all_detailed_data