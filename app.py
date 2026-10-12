from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# إعدادات الحساب وبيانات الاعتماد
API_KEY = os.getenv("CAPITAL_API_KEY", "RDOj635EeNudIXcx")
API_PASSWORD = os.getenv("CAPITAL_PASSWORD", "Bot11987@")
# معرف المستخدم أو البريد الخاص بحساب Capital.com إذا لزم الأمر، أو يتم الاعتماد على المفتاح
API_IDENTIFIER = os.getenv("CAPITAL_IDENTIFIER", "") 

# رابط الـ API الرسمي لمنصة Capital.com (استخدم البيلو/الديمو أو الحقيقي حسب حسابك)
# للوضع التجريبي (Demo): https://demo-api-capital.backend-capital.com/api/v1
# للوضع الحقيقي (Live): https://api-capital.backend-capital.com/api/v1
BASE_URL = "https://demo-api-capital.backend-capital.com/api/v1"

def get_session_tokens():
    """الحصول على رموز الجلسة للتصريح بعمليات التداول"""
    url = f"{BASE_URL}/session"
    headers = {
        "X-CAP-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "identifier": API_IDENTIFIER,
        "password": API_PASSWORD
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            cst = response.headers.get("CST")
            x_security_token = response.headers.get("X-SECURITY-TOKEN")
            return cst, x_security_token
    except Exception as e:
        print(f"Auth Error: {e}")
    return None, None

@app.route('/', methods=['GET'])
def home():
    return "Capital Trading Bot with API Execution is Active!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True, silent=True)
        
        if not data:
            import json
            if request.data:
                data = json.loads(request.data.decode('utf-8'))
            else:
                return jsonify({"status": "error", "message": "No data received"}), 400

        action = data.get("action")      # buy أو sell
        ticker = data.get("ticker")      # رمز الأصل (مثلاً GOLD)
        contracts = data.get("contracts", 1) # عدد العقود أو حجم الصفقة
        price = data.get("price")        # السعر
        
        print(f"تم استلام إشارة من ترندفيو: {action} للأصل {ticker} بعدد {contracts}")

        # تنفيذ الطلب فعلياً في منصة Capital.com
        cst, x_token = get_session_tokens()
        if not cst or not x_token:
            return jsonify({"status": "error", "message": "Failed to authenticate with Capital.com"}), 401

        trade_url = f"{BASE_URL}/positions"
        headers = {
            "X-CAP-API-KEY": API_KEY,
            "CST": cst,
            "X-SECURITY-TOKEN": x_token,
            "Content-Type": "application/json"
        }
        
        # تحويل صيغة أمر TradingView إلى صيغة طلب Capital.com
        # direction تكون 'BUY' أو 'SELL'
        direction = "BUY" if str(action).upper() in ["BUY", "LONG"] else "SELL"
        
        trade_payload = {
            "epic": ticker,
            "direction": direction,
            "size": float(contracts),
            "guaranteedStopLoss": False,
            "type": "MARKET" # أمر مباشر بسعر السوق
        }

        trade_response = requests.post(trade_url, json=trade_payload, headers=headers)
        
        if trade_response.status_code in [200, 201]:
            print("تم تنفيذ الصفقة بنجاح على المنصة!")
            return jsonify({"status": "success", "message": "Order executed on Capital.com"}), 200
        else:
            print(f"فشل التنفيذ: {trade_response.text}")
            return jsonify({"status": "error", "details": trade_response.text}), 400

    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
