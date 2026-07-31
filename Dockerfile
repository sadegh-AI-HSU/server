# 1. استفاده از ایمیج رسمی و سبک پایتون (Debian slim)
# نکته: از Alpine استفاده نمی‌کنیم چون نصب LibreOffice روی Alpine به دلیل تفاوت کتابخانه‌ها بسیار پیچیده و ناپایدار است.
FROM python:3.9-slim

# 2. نصب پیش‌نیازهای سیستم (LibreOffice برای تبدیل PDF)
# نکته مقاله: دستورات update و install باید در یک خط باشند تا کش داکر خراب نشود.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

# 3. تنظیم پوشه کار (طبق استاندارد مقاله برای پایتون)
WORKDIR /app

# 4. کپی فایل وابستگی‌ها و نصب آن‌ها (قبل از کپی کل کد، برای استفاده از کش داکر)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. کپی تمام فایل‌های پروژه به داخل کانتینر
COPY . .

# 6. ایجاد یک کاربر غیر root برای امنیت بیشتر (طبق توصیه مقاله)
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# 7. دستور اجرای برنامه (لاگ‌ها به صورت خودکار به stdout می‌روند که استاندارد داکر است)
CMD ["python3", "main.py"]