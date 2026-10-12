import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# إعدادات حساب Capital.com الحقيقي (Live)
CAPITAL_URL = "https://api-capital.backend-capital.com/api/v1"

# استدعاء البيانات من متغيرات البيئة أو تعيينها مباشرة
API_KEY = os.getenv("CAPITAL_API_KEY", "RDOj635EeNudIXcx")
API_PASSWORD = os.getenv("CAPITAL_PASSWORD", "")
IDENTIFIER = os.getenv("CAPITAL_IDENTIFIER", "")  # البريد الإلكتروني الخاص بحسابك في Capital.com


def get_session():
    """إنشاء جلسة تداول واستخراج التوكينات (CST & X-SECURITY-TOKEN)"""
    url = f"{CAPITAL_URL}/session"
    headers = {
        "X-CAP-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "identifier": IDENTIFIER,
        "password": API_PASSWORD
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        cst = response.headers.get("CST")
        x_sec = response.headers.get("X-SECURITY-TOKEN")
        return cst, x_sec
    else:
        print(f"خطأ في تسجيل الدخول: {response.status_code} - {response.text}")
        return None, None


@app.route("/", methods=["GET", "HEAD"])
def home():
    """نقطة فحص الرابط وإيقاظ السيرفر"""
    return "Capital.com Live Trading Bot is Running!", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    """استقبال إشارات TradingView وتنفيذ الصفقات الحقيقية"""
    data = request.json
    print("تم استلام إشارة من TradingView:", data)

    if not data:
        return jsonify({"status": "error", "message": "لم يتم استلام أي بيانات JSON"}), 400

    ticker = data.get("ticker", "GOLD")
    action = data.get("action", "").upper()  # BUY أو SELL
    size = data.get("contracts", 1)  # عدد العقود

    # تحديد اتجاه الصفقة
    direction = "BUY" if action == "BUY" else "SELL"

    # تسجيل الدخول وتوليد التوكين
    cst, x_sec = get_session()
    if not cst or not x_sec:
        return jsonify({"status": "error", "message": "فشل الاتصال بمنصة Capital.com"}), 500

    # إرسال أمر فتح الصفقة إلى API
    order_url = f"{CAPITAL_URL}/positions"
    order_headers = {
        "X-CAP-API-KEY": API_KEY,
        "CST": cst,
        "X-SECURITY-TOKEN": x_sec,
        "Content-Type": "application/json"
    }
    order_payload = {
        "epic": ticker,
        "direction": direction,
        "size": float(size)
    }

    order_res = requests.post(order_url, json=order_payload, headers=order_headers)

    if order_res.status_code == 200:
        print(f"تم تنفيذ الصفقة بنجاح على الحساب الحقيقي! {direction} {size} {ticker}")
        return jsonify({"status": "success", "response": order_res.json()}), 200
    else:
        print(f"خطأ أثناء تنفيذ الصفقة: {order_res.status_code} - {order_res.text}")
        return jsonify({"status": "error", "details": order_res.text}), order_res.status_code


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
