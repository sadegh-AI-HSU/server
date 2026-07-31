FROM python:3.9-slim

# نصب LibreOffice برای تبدیل Word به PDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    fonts-noto \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# کپی و نصب وابستگی‌ها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی صریح تمام فایل‌های پروژه
COPY template.docx /app/template.docx
COPY main.py /app/main.py

# تنظیم permissions برای همه فایل‌ها
RUN chmod 644 /app/template.docx && \
    chmod 755 /app/main.py

# نمایش فایل‌های موجود برای دیباگ (در Build Log دیده می‌شود)
RUN ls -la /app/

# ایجاد کاربر غیر root برای امنیت
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# دستور اجرای ربات
CMD ["python3", "main.py"]
