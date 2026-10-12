import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# إعداد بيانات الاعتماد من متغيرات البيئة في Render
CAPITAL_IDENTIFIER = os.environ.get("CAPITAL_IDENTIFIER")
CAPITAL_PASSWORD = os.environ.get("CAPITAL_PASSWORD")
CAPITAL_API_KEY = os.environ.get("CAPITAL_API_KEY")

# روابط البيئة الحقيقية (Live) لمنصة Capital.com
BASE_URL = "https://api-capital.backend-capital.com/api/v1"

HEADERS_BROWSER = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
    "X-CAP-API-KEY": CAPITAL_API_KEY,
}


def capital_login():
  """تسجيل الدخول تلقائياً للحصول على رموز الجلسة المحدثة"""
  login_url = f"{BASE_URL}/session"
  payload = {
      "identifier": CAPITAL_IDENTIFIER,
      "password": CAPITAL_PASSWORD,
  }
  try:
    response = requests.post(
        login_url, json=payload, headers=HEADERS_BROWSER, timeout=10
    )
    if response.status_code == 200:
      cst = response.headers.get("CST")
      x_security_token = response.headers.get("X-SECURITY-TOKEN")
      print("Authentication successful: New tokens retrieved.")
      return cst, x_security_token
    else:
      print(f"Login failed: {response.status_code} - {response.text}")
      return None, None
  except Exception as e:
    print(f"Exception during login: {str(e)}")
    return None, None


@app.route("/webhook", methods=["POST"])
def webhook():
  try:
    data = request.get_json(force=True)
    print(f"Received TradingView Alert: {data}")

    ticker = data.get("ticker")
    action = data.get("action", "").upper()
    contracts = float(data.get("contracts", 0.1))

    # تسجيل الدخول وجلب رموز الجلسة الجديدة لكل طلب لتجنب انتهاء الصلاحية
    cst, x_security_token = capital_login()
    if not cst or not x_security_token:
      return (
          jsonify({
              "status": "error",
              "message": "Authentication Error with Capital.com",
          }),
          401,
      )

    # إعداد ترويسة التنفيذ مع رموز الجلسة المحدثة
    headers = {
        "X-CAP-API-KEY": CAPITAL_API_KEY,
        "CST": cst,
        "X-SECURITY-TOKEN": x_security_token,
        "Content-Type": "application/json",
        "User-Agent": HEADERS_BROWSER["User-Agent"],
    }

    # تجهيز أمر الصفقة
    order_payload = {
        "epic": ticker,
        "direction": (
            "BUY" if action == "BUY" or action == "LONG" else "SELL"
        ),
        "size": contracts,
        "guaranteedStop": False,
        "orderType": "MARKET",
    }

    order_url = f"{BASE_URL}/positions"
    response = requests.post(
        order_url, json=order_payload, headers=headers, timeout=10
    )

    if response.status_code in [200, 201]:
      print(f"Order placed successfully: {response.json()}")
      return jsonify({"status": "success", "response": response.json()}), 200
    else:
      print(f"Failed to place order: {response.text}")
      return jsonify({"status": "error", "message": response.text}), 400

  except Exception as e:
    print(f"Server Error: {str(e)}")
    return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
