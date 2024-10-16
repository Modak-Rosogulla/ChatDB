from fastapi import FastAPI, Request, UploadFile, File
from app.firebase_helpers import load_data_to_firebase, search_by_id
from fastapi.templating import Jinja2Templates
import requests
import json
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import os
import shutil
from pydantic import BaseModel


load_dotenv()
FIREBASE_URL = os.getenv('DATABASE_URL')

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


class ChatMessage(BaseModel):
    message: str


@app.get("/")
def root(request: Request):

    return templates.TemplateResponse(
        name="home.html", 
        context={"request": request}
    )
    # return {"message": "Welcome to ChatDB"}

@app.get("/mysql")
def mysql():
    return {"message": "MySQL"}

@app.get("/mongodb")
def mongodb():
    return {"message": "MongoDB"}

@app.get("/firebase")
def firebase(request: Request):
    # load_data_to_firebase("app/data.csv")
    AQI_data = requests.get(FIREBASE_URL + "/AQI.json")
    print(f"response_type: {type(AQI_data)}")

    # return AQI_data.json()
    return templates.TemplateResponse(
        name="firebase.html", 
        context={"request": request, "AQI_data": AQI_data.json()}
    )

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Basic file upload to firebase using FastAPI
    Have to process how to upload the file - 
    
    a more general "load_data_to_firebase" function
    This data can also be uploaded to MySQL
    """
    # try:
    upload_folder = "uploads/"
    os.makedirs(upload_folder, exist_ok=True)
    file_location = f"{upload_folder}/{file.filename}"

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    load_data_to_firebase(file_location, DATABASE_URL=FIREBASE_URL)

    return JSONResponse(content={"message": "File uploaded successfully!"})

    # except Exception as e:
    #     return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/chat")
async def chat(message: ChatMessage):
    # Simple echo response for demonstration
    # Replace this with your logic for generating responses
    user_message = message.message
    db_url = FIREBASE_URL + user_message

    response = requests.get(db_url)
    # bot_response = f"Echo: {user_message}"

    # return JSONResponse(content={"reply": bot_response})

    # print(f"Executing requests.get({db_url})")
    
    if response.status_code == 200:
        bot_response = response.json()
        return JSONResponse(content={"reply": f"Your query was executed successfully: \n {bot_response}" })
        # bot_response = f"Your query was executed successfully: {bot_response}"

    else:
        bot_response = f" {response.status_code} - {response.text}"
        return JSONResponse(content={"reply": f"Your query ran into an error :( \n {bot_response}"})

@app.get("/firebase_data")
async def chat(request: Request):
    # user_message = message.message
    db_url = FIREBASE_URL + "/.json"

    print(f"Executing requests.get({db_url})")

    response = requests.get(db_url)
    
    if response.status_code == 200:
        # return JSONResponse(content={"reply": response.json() })
        return response.json()
        # bot_response = f"Your query was executed successfully: {bot_response}"

    else:
        bot_response = f" {response.status_code} - {response.text}"
        return JSONResponse(content={"reply": f"Your query ran into an error :( \n {bot_response}"})

