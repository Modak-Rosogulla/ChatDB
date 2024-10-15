from fastapi import FastAPI, Request
from app.firebase_helpers import load_data_to_firebase, search_by_id
from fastapi.templating import Jinja2Templates
import requests
import json
from fastapi.staticfiles import StaticFiles

app = FastAPI()

DATABASE_URL = "https://dsci551-877cc-default-rtdb.firebaseio.com/"
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


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
def firebase():
    # load_data_to_firebase("app/data.csv")
    AQI_data = requests.get(DATABASE_URL + "/AQI.json")
    print(f"response_type: {type(AQI_data)}")

    return AQI_data.json()

@app.get("/upload_to_firebase")
def upload_to_firebase():
    load_data_to_firebase("app/data.csv")
    return {"message": "Data uploaded successfully"}