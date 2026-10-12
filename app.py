import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

CAPITAL_API_KEY = os.environ.get("CAPITAL_API_KEY", "")
CAPITAL_IDENTIFIER = os.environ.get("CAPITAL_IDENTIFIER", "")
CAPITAL_PASSWORD = os.environ.get("CAPITAL_PASSWORD", "")
CAPITAL_BASE_URL = os.environ.get("CAPITAL_BASE_URL", "https://api-capital.backend-capital.com/api/v1")

COMMON_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_capital_session():
    url = f"{CAPITAL_BASE_URL}/session"
    headers = COMMON_HEADERS.copy()
    headers["X-CAP-API-KEY"] = CAPITAL_API_KEY
    
    payload = {
        "identifier": CAPITAL_IDENTIFIER,
        "password": CAPITAL_PASSWORD
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        cst = response.headers.get("CST")
        x_security_token = response.headers.get("X-SECURITY-TOKEN")
        return cst, x_security_token
    else:
        print(f"Failed to authenticate with Capital.com: {response.text}")
        return None, None

def place_order(epic, direction, size):
    cst, x_security_token = get_capital_session()
    if not cst or not x_security_token:
        return False, "Authentication Error with Capital.com"

    url = f"{CAPITAL_BASE_URL}/positions"
    headers = COMMON_HEADERS.copy()
    headers["X-CAP-API-KEY"] = CAPITAL_API_KEY
    headers["CST"] = cst
    headers["X-SECURITY-TOKEN"] = x_security_token
    
    payload = {
        "epic": epic,
        "direction": direction,
        "size": float(size)
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code in [200, 201]:
        return True, response.json()
    else:
        return False, response.text

@app.route('/', methods=['GET'])
@app.route('/ping', methods=['GET'])
def health_check():
    return jsonify({"status": "online", "message": "Bot is alive and running!"}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            print("Received invalid JSON or empty body")
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400

        print(f"Received Payload: {data}")

        ticker = data.get("ticker", "GOLD")
        action = str(data.get("action", "")).upper()
        contracts = data.get("contracts") or data.get("size") or 0.1

        if action not in ["BUY", "SELL"]:
            return jsonify({"status": "ignored", "message": f"Action '{action}' not supported"}), 200

        success, result = place_order(epic=ticker, direction=action, size=contracts)

        if success:
            print(f"Order executed successfully: {result}")
            return jsonify({"status": "success", "data": result}), 200
        else:
            print(f"Failed to place order: {result}")
            return jsonify({"status": "error", "details": result}), 500

    except Exception as e:
        print(f"Internal Server Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
