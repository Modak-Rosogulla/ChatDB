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
        # print(f"{self.cursor.execute('SHOW DATABASES')}")
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

    def select_database(self, database_name):
        # try:

        self.cursor.execute(f"USE {database_name}")
        # except:


# def create_database(connection):
#     cursor = connection.cursor()
#     cursor.execute("CREATE DATABASE IF NOT EXISTS hello_Databases")
#     cursor.execute("USE hello_Databases")


# def create_sample_table(connection):
#     cursor = connection.cursor()
#     # cursor.execute("CREATE TABLE hello_world (id INT PRIMARY KEY, name VARCHAR(255))")    
#     cursor.execute("CREATE TABLE IF NOT EXISTS hello_world (id INT PRIMARY KEY, name VARCHAR(255))")    


# def view_all_tables(connection):
#     cursor = connection.cursor()
#     cursor.execute("SHOW TABLES")
#     for table in cursor:
#         print(table)


# def run_user_query(connection, query):
#     cursor = connection.cursor()
#     cursor.execute(query)


if __name__ == "__main__":
    sql_obj = SqlHelper()
    
    output = sql_obj.execute_user_query("SHOW TABLES;")

    print(f"type: {type(output)}")
    print(f"output: {output}")
