FROM python:3.9-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی صریح فایل template.docx
COPY template.docx /app/template.docx

# کپی بقیه فایل‌ها
COPY . .

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python3", "main.py"]
