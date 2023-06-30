from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # import StaticFiles
from jump_cutter import jump_cutter
import os

app = FastAPI()

# Mount the static files directory
app.mount("/temp", StaticFiles(directory="temp"), name="temp")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        if not os.path.exists('temp'):
            os.makedirs('temp')

        with open(f"temp/{file.filename}", "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"filename": file.filename}

@app.get("/process_video/{filename}")
async def process_video(filename: str, silent_threshold: float):
    try:
        input_file = f"temp/{filename}"
        output_file = f"temp/output_file"

        jump_cutter(
            input_file=input_file,
            output_file=output_file,
            silent_threshold=silent_threshold
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"output_file": output_file}
