import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()

SQL_HOST = os.getenv('SQL_HOST')
SQL_USER = os.getenv('SQL_USER')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')

class SqlHelper:
    def __init__(self):
        self.connection = self.create_connection()
        self.cursor = self.connection.cursor()
        # self.create_database_sample()

        # # Fetch results from SHOW DATABASES
        # self.cursor.execute('SHOW DATABASES')
        # databases = self.cursor.fetchall()
        # print(f"Databases: {databases}")
        
        self.select_database("hello_Databases")


    def create_connection(self):
        
        connection = mysql.connector.connect(
            host=SQL_HOST,
            user=SQL_USER,
            password=SQL_PASSWORD
        )

        return connection
    
    def execute_user_query(self, query):
        self.cursor.execute(query)
        # Fetch results if the query returns any
        if self.cursor.with_rows:
            return self.cursor.fetchall()
        return None

    def select_database(self, database_name):
        self.cursor.execute(f"USE {database_name}")

    def create_database_sample(self):
        self.cursor.execute("CREATE DATABASE IF NOT EXISTS hello_Databases")


if __name__ == "__main__":
    sql_obj = SqlHelper()
    
    sql_obj.execute_user_query("CREATE TABLE IF NOT EXISTS hello_world_1 (id INT PRIMARY KEY, name VARCHAR(255))")
    tables = sql_obj.execute_user_query("SHOW TABLES;")

    # print(f"type: {type(output)}")
    print(f"output1: {tables}")
    # print(f"output: {output}")
