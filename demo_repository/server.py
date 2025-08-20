
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

@app.route('/users/<user_id>')
def get_user(user_id):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_id}"
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/update_user', methods=['POST'])
def update_user():
    data = request.json
    # No input validation
    user_id = data['id']
    name = data['name'] 
    email = data['email']
    
    print(f"Updating user {user_id}")  # Logging issue
    
    # More SQL injection
    query = f"UPDATE users SET name='{name}', email='{email}' WHERE id={user_id}"
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    conn.close()
    
    return jsonify({"status": "updated"})
