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

    json_data = json.load(open(file_location, "r"))
    # print(f"json_data: {json_data}")
    # load_data_to_firebase(file_location, DATABASE_URL=FIREBASE_URL)
    requests.put(FIREBASE_URL + "/uploads.json", json=json_data )

    return JSONResponse(content={"message": "File uploaded successfully!"})

    # except Exception as e:
    #     return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/chat")
async def chat(message: ChatMessage):
    # Simple echo response for demonstration
    # Replace this with your logic for generating responses
    user_message = message.message
    split_message = user_message.split("=")
    
    command = split_message[0]

    gets = ["get", "Get", "GET"]
    puts = ["put", "Put", "PUT"]
    posts = ["post", "Post", "POST"]
    deletes = ["delete","Delete", "DELETE"]
    patches = ["patch", "Patch", "PATCH"]

    if command in gets:
        db_url = FIREBASE_URL + split_message[1]
        response = requests.get(db_url)
        print(f"GETTING from {db_url}")
        if response.status_code == 200:
            bot_response = response.json()
            return JSONResponse(content={"reply": f"Your query was executed successfully: \n {bot_response}" })
            # bot_response = f"Your query was executed successfully: {bot_response}"

        else:
            bot_response = f" {response.status_code} - {response.text}"
            return JSONResponse(content={"reply": f"Your query ran into an error :( \n {bot_response}"})
        
    elif command in puts:
        url = split_message[1]
        data = split_message[2]

        db_url = FIREBASE_URL + url
        # data = json.loads(data)
        # data = f"""{data[1:-1]}"""
        data = data.replace("'", '"')
        print(data)
        data = json.loads(data)
        response = requests.put(db_url, json=data)
        if response.status_code == 200:
            bot_response = response.json()
            return JSONResponse(content={"reply": f"Your query was executed successfully: \n {bot_response}" })
            # bot_response = f"Your query was executed successfully: {bot_response}"

        else:
            bot_response = f" {response.status_code} - {response.text}"
            return JSONResponse(content={"reply": f"Your query ran into an error :( \n {bot_response}"})
        
    elif command in posts:
        url = split_message[1]
        data = split_message[2]

        db_url = FIREBASE_URL + url
        data = data.replace("'", '"')
        print(data)
        response = requests.post(db_url, json=data)
        if response.status_code == 200:
            bot_response = response.json()
            return JSONResponse(content={"reply": f"Your query was executed successfully: \n {bot_response}" })
            # bot_response = f"Your query was executed successfully: {bot_response}"

        else:
            bot_response = f" {response.status_code} - {response.text}"
            return JSONResponse(content={"reply": f"Your query ran into an error :( \n {bot_response}"})

    elif command in patches:
        print(f"PATCHING")
        url = split_message[1]
        data = split_message[2]

        db_url = FIREBASE_URL + url
        data = data.replace("'", '"')
        print(data)
        data = json.loads(data)
        response = requests.patch(db_url, json=data)
        if response.status_code == 200:
            bot_response = response.json()
            return JSONResponse(content={"reply": f"Your query was executed successfully: \n {bot_response}" })
            # bot_response = f"Your query was executed successfully: {bot_response}"

        else:
            bot_response = f" {response.status_code} - {response.text}"
            return JSONResponse(content={"reply": f"Your query ran into an error :( \n {bot_response}"})
        
    elif command in deletes:
        url = split_message[1]

        db_url = FIREBASE_URL + url

        response = requests.delete(db_url)
        if response.status_code == 200:
            bot_response = response.json()
            return JSONResponse(content={"reply": f"Data was deleted: \n {bot_response}" })
            # bot_response = f"Your query was executed successfully: {bot_response}"

        else:
            bot_response = f" {response.status_code} - {response.text}"
            return JSONResponse(content={"reply": f"Your query ran into an error :( \n {bot_response}"})
    
    else:
        return JSONResponse(content={"reply": f"Sorry please try amongst: GET, PUT, POST."})

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

