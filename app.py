import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# استدعاء البيانات الحساسة من المتغيرات البيئية
CAPITAL_API_KEY = os.getenv("CAPITAL_API_KEY")
CAPITAL_PASSWORD = os.getenv("CAPITAL_PASSWORD")
CAPITAL_IDENTIFIER = os.getenv("CAPITAL_IDENTIFIER", "h89883626@gmail.com")  # بريدك الإلكتروني في كابيتال

BASE_URL = "https://api-capital.backend-capital.com/api/v1"

def get_session():
    """تسجيل الدخول لجلب جلسة التداول CST و X-SECURITY-TOKEN"""
    url = f"{BASE_URL}/session"
    headers = {
        "X-CAP-API-KEY": CAPITAL_API_KEY,
        "Content-Type": "application/json"
    }
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
        print("فشل تسجيل الدخول:", response.json())
        return None, None

@app.route("/", methods=["GET"])
def home():
    return "Capital.com Webhook Bot is Running Successfully!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No JSON data received"}), 400

    print("تنبيه جديد من TradingView:", data)

    # استخراج البيانات القادمة من التنبيه
    epic = data.get("epic")          # مثل: GOLD, US500, TSLA
    direction = data.get("action")    # BUY أو SELL
    size = data.get("size", 1)        # حجم الصفقة

    if not epic or not direction:
        return jsonify({"status": "error", "message": "Missing epic or action"}), 400

    cst, x_security_token = get_session()
    if not cst or not x_security_token:
        return jsonify({"status": "error", "message": "Authentication failed with Capital.com"}), 500

    # إرسال أوردر التداول إلى كابيتال
    order_url = f"{BASE_URL}/positions"
    order_headers = {
        "CST": cst,
        "X-SECURITY-TOKEN": x_security_token,
        "Content-Type": "application/json"
    }
    
    payload = {
        "epic": epic,
        "direction": direction.upper(),
        "size": float(size)
    }

    res = requests.post(order_url, json=payload, headers=order_headers)
    
    if res.status_code == 200:
        return jsonify({"status": "success", "capital_response": res.json()}), 200
    else:
        return jsonify({"status": "failed", "capital_response": res.json()}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
