from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# جلب المفتاح وكلمة المرور من إعدادات الأمان في Render
API_KEY = os.getenv("CAPITAL_API_KEY", "RDOj635EeNudIXcx")
API_PASSWORD = os.getenv("CAPITAL_PASSWORD", "Bot11987@")

@app.route('/', methods=['GET'])
def home():
    return "Capital Trading Bot is Active and Ready!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # استقبال البيانات من ترند فيو
        data = request.json
        
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400

        action = data.get("action")      # نوع الأمر: BUY أو SELL
        ticker = data.get("ticker")      # اسم الأصول
        price = data.get("price")        # السعر الحالي
        
        print(f"تم استلام إشارة: {action} للأصل {ticker} بسعر {price}")
        
        return jsonify({"status": "success", "message": "Order processed successfully"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
