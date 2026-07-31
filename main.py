import requests
import time
import datetime
import json
import os
from docxtpl import DocxTemplate
from docx2pdf import convert

# ==========================================
# تنظیمات اولیه
# ==========================================
TOKEN = "1409908229:7zQYMlRMIqSixuQkt_QIFPgGcOjpAvW-u50"
SUPPORT_USER_ID = 1411467910

BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

# ✅ مسیر مطلق فایل قالب (حل مشکل Package not found)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FILE = os.path.join(BASE_DIR, "template.docx")

last_update_id = 0

# مدیریت وضعیت (State) و داده‌های موقت کاربران
user_states = {}
user_data = {}

# تعریف ثابت‌های وضعیت (States)
STATE_CASE_TYPE = "CASE_TYPE"
STATE_CASE_NUM = "CASE_NUM"
STATE_CLASS_NUM = "CLASS_NUM"
STATE_COURT = "COURT"
STATE_P_NAME = "P_NAME"
STATE_P_NID = "P_NID"
STATE_D_NAME = "D_NAME"
STATE_D_NID = "D_NID"
STATE_BIO = "BIO"
STATE_COURT_REQ = "COURT_REQ"
STATE_EXPERT_OP = "EXPERT_OP"
STATE_REVIEW = "REVIEW"

# ==========================================
# توابع کمکی API بله
# ==========================================
def send_message(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    return requests.post(url, json=data).json()

def edit_message_text(chat_id, message_id, text, reply_markup=None):
    url = f"{BASE_URL}/editMessageText"
    data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    return requests.post(url, json=data).json()

def answer_callback(callback_query_id, text=None):
    url = f"{BASE_URL}/answerCallbackQuery"
    data = {"callback_query_id": callback_query_id}
    if text:
        data["text"] = text
    requests.post(url, json=data)

def send_document(chat_id, file_path, caption):
    url = f"{BASE_URL}/sendDocument"
    with open(file_path, 'rb') as f:
        files = {'document': f}
        data = {"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"}
        return requests.post(url, data=data, files=files).json()

# ==========================================
# مدیریت داده‌ها و وضعیت (کلید شیشه‌ای)
# ==========================================
def set_state(chat_id, state):
    user_states[chat_id] = state

def get_state(chat_id):
    return user_states.get(chat_id, STATE_CASE_TYPE)

def save_data(chat_id, key, value):
    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id][key] = value

def get_data(chat_id):
    return user_data.get(chat_id, {})

def build_review_text(data):
    """ساخت متن خلاصه برای نمایش یا ویرایش"""
    return (
        "📋 *خلاصه اطلاعات پرونده (حالت شیشه‌ای)*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f" نوع پرونده: {data.get('case_type', 'ثبت نشده')}\n"
        f"🔸 شماره پرونده: {data.get('case_num', 'ثبت نشده')}\n"
        f"🔸 کلاسه بایگانی: {data.get('class_num', 'ثبت نشده')}\n"
        f"🔸 دادگاه: {data.get('court', 'ثبت نشده')}\n"
        f"🔸 خواهان: {data.get('p_name', 'ثبت نشده')} (کدملی: {data.get('p_nid', 'ثبت نشده')})\n"
        f"🔸 خوانده: {data.get('d_name', 'ثبت نشده')} (کدملی: {data.get('d_nid', 'ثبت نشده')})\n"
        f"🔸 بیوگرافی: {data.get('bio', 'ثبت نشده')}\n"
        f"🔸 دستور دادگاه: {data.get('court_req', 'ثبت نشده')}\n"
        f"🔸 نظر کارشناس: {data.get('expert_op', 'ثبت نشده')}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "برای ویرایش هر بخش روی دکمه آن کلیک کنید. در صورت تایید، 'ثبت نهایی' را بزنید."
    )

# ==========================================
# ساخت کیبوردها
# ==========================================
def get_case_type_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "مطالبه نفقه", "callback_data": "type_nafaqah"}],
            [{"text": "اجرت‌المثل ایام زوجیت", "callback_data": "type_ojrat"}],
            [{"text": "تعیین جهیزیه", "callback_data": "type_jahizieh"}],
            [{"text": "سایر موارد", "callback_data": "type_other"}]
        ]
    }

def get_review_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "✏️ ویرایش نوع پرونده", "callback_data": "edit_type"}],
            [{"text": "✏️ ویرایش شماره/کلاسه/دادگاه", "callback_data": "edit_case_info"}],
            [{"text": "✏️ ویرایش خواهان", "callback_data": "edit_plaintiff"}],
            [{"text": "✏️ ویرایش خوانده", "callback_data": "edit_defendant"}],
            [{"text": "✏️ ویرایش بیوگرافی", "callback_data": "edit_bio"}],
            [{"text": "✏️ ویرایش خواسته دادگاه", "callback_data": "edit_court_req"}],
            [{"text": "️ ویرایش نظر کارشناس", "callback_data": "edit_expert_op"}],
            [{"text": "✅ ثبت نهایی و دریافت فایل Word/PDF", "callback_data": "finalize_report"}]
        ]
    }

# ==========================================
# منطق تولید فایل Word و PDF
# ==========================================
def generate_and_send_files(chat_id, data):
    send_message(chat_id, "⏳ در حال تنظیم نظریه و تولید فایل‌ها...")
    
    # ✅ بررسی وجود فایل قالب
    if not os.path.exists(TEMPLATE_FILE):
        error_msg = (
            f"❌ فایل قالب پیدا نشد!\n\n"
            f"ربات دقیقاً در این مسیر به دنبال فایل می‌گردد:\n"
            f"`{TEMPLATE_FILE}`\n\n"
            f"لطفاً فایل template.docx را دقیقاً در همین مسیر کپی کنید."
        )
        send_message(chat_id, error_msg)
        print(error_msg)
        return
    
    try:
        # 1. بارگذاری قالب
        tpl = DocxTemplate(TEMPLATE_FILE)
        
        # 2. نگاشت داده‌ها به متغیرهای قالب
        context = {
            "court": data.get('court', 'ثبت نشده'),
            "class_num": data.get('class_num', 'ثبت نشده'),
            "p_name": data.get('p_name', 'ثبت نشده'),
            "d_name": data.get('d_name', 'ثبت نشده'),
            "case_type": data.get('case_type', 'ثبت نشده'),
            "bio_text": data.get('bio', 'ثبت نشده'),
            "court_req": data.get('court_req', 'ثبت نشده'),
            "final_opinion": data.get('expert_op', 'ثبت نشده')
        }
        
        # 3. رندر و ذخیره ورد
        tpl.render(context)
        safe_class = str(data.get('class_num', '000')).replace('/', '_').replace(' ', '_')
        word_filename = f"نظریه_کارشناسی_{safe_class}.docx"
        pdf_filename = f"نظریه_کارشناسی_{safe_class}.pdf"
        
        tpl.save(word_filename)
        
        # 4. تبدیل به PDF
        convert(word_filename, pdf_filename)
        
        # 5. ارسال فایل‌ها در بله
        send_document(chat_id, word_filename, "📄 فایل Word نظریه کارشناسی")
        send_document(chat_id, pdf_filename, "📑 فایل PDF نظریه کارشناسی")
        
        send_message(chat_id, "✅ نظریه با موفقیت ثبت و فایل‌ها ارسال شدند.\nبرای شروع جدید /start را بزنید.")
        
        # پاکسازی حافظه و فایل‌های موقت
        if chat_id in user_states: del user_states[chat_id]
        if chat_id in user_data: del user_data[chat_id]
        if os.path.exists(word_filename): os.remove(word_filename)
        if os.path.exists(pdf_filename): os.remove(pdf_filename)
        
    except Exception as e:
        send_message(chat_id, f"❌ خطا در تولید فایل: {str(e)}\nلطفاً بررسی کنید فایل {TEMPLATE_FILE} در پوشه ربات موجود باشد و نرم‌افزار Word نصب باشد.")

# ==========================================
# پردازش پیام‌ها و دکمه‌ها
# ==========================================
def handle_callback(callback_query):
    data = callback_query["data"]
    chat_id = callback_query["message"]["chat"]["id"]
    message_id = callback_query["message"]["message_id"]
    callback_id = callback_query["id"]
    
    answer_callback(callback_id)

    # مدیریت دکمه‌های ویرایش در حالت بازبینی (کلید شیشه‌ای)
    if data == "edit_type":
        set_state(chat_id, STATE_CASE_TYPE)
        edit_message_text(chat_id, message_id, "لطفاً نوع پرونده را انتخاب کنید:", reply_markup=get_case_type_keyboard())
    elif data == "edit_case_info":
        set_state(chat_id, STATE_CASE_NUM)
        edit_message_text(chat_id, message_id, "لطفاً *شماره پرونده* را وارد کنید:")
    elif data == "edit_plaintiff":
        set_state(chat_id, STATE_P_NAME)
        edit_message_text(chat_id, message_id, "لطفاً *نام و نام خانوادگی خواهان* را وارد کنید:")
    elif data == "edit_defendant":
        set_state(chat_id, STATE_D_NAME)
        edit_message_text(chat_id, message_id, "لطفاً *نام و نام خانوادگی خوانده* را وارد کنید:")
    elif data == "edit_bio":
        set_state(chat_id, STATE_BIO)
        edit_message_text(chat_id, message_id, "لطفاً *بیوگرافی و شرح حال* را وارد کنید:")
    elif data == "edit_court_req":
        set_state(chat_id, STATE_COURT_REQ)
        edit_message_text(chat_id, message_id, "لطفاً *خواسته و دستور مقام قضایی* را وارد کنید:")
    elif data == "edit_expert_op":
        set_state(chat_id, STATE_EXPERT_OP)
        edit_message_text(chat_id, message_id, "لطفاً *نظریه نهایی کارشناسی* را وارد کنید:")
    elif data == "show_review":
        review_text = build_review_text(get_data(chat_id))
        edit_message_text(chat_id, message_id, review_text, reply_markup=get_review_keyboard())
    elif data == "finalize_report":
        generate_and_send_files(chat_id, get_data(chat_id))
    elif data.startswith("type_"):
        type_names = {
            "type_nafaqah": "مطالبه نفقه",
            "type_ojrat": "اجرت‌المثل ایام زوجیت",
            "type_jahizieh": "تعیین جهیزیه",
            "type_other": "سایر موارد"
        }
        save_data(chat_id, "case_type", type_names.get(data, data))
        set_state(chat_id, STATE_CASE_NUM)
        edit_message_text(chat_id, message_id, f"✅ نوع پرونده ثبت شد.\n\n🔹 لطفاً *شماره پرونده* را وارد کنید:")

def handle_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()
    from_user = message.get("from", {})
    user_name = from_user.get("first_name", "کاربر")
    user_id = from_user.get("id")

    current_state = get_state(chat_id)
    print(f"[DEBUG] User {user_id} in state '{current_state}' sent: '{text}'")

    if text == "/start":
        set_state(chat_id, STATE_CASE_TYPE)
        if chat_id in user_data: del user_data[chat_id]
        send_message(chat_id, f"سلام {user_name} عزیز، به ربات ثبت نظریه کارشناسی خوش آمدید.\n\nلطفاً نوع پرونده را انتخاب کنید:", reply_markup=get_case_type_keyboard())
        return

    # ماشین حالت (State Machine) برای دریافت اطلاعات
    if current_state == STATE_CASE_NUM:
        save_data(chat_id, "case_num", text)
        set_state(chat_id, STATE_CLASS_NUM)
        send_message(chat_id, "🔹 لطفاً *شماره کلاسه بایگانی* را وارد کنید:")
        
    elif current_state == STATE_CLASS_NUM:
        save_data(chat_id, "class_num", text)
        set_state(chat_id, STATE_COURT)
        send_message(chat_id, " لطفاً *نام دادگاه رسیدگی کننده* را وارد کنید:")
        
    elif current_state == STATE_COURT:
        save_data(chat_id, "court", text)
        set_state(chat_id, STATE_P_NAME)
        send_message(chat_id, " *مشخصات خواهان*\n\n نام و نام خانوادگی خواهان را وارد کنید:")
        
    elif current_state == STATE_P_NAME:
        save_data(chat_id, "p_name", text)
        set_state(chat_id, STATE_P_NID)
        send_message(chat_id, " کد ملی خواهان را وارد کنید:")
        
    elif current_state == STATE_P_NID:
        save_data(chat_id, "p_nid", text)
        set_state(chat_id, STATE_D_NAME)
        send_message(chat_id, "👤 *مشخصات خوانده*\n\n🔹 نام و نام خانوادگی خوانده را وارد کنید:")
        
    elif current_state == STATE_D_NAME:
        save_data(chat_id, "d_name", text)
        set_state(chat_id, STATE_D_NID)
        send_message(chat_id, "🔹 کد ملی خوانده را وارد کنید:")
        
    elif current_state == STATE_D_NID:
        save_data(chat_id, "d_nid", text)
        set_state(chat_id, STATE_BIO)
        send_message(chat_id, "📖 لطفاً *بیوگرافی و شرح حال مختصر* طرفین را وارد کنید:")
        
    elif current_state == STATE_BIO:
        save_data(chat_id, "bio", text)
        set_state(chat_id, STATE_COURT_REQ)
        send_message(chat_id, "️ لطفاً *خواسته و دستور مقام قضایی* را وارد کنید:")
        
    elif current_state == STATE_COURT_REQ:
        save_data(chat_id, "court_req", text)
        set_state(chat_id, STATE_EXPERT_OP)
        send_message(chat_id, "📝 و در نهایت، لطفاً *نظریه نهایی کارشناسی* خود را وارد کنید:")
        
    elif current_state == STATE_EXPERT_OP:
        save_data(chat_id, "expert_op", text)
        set_state(chat_id, STATE_REVIEW)
        review_text = build_review_text(get_data(chat_id))
        send_message(chat_id, review_text, reply_markup=get_review_keyboard())
        
    else:
        send_message(chat_id, "برای شروع فرآیند ثبت نظریه، دستور /start را ارسال کنید.")

def get_updates():
    global last_update_id
    url = f"{BASE_URL}/getUpdates"
    params = {"offset": last_update_id + 1, "timeout": 30}
    try:
        response = requests.get(url, params=params, timeout=35)
        updates = response.json()
        if updates.get("ok"):
            for update in updates.get("result", []):
                last_update_id = update["update_id"]
                if "message" in update:
                    handle_message(update["message"])
                elif "callback_query" in update:
                    handle_callback(update["callback_query"])
    except Exception as e:
        print(f"Error in get_updates: {e}")
        time.sleep(1)

def main():
    print("🤖 ربات در حال راه‌اندازی...")
    url = f"{BASE_URL}/getMe"
    response = requests.get(url)
    result = response.json()
    if result.get("ok"):
        bot_name = result["result"].get("first_name", "ربات")
        print(f"✅ ربات آماده است: {bot_name}")
    else:
        print(f"❌ خطا در اتصال: {result}")
        return

    print("در حال گوش دادن به پیام‌ها... (برای توقف Ctrl+C را بزنید)")
    while True:
        get_updates()

if __name__ == "__main__":
    main()