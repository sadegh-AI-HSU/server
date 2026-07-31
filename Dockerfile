FROM python:3.9-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# کپی تک‌تک فایل‌ها به صورت صریح
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY template.docx ./template.docx
COPY main.py ./main.py

# تنظیم permissions
RUN chmod 644 ./template.docx

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python3", "main.py"]
