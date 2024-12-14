# ChatDB

ChatDB is a user-friendly web application that allows users to interact with both SQL and NoSQL databases using natural language. It leverages advanced NLP techniques to generate database queries seamlessly, enabling efficient data exploration and management.

---

## Setup Instructions

Follow the steps below to set up and run ChatDB on your local environment:

### Step 1: Create a Virtual Environment
Run the following command to create a virtual environment:
```bash
python -m venv chatdb_env
```
### Step 2: Activate the virtual environment:

For Windows
```bash
chatdb_env\Scripts\activate
```

For Linux
```bash
source chatdb_env/bin/activate
```

### Step 3: Install required dependencies
```bash
pip install -r requirements.txt
```

### Step 4:
Configure environment variables by filling the .env file with the appropriate URLs for MySQL & Firebase links

### Step 5: Run
Please check http://localhost:8000 (or the link that appears) after running the following command.
```bash
python main.py
```

### Step 6: Data Upload
To upload data to Firebase, upload JSON to the main page.


To upload data to MySQL, navigate to MySQL then upload a csv file.

### Step 7: MySQL

1. Navigate to MySQL and Select a database from the dropdown.
2. Upload data if not done so from samples provided or your own data.
3. Write "show tables;" to see the schema.
4. Write SQL queries as if writing in a mysql shell. 
5. Sample Query generation = Write "generate 5 queries with where clause"


### Step 8: Firebase
1. Upload data from the main page (optional).
2. Navigate to Firebase.
3. Interact with the expandable data visualization.
4. PUT 
```bash
PUT=colleges.json={"USC": {"city":"Los Angeles", "expertise":["Computer Science", "Cinematics", "Robotics"] }, "UCI": {"city": "Los Angeles", "expertise":["Computer Science", "Compilers"] }, "UCSD": {"city": "San Diego", "expertise": "Natural Language Processing"}}
```

5. GET
```bash
GET=colleges/USC/expertise.json
```

6. DELETE
```bash
DELETE=colleges/UCSD.json
```

## Enjoy ChatDB!





