from datetime import datetime

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
            if "*" not in query:
                return self.cursor.fetchall()
            else:
                rows = self.cursor.fetchall()
                column_names = [desc[0] for desc in self.cursor.description]
                # Convert datetime to string
                processed_rows = [
                    tuple(item.isoformat() if isinstance(item, datetime) else item for item in row)
                    for row in rows
                ]
                return {"columns": column_names, "rows": processed_rows}
        return None

    def select_database(self, database_name):
        self.cursor.execute(f"USE {database_name}")

    def create_database_sample(self):
        self.cursor.execute("CREATE DATABASE IF NOT EXISTS hello_Databases")

    
    def insert_data_into_table(self, table_name, columns, rows):
        """
        Insert data into a table row by row.
        """
        placeholders = ", ".join(["%s"] * len(columns))
        query = f"INSERT INTO `{table_name}` ({', '.join(columns)}) VALUES ({placeholders})"

        # Prepare rows as tuples
        values = [tuple(row[col] for col in columns) for row in rows]

        # Execute query for all rows
        for value in values:
            self.cursor.execute(query, value)
        self.connection.commit()
    
    def get_table_metadata(self):
        metadata = {}

        # Fetch all table names
        self.cursor.execute("SHOW TABLES;")
        tables = self.cursor.fetchall()

        for (table_name,) in tables:
            # Fetch columns for each table
            self.cursor.execute(f"SHOW COLUMNS FROM {table_name};")
            columns = [column[0] for column in self.cursor.fetchall()]
            metadata[table_name] = columns

        return metadata



if __name__ == "__main__":
    sql_obj = SqlHelper()
    
    sql_obj.execute_user_query("CREATE TABLE IF NOT EXISTS hello_world_1 (id INT PRIMARY KEY, name VARCHAR(255))")
    tables = sql_obj.execute_user_query("SHOW TABLES;")
    print(f"output1: {tables}")


def generate_create_table_query(table_name, columns):
    """
    Generate a SQL query to create a table based on the provided column names.
    """
    columns_definition = ", ".join([f"`{col}` TEXT" for col in columns])  # Default to TEXT for simplicity
    query = f"CREATE TABLE IF NOT EXISTS `{table_name}` ({columns_definition});"
    return query


# def insert_data_into_table(table_name, columns, rows):
#     """
#     Insert data into a table row by row.
#     """
#     placeholders = ", ".join(["%s"] * len(columns))
#     query = f"INSERT INTO `{table_name}` ({', '.join(columns)}) VALUES ({placeholders})"

#     # Prepare rows as tuples
#     values = [tuple(row[col] for col in columns) for row in rows]

#     # Execute query for all rows
#     for value in values:
#         sql_obj.cursor.execute(query, value)
#     sql_obj.connection.commit()