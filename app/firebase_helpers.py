import pandas as pd
import json
import requests
import sys

# Firebase Database URL (replace with your actual Firebase URL)
# DATABASE_URL = "https://homework1-8757c-default-rtdb.firebaseio.com/"
DATABASE_URL = "https://dsci551-877cc-default-rtdb.firebaseio.com/"

# 1. Load data from csv
def load_data_to_firebase(csv_file):
    # INPUT : Path to the CSV file
    # RETURN : Status code after Python REST call to add the data [response.status_code]
    # EXPECTED RETURN : 200
    df = pd.read_csv(csv_file)

    df['transaction_id'] = df['transaction_id'].astype(str)

    data_dict = df.set_index('transaction_id').to_dict(orient='index')

    response = requests.put(DATABASE_URL + "/transactions.json", json=data_dict)

    return response.status_code

# 2. Search by ID
def search_by_id(transaction_id):
    # INPUT : Transaction ID
    # RETURN : JSON object of the transaction details for the given ID or None if not found
    # EXPECTED RETURN: {"product_category": "Coffee", "product_detail": "Jamaican Coffee River Rg", ...} or None
    try:
        transaction_id = str(int(transaction_id))
    except:
        return None

    url = f"{DATABASE_URL}/transactions/{transaction_id}.json/"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data is not None:
            return data
        else:
            return None
    else:
        return None 

# 3. Create an index on product_type
def create_index_on_product_type(csv_file):
    # INPUT : Path to the CSV file
    # RETURN : Status code after Python REST call to add the index [response.status_code]
    # EXPECTED RETURN : 200
    index = {}
    df = pd.read_csv(csv_file)
    
    for _, row in df.iterrows():
        product_type = str(row['product_type'])
        transaction_id = str(row['transaction_id'])

        keywords = product_type.split(" ")
        
        for keyword in keywords:
            keyword = keyword.lower()
            if keyword not in index:
                index[keyword] = []
        
            index[keyword].append(transaction_id)

    response = requests.put(f"{DATABASE_URL}product_type_index.json", json=index)
    return response.status_code

# 4. Search by keywords
def search_by_keywords(keywords):
    # INPUT : Space separated keywords.
    # RETURN : List of transaction IDs with product_type having all the keywords or Empty list if not found
    # EXPECTED RETURN : [1,7,4,789] or []
    keyword_list = keywords.lower().split()

    lists_of_ids = []
    for keyword in keyword_list:
        url = f"{DATABASE_URL}/product_type_index/{keyword}.json"
        response = requests.get(url)

        if response.status_code == 200:
            ids = response.json()
            if ids is not None:
                lists_of_ids.append(set(ids))
            else:
                return []
        else:
            return []

    if lists_of_ids:
        common_ids = set.intersection(*lists_of_ids)
        return [int(id_) for id_ in common_ids]
    else:
        return []

# Main execution logic
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py [operation] [arguments]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "load":
        csv_file = sys.argv[2]
        result = load_data_to_firebase(csv_file)
        print(result)
    
    elif command == "search_by_id":
        transaction_id = sys.argv[2]
        transaction = search_by_id(transaction_id)
        print(transaction)
    
    elif command == "create_index":
        csv_file = sys.argv[2]
        result = create_index_on_product_type(csv_file)
        print(result)
    
    elif command == "search_by_keywords":
        keywords = sys.argv[2]
        result_ids = search_by_keywords(keywords)
        print(result_ids)
    
    else:
        print("Invalid command. Use 'load', 'search_by_id', 'create_index', or 'search_by_keywords'.")
