from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from jump_cutter import jump_cutter
import os

app = FastAPI()

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    # create a temporary file and write the uploaded file's content to it
    with open(f"temp/{file.filename}", "wb") as buffer:
        buffer.write(await file.read())

    return {"filename": file.filename}

@app.post("/process_video/")
async def process_video(filename: str, silent_threshold: float):
    # input and output file paths
    input_file = f"temp/{filename}"
    output_file = f"temp/output_{filename}"
    
    # Call the function with the correct extension for the output
    jump_cutter(
        input_file=input_file,
        output_file=output_file,
        silent_threshold=silent_threshold
    )
    
    # After processing the video, return it as a file download response
    response = FileResponse(output_file, media_type='application/octet-stream')

    # Clean up the input and output files from the disk after sending the response
    os.remove(input_file)
    os.remove(output_file)
    
    return response
