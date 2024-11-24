from fastapi import FastAPI, Request, UploadFile, File ,HTTPException
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
from app.sql_helpers import SqlHelper, generate_create_table_query
import csv
from app.query_preprocessor import process_user_query

load_dotenv()
FIREBASE_URL = os.getenv('DATABASE_URL')

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


sql_obj = SqlHelper()
tables = {}

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
def mysql(request: Request):
    return templates.TemplateResponse(
        name="mysql.html", 
        context={"request": request}
    )

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


@app.get("/mysql_data")
async def chat(request: Request):
    databases = sql_obj.execute_user_query("SHOW DATABASES;")
    # databases = sql_obj.cursor.fetchall()

    # result = sql_obj.execute_user_query("SHOW TABLES;")
    print(f"databases: {databases}")
    flat_databases = [db[0] for db in databases]
    print(f"flat: {flat_databases}")
    return JSONResponse(content={"databases": flat_databases })

@app.post("/select_database")
async def select_database(request: Request):
    data = await request.json()
    database_name = data.get("database_name")
    if not database_name:
        raise HTTPException(status_code=400, detail="Database name is required.")
    
    sql_obj.select_database(database_name)
    return JSONResponse(content={"message": f"Database {database_name} selected."})


@app.post("/chat_sql")
async def chat_sql(message: ChatMessage):
    global tables
    # Simple echo response for demonstration
    # Replace this with your logic for generating responses
    
    user_message = message.message

    # result = sql_obj.execute_user_query(user_message)

    # return JSONResponse(content={"reply": result })
    try:

        generated_query = process_user_query(user_message,tables)
        print(f"Generated SQL Query: {generated_query}")

        if "Error" in generated_query:
            return JSONResponse(content={"error": generated_query}, status_code=400)

        result = sql_obj.execute_user_query(generated_query)
        
        if result is None:
            return JSONResponse(content={"reply": "Query executed successfully, but no data was returned."})
        
        if isinstance(result, dict) and "columns" in result and "rows" in result:
            # Query returned data with columns and rows
            return JSONResponse(content={"reply":result})
        else:
            # Query returned rows without column names
            return JSONResponse(content={"reply": result})
    except Exception as e:
        return JSONResponse(content={"reply": "Sorry, there was an error."}, status_code=500)


@app.post("/upload_to_mysql")
async def upload_to_mysql(file: UploadFile = File(...), table_name: str = None):
    """
    Upload CSV/JSON to MySQL Database
    - Creates a table dynamically based on the uploaded file's schema
    - Inserts all the file's data into the created table
    """
    try:
    # Save uploaded file to a local folder
        print(f"[Inside upload_to_mysql] uploading")
        upload_folder = "uploads/"
        os.makedirs(upload_folder, exist_ok=True)
        file_location = f"{upload_folder}/{file.filename}"

        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Determine file type
        file_extension = os.path.splitext(file.filename)[1].lower()

        if not table_name:
            table_name = os.path.splitext(file.filename)[0]

        # Process CSV file
        if file_extension == ".csv":
            with open(file_location, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                columns = reader.fieldnames
                rows = [row for row in reader]

                print(f"read {len(rows)} rows from {file_location}")
                # Create a table dynamically
                create_table_query = generate_create_table_query(table_name, columns)
                print(f"creating table {create_table_query}")

                sql_obj.execute_user_query(create_table_query)

                print(f"created table {table_name}")
                # Insert data into the table
                sql_obj.insert_data_into_table(table_name, columns, rows)

        # Process JSON file
        elif file_extension == ".json":
            with open(file_location, "r", encoding="utf-8") as jsonfile:
                data = json.load(jsonfile)
                if isinstance(data, list) and len(data) > 0:
                    columns = data[0].keys()
                    rows = data

                    # Create a table dynamically
                    create_table_query = generate_create_table_query(table_name, columns)
                    sql_obj.execute_user_query(create_table_query)

                    # Insert data into the table
                    sql_obj.insert_data_into_table(table_name, columns, rows)
                else:
                    raise HTTPException(status_code=400, detail="JSON file must contain a list of objects.")

        else:
            raise HTTPException(status_code=400, detail="Only CSV and JSON files are supported.")

        return JSONResponse(content={"message": f"Data uploaded successfully to table '{table_name}'."})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/refresh_metadata")
async def refresh_metadata():
    """
    Refresh table metadata dynamically from the selected database.
    """
    try:
        global tables  # Use the global tables variable
        tables = sql_obj.get_table_metadata()  # Call helper function to fetch metadata
        return JSONResponse(content={"message": "Metadata refreshed successfully!", "tables": tables})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)