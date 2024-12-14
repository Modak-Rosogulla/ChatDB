import nltk
import re
import os
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import random
print(nltk.data.path)
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

SQL_KEYWORDS = {"select", "from", "where", "group", "by", "having", "order", "limit", "sum","not", "equal", "greater", "less", "between", "and", "or", "in","count"}
SQL_KEYWORDS_ONLY = {"where", "group", "by", "having", "order", "limit"}


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

def prioritize_by_query_context(tokens, matched_metadata):
    """
    Prioritize tables based on the order of tokens in the user query.

    Args:
        tokens (list): List of tokens from the user query.
        matched_metadata (dict): Matched tables and columns.

    Returns:
        dict: Updated metadata prioritizing tables by query context.
    """
    resolved_metadata = {}
    for token in tokens:
        for table, columns in matched_metadata.items():
            if token in columns or token == table:
                if table not in resolved_metadata:
                    resolved_metadata[table] = []
                if token in columns and token not in resolved_metadata[table]:
                    resolved_metadata[table].append(token)
    return resolved_metadata


# Function to preprocess the user query (Tokenization, Lemmatization, Stopwords Removal)
def preprocess_query(query):
    try:
        print(f"Raw query: {query}")  # Debug input
        synonyms = {
            "ordered by": "order by",
            "list": "select",
            "rows": "*",
            "top": "limit",  # 'TOP X rows' can translate to 'LIMIT X'
            "from table": "from",  # Normalize 'from table' to 'from'
        }

        # Normalize case and replace phrases
        query = query.lower()  # Case normalization
        for phrase, replacement in synonyms.items():
            query = query.replace(phrase, replacement)

        # Tokenize and process the query
        tokens = word_tokenize(query)

        tokens = [lemmatizer.lemmatize(token.lower()) for token in tokens if token.lower() not in stop_words or token.lower() in SQL_KEYWORDS]
        print(f"Tokens: {tokens}")   # Debug tokens
        return tokens
    except Exception as e:
        print(f"Error in word_tokenize: {e}")
        raise


def map_tokens_to_metadata(tokens, tables):
    """
    Map tokens to tables and columns, resolving ambiguities using query context.

    Args:
        tokens (list): List of tokens from the query.
        tables (dict): Metadata containing table-column mappings.

    Returns:
        dict: Prioritized metadata mapping tables to their matched columns.
    """
    matched_metadata = {}
    explicit_tables = set()

    for i, token in enumerate(tokens):
        # Match explicit table references (e.g., "in actor")
        if token in tables:
            explicit_tables.add(token)

        # Match columns in all tables
        for table, columns in tables.items():
            if token in columns:
                if table not in matched_metadata:
                    matched_metadata[table] = []
                matched_metadata[table].append(token)

    # If explicit tables are mentioned, filter metadata to include only those tables
    if explicit_tables:
        matched_metadata = {table: matched_metadata.get(table, []) for table in explicit_tables}

    return matched_metadata


# Function to generate SQL query based on detected clauses and metadata
def generate_sql_query(tokens, metadata):
    """
    Generate SQL query dynamically based on tokens and detected clauses.

    Args:
        tokens (list): Preprocessed tokens from the user query.
        metadata (dict): Metadata containing table-column mappings (table: [columns]).

    Returns:
        str: Generated SQL query or an error message.
    """
    if not metadata:
        return "Error: No tables or columns matched in the query."

    # Detect SQL clauses and keywords
    has_group_by = "group" in tokens and "by" in tokens
    has_having = "having" in tokens
    has_where = "where" in tokens
    has_order_by = "order" in tokens and "by" in tokens
    has_limit = "limit" in tokens or "top" in tokens
    has_like = "like" in tokens
    has_count = "count" in tokens  # Detect aggregate functions
    has_join = len(metadata) > 1
    has_union = "union" in tokens

    # Define valid operators and their SQL equivalents
    operator_map = {
        "equal": "=",
        "not equal": "!=",
        "greater than": ">",
        "less than": "<",
        "greater or equal": ">=",
        "less or equal": "<=",
    }

    # Prepare components for query construction
    selected_columns = []
    conditions = []
    having_conditions = []
    limit_value = None
    order_by_column = None
    order_direction = "ASC"
    query = ""

    # Handle aggregate functions
    if has_count:
        selected_columns = ["COUNT(*)"]

    # Handle 'TOP X rows'
    if "top" in tokens:
        top_index = tokens.index("top") + 1
        if top_index < len(tokens) and tokens[top_index].isdigit():
            limit_value = int(tokens[top_index])

    # Handle ORDER BY
    if has_order_by:
        order_index = tokens.index("by") + 1
        if order_index < len(tokens):
            order_by_column = tokens[order_index]
            for table, columns in metadata.items():
                if order_by_column in columns:
                    order_by_column = f"{table}.{order_by_column}"
                    break
        if "desc" in tokens:
            order_direction = "DESC"

    # Handle WHERE clause
    if has_where:
        where_index = tokens.index("where") + 1
        where_tokens = tokens[where_index:]

        i = 0
        while i < len(where_tokens):
            # Look for multi-token operators (e.g., "not equal", "greater than")
            if i + 1 < len(where_tokens) and f"{where_tokens[i]} {where_tokens[i + 1]}" in operator_map:
                column = where_tokens[i - 1]
                operator = operator_map[f"{where_tokens[i]} {where_tokens[i + 1]}"]
                value = where_tokens[i + 2] if i + 2 < len(where_tokens) else "''"
                # Ensure column is valid
                for table, columns in metadata.items():
                    if column in columns:
                        column = f"{table}.{column}"
                        break
                conditions.append(f"{column} {operator} {value}")
                i += 3  # Skip operator and value
            elif where_tokens[i] in operator_map:
                column = where_tokens[i - 1]
                operator = operator_map[where_tokens[i]]
                value = where_tokens[i + 1] if i + 1 < len(where_tokens) else "''"
                # Ensure column is valid
                for table, columns in metadata.items():
                    if column in columns:
                        column = f"{table}.{column}"
                        break
                conditions.append(f"{column} {operator} {value}")
                i += 2  # Skip operator and value
            else:
                i += 1

    # Handle LIKE clause
    if has_like:
        like_index = tokens.index("like") + 1
        like_value = tokens[like_index] if like_index < len(tokens) else "''"
        column = next((f"{table}.{col}" for table, cols in metadata.items() for col in cols), "id")
        conditions.append(f"{column} LIKE '{like_value}'")

    # Handle HAVING clause
    if has_having:
        having_index = tokens.index("having") + 1
        having_condition = " ".join(tokens[having_index:]).strip()
        if having_condition:
            having_conditions.append(having_condition)

    # Determine selected columns if not using aggregates
    if not selected_columns:
        for table, columns in metadata.items():
            selected_columns.extend([f"{table}.{col}" for col in columns])

    # Default to "*" if no explicit columns are selected
    if '*' in tokens or not selected_columns:
        selected_columns = ["*"]

    # Construct SELECT query
    tables = list(metadata.keys())
    query = f"SELECT {', '.join(selected_columns)} FROM {tables[0]}"

    # Add JOIN clause if multiple tables are present
    if has_join:
        for table in tables[1:]:
            query += f" JOIN {table} ON {tables[0]}.id = {table}.id"

    # Append WHERE clause if conditions exist
    if conditions:
        query += f" WHERE {' AND '.join(conditions)}"

    # Handle GROUP BY and HAVING clauses
    if has_group_by:
        group_by_index = tokens.index("by") + 1
        group_column = tokens[group_by_index] if group_by_index < len(tokens) else selected_columns[0]
        query += f" GROUP BY {group_column}"
        if having_conditions:
            query += f" HAVING {' AND '.join(having_conditions)}"
        elif not having_conditions and has_having:
            return "Error: HAVING clause requires a GROUP BY clause."

    # Add ORDER BY clause
    if order_by_column:
        query += f" ORDER BY {order_by_column} {order_direction}"

    # Handle LIMIT clause
    if has_limit:
        if "limit" in tokens:
            limit_index = tokens.index("limit") + 1
            if limit_index < len(tokens) and tokens[limit_index].isdigit():
                limit_value = int(tokens[limit_index])
        if limit_value:
            query += f" LIMIT {limit_value}"

    # Handle UNION clause
    if has_union:
        query1 = "SELECT * FROM table1"
        query2 = "SELECT * FROM table2"
        query = query_templates["union"].format(query1=query1, query2=query2)

    return query

# Main function to process user input and generate a query
def process_user_query(query,table):
    global tables
    tables = table
    # Step 1: Preprocess the input query
    tokens = preprocess_query(query)
    
    if "generate" in tokens:
        # Use regex to extract the number of queries and the clause type
        match = re.search(r"generate\s+(\d+)\s+queries\s+with\s+(.+)", query, re.IGNORECASE)
        if match:
            try:
                num_queries = int(match.group(1))  # Extract number of queries
                clause_type_raw = match.group(2).strip().lower()  # Extract clause type
                # Match clause type with SQL keywords
                clause_type = next((clause for clause in SQL_KEYWORDS_ONLY if clause in clause_type_raw), None)
                if not clause_type:
                    return "Error: Unsupported clause type. Supported types: WHERE, HAVING, ORDER BY, LIMIT."
                return generate_random_queries(tables, num_queries, clause_type)
            except ValueError:
                return "Error: Invalid number of queries. Example: 'generate 5 queries with WHERE clause'."
        else:
            return "Error: Invalid syntax. Example: 'generate 5 queries with WHERE clause'."


    # Step 2: Map tokens to table and column metadata
    metadata = map_tokens_to_metadata(tokens, tables)

    # Handle missing metadata gracefully
    if not metadata:
        return "Error: No matching table or columns found for your query."
    # if not matched_column:
    #     return f"Error: No matching column found in table '{matched_table}'."
    
    # Step 3: Generate SQL query based on the matched information
    generated_query = generate_sql_query(tokens, metadata)
    
    return generated_query

import random

def generate_random_queries(metadata, num_queries, clause_type):
    """
    Generate random SQL queries based on the provided clause type and metadata.

    Args:
        metadata (dict): Metadata containing table-column mappings (table: [columns]).
        num_queries (int): Number of queries to generate.
        clause_type (str): Clause type to include in the queries (e.g., "HAVING", "WHERE").

    Returns:
        list: A list of randomly generated SQL queries.
    """
    if not metadata:
        return "Error: No metadata provided for generating queries."

    queries = []
    clause_type = clause_type.lower()

    for _ in range(num_queries):
        # Select a random table and its columns
        table = random.choice(list(metadata.keys()))
        columns = metadata[table]
        
        if not columns:
            return f"Error: No columns found for table '{table}'."

        # Generate SELECT clause
        selected_columns = random.sample(columns, k=min(len(columns), random.randint(1, 3)))
        select_clause = f"SELECT {', '.join(selected_columns)} FROM {table}"

        # Generate WHERE clause
        if clause_type == "where":
            column = random.choice(columns)
            operator = random.choice(["=", "!=", ">", "<", ">=", "<="])
            value = random.randint(1, 100)
            where_clause = f" WHERE {column} {operator} {value}"
            query = select_clause + where_clause

        # Generate HAVING clause
        elif clause_type == "having":
            group_by_column = random.choice(columns)
            aggregate_column = random.choice(columns)
            operator = random.choice([">", "<", ">=", "<="])
            value = random.randint(1, 100)
            having_clause = f" GROUP BY {group_by_column} HAVING SUM({aggregate_column}) {operator} {value}"
            query = select_clause + having_clause

        # Generate ORDER BY clause
        elif clause_type == "order by":
            order_by_column = random.choice(columns)
            direction = random.choice(["ASC", "DESC"])
            order_by_clause = f" ORDER BY {order_by_column} {direction}"
            query = select_clause + order_by_clause

        # Generate LIMIT clause
        elif clause_type == "limit":
            limit_value = random.randint(1, 100)
            limit_clause = f" LIMIT {limit_value}"
            query = select_clause + limit_clause

        # Default or unsupported clause
        else:
            query = select_clause

        queries.append(query)

    return "\n\n".join([f"Query {i + 1}:\n{query}" for i, query in enumerate(queries)])


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
