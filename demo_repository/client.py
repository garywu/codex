import requests


def fetch_user_data(user_id):
    print(f"Fetching data for user {user_id}")
    url = f"https://api.example.com/users/{user_id}"
    response = requests.get(url)
    data = response.json()  # No error handling
    return data


def process_users(user_ids):
    results = []
    for user_id in user_ids:
        print("Processing user:", user_id)
        try:
            data = fetch_user_data(user_id)
            results.append(data)
        except:
            pass  # Bare except clause
    return results
