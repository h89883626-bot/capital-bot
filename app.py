import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- إعدادات الحساب والمفاتيح من متغيرة البيئة (Environment Variables) ---
CAPITAL_API_KEY = os.environ.get("CAPITAL_API_KEY", "")
CAPITAL_IDENTIFIER = os.environ.get("CAPITAL_IDENTIFIER", "")  # البريد الإلكتروني أو اسم المستخدم
CAPITAL_PASSWORD = os.environ.get("CAPITAL_PASSWORD", "")
CAPITAL_BASE_URL = os.environ.get("CAPITAL_BASE_URL", "https://demo-api-capital.backend-capital.com/api/v1")  # استخدم الرابط الحقيقي (demo/live)

# --- دالة تسجيل الدخول والحصول على جلسة العمل في Capital.com ---
def get_capital_session():
    url = f"{CAPITAL_BASE_URL}/session"
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
        print(f"Failed to authenticate with Capital.com: {response.text}")
        return None, None

# --- دالة إرسال أمر التداول إلى Capital.com ---
def place_order(epic, direction, size):
    cst, x_security_token = get_capital_session()
    if not cst or not x_security_token:
        return False, "Authentication Error with Capital.com"

    url = f"{CAPITAL_BASE_URL}/positions"
    headers = {
        "X-CAP-API-KEY": CAPITAL_API_KEY,
        "CST": cst,
        "X-SECURITY-TOKEN": x_security_token,
        "Content-Type": "application/json"
    }
    
    payload = {
        "epic": epic,            # رمز الأداة في Capital.com (مثل GOLD أو US100)
        "direction": direction,  # BUY أو SELL
        "size": float(size)      # حجم العقد
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200 or response.status_code == 201:
        return True, response.json()
    else:
        return False, response.text

# --- 1. مسار الإيقاظ وفحص الصحة (يمنع Not Found ويستجيب لخدمات Uptime) ---
@app.route('/', methods=['GET'])
@app.route('/ping', methods=['GET'])
def health_check():
    return jsonify({"status": "online", "message": "Bot is alive and running!"}), 200

# --- 2. مسار استقبال تنبيهات Webhook من TradingView ---
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            print("Received invalid JSON or empty body")
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400

        print(f"Received Payload: {data}")

        # قراءة البيانات مع ضمان تحويل الاتجاه للأنماط الكبيرة (BUY / SELL)
        ticker = data.get("ticker", "GOLD")
        action = str(data.get("action", "")).upper()
        
        # دعم قراءة اللوتس سواء كُتبت بصيغة contracts أو size
        contracts = data.get("contracts") or data.get("size") or 0.1

        if action not in ["BUY", "SELL"]:
            return jsonify({"status": "ignored", "message": f"Action '{action}' not supported"}), 200

        # تنفيذ الأمر على Capital.com
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

# --- تشغيل التطبيق ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
