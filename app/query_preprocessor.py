import nltk
import re
import os
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import random
print(nltk.data.path)
# print("Tokenizers Path Exists:", "tokenizers/punkt" in nltk.data.find("tokenizers/punkt").path)
# Download necessary NLTK resources
current_dir = os.path.dirname(os.path.abspath(__file__))
nltk_data_dir = os.path.join(current_dir, "nltk_data")
nltk.data.path.append(nltk_data_dir)  # Add this directory to NLTK's search path

# Download the 'punkt' resource
nltk.download('punkt', download_dir=nltk_data_dir)
nltk.download('punkt_tab', download_dir=nltk_data_dir)

nltk.download('stopwords', download_dir=nltk_data_dir)
nltk.download('wordnet', download_dir=nltk_data_dir)

print(nltk.data.path)
print("Tokenizers Path Exists:", "tokenizers/punkt" in nltk.data.find("tokenizers/punkt").path)

# Initialize the NLTK components
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

SQL_KEYWORDS = {"select", "from", "where", "group", "by", "having", "order", "limit", "sum"}


# # Sample table metadata
tables = {}

# SQL Query templates for different constructs
query_templates = {
    'select': "SELECT {columns} FROM {table};",
    'join': "SELECT {columns} FROM {table1} {join_type} JOIN {table2} ON {on_condition};",
    'union': "{query1} UNION {query2};",
    'group_by': "SELECT {column}, SUM({aggregate_column}) AS total_qty FROM {table} GROUP BY {column};",
    'having': "SELECT {column}, SUM({aggregate_column}) AS total_qty FROM {table} GROUP BY {column} HAVING {condition};",
    'where': "SELECT * FROM {table} WHERE {conditions};",
    'order_by': "SELECT {columns} FROM {table} ORDER BY {column} {order};",
    'limit': "{query} LIMIT {limit};"
}


# Function to preprocess the user query (Tokenization, Lemmatization, Stopwords Removal)
def preprocess_query(query):
    try:
        print(f"Raw query: {query}")  # Debug input
        tokens = word_tokenize(query)
        print(f"Tokens: {tokens}")   # Debug tokens
        tokens = [lemmatizer.lemmatize(token.lower()) for token in tokens if token.lower() not in stop_words or token.lower() in SQL_KEYWORDS]
        return tokens
    except Exception as e:
        print(f"Error in word_tokenize: {e}")
        raise

# Function to match tokens to tables and columns
def map_tokens_to_metadata(tokens, tables):
    matched_table = None
    matched_column = None
    
    # Check for table and column matches
    for token in tokens:
        if token in tables.keys():  # Check only against table names
            matched_table = token
            break  # Once a table is matched, no need to check further

    if matched_table:
        for token in tokens:
            if token in tables[matched_table]:  # Check only columns of the matched table
                matched_column = token
                break 
    
    return matched_table, matched_column

# Function to generate SQL query based on detected clauses and metadata
def generate_sql_query(tokens, matched_table, matched_column):
    """
    Generate SQL query dynamically based on tokens and detected clauses.

    Args:
        tokens (list): Preprocessed tokens from the user query.
        matched_table (str): Matched table name.
        matched_column (str): Matched column name.
        metadata (dict): Metadata containing table-column mappings.

    Returns:
        str: Generated SQL query or an error message.
    """
    if not matched_table:
        return "Error: No table matched in the query."

    # Detect SQL clauses and keywords
    has_group_by = "group" in tokens and "by" in tokens
    has_having = "having" in tokens
    has_where = "where" in tokens or "like" in tokens
    has_order_by = "order" in tokens and "by" in tokens
    has_limit = "limit" in tokens
    has_like = "like" in tokens
    has_join = "join" in tokens
    has_union = "union" in tokens

    # Default values
    columns = matched_column if matched_column else "*"
    if "row" in tokens:
        columns = "*"
    aggregate_column = next(iter(tables.get(matched_table, [])), "id")  # Default to the first column or 'id'
    query = ""
    conditions = []  # Collect conditions dynamically
    having_conditions = []  # Collect HAVING conditions separately

    # Handle LIKE and WHERE clauses
    if has_like:
        like_index = tokens.index("like") + 1
        like_value = tokens[like_index] if like_index < len(tokens) else "''"
        conditions.append(f"{matched_column} LIKE '{like_value}'")

    if has_where:
        where_index = tokens.index("where") + 1 if "where" in tokens else 0
        where_conditions = " ".join(tokens[where_index:]).strip()
        if where_conditions and not has_like:  # Avoid duplicating LIKE
            conditions.append(where_conditions)

    # Handle HAVING clause for aggregated conditions
    if has_having:
        having_index = tokens.index("having") + 1
        having_condition = " ".join(tokens[having_index:]).strip()
        if having_condition and not any(cond in having_condition for cond in conditions):  # Avoid duplication
            having_conditions.append(having_condition)

    # Construct WHERE clause if there are conditions
    if conditions:
        query = query_templates['where'].format(
            columns=columns,
            table=matched_table,
            conditions=" AND ".join(conditions)
        )

    if having_conditions:
        if "GROUP BY" in query.upper():  # Ensure GROUP BY exists
            query += f" HAVING {' AND '.join(having_conditions)}"
        elif not query :
            return "Error: HAVING clause requires a GROUP BY clause."

    # Handle GROUP BY clause
    if has_group_by:
        group_by_index = tokens.index("by") + 1
        group_column = tokens[group_by_index] if group_by_index < len(tokens) else matched_column
        query = query_templates['group_by'].format(
            column=group_column,
            aggregate_column=aggregate_column,
            table=matched_table
        )
        # Append HAVING to GROUP BY if present
        if having_conditions:
            query += f" HAVING {' AND '.join(having_conditions)}"

    # Handle ORDER BY clause
    if has_order_by:
        order_index = tokens.index("by") + 1
        order_column = tokens[order_index] if order_index < len(tokens) else matched_column
        order_direction = "DESC" if "desc" in tokens else "ASC"
        query += f" ORDER BY {order_column} {order_direction}"

    # Handle LIMIT clause
    if has_limit:
        limit_index = tokens.index("limit") + 1
        limit_value = tokens[limit_index] if limit_index < len(tokens) else "10"
        query += f" LIMIT {limit_value}"

    # Handle JOIN clause
    if has_join:
        join_index = tokens.index("join") + 1
        join_table = tokens[join_index] if join_index < len(tokens) else None
        on_condition = " ".join(tokens[join_index + 1:]).strip() if join_table else "table1.id = table2.id"
        join_type = "INNER" if "inner" in tokens else "LEFT" if "left" in tokens else "RIGHT" if "right" in tokens else "INNER"
        query = query_templates['join'].format(
            columns=columns,
            table1=matched_table,
            join_type=join_type,
            table2=join_table or "another_table",
            on_condition=on_condition
        )

    # Handle UNION clause
    if has_union:
        union_index = tokens.index("union")
        query1 = "SELECT * FROM table1"  # Replace with logic to extract query1
        query2 = "SELECT * FROM table2"  # Replace with logic to extract query2
        query = query_templates['union'].format(
            query1=query1,
            query2=query2
        )

    # Default SELECT query if no specific clause is detected
    if not query:
        query = query_templates['select'].format(
            columns=columns,
            table=matched_table
        )

    return query

# Main function to process user input and generate a query
def process_user_query(query,table):
    global tables
    tables = table
    # Step 1: Preprocess the input query
    tokens = preprocess_query(query)
    
    # Step 2: Map tokens to table and column metadata
    matched_table, matched_column = map_tokens_to_metadata(tokens, tables)

    # Handle missing metadata gracefully
    if not matched_table:
        return "Error: No matching table found for your query."
    if not matched_column:
        return f"Error: No matching column found in table '{matched_table}'."
    
    # Step 3: Generate SQL query based on the matched information
    generated_query = generate_sql_query(tokens, matched_table, matched_column)
    
    return generated_query

# # Example queries to test the system
# queries = [
#     "Show me a query with HAVING",
#     "Show me a query with GROUP BY",
#     "Group products by category",
#     "Where transaction_id = 20"
# ]

# for query in queries:
#     print(f"Input Query: {query}")
#     print(f"Generated SQL: {process_user_query(query)}")
#     print("-" * 60)
