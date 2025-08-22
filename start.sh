#!/bin/bash

echo "🚀 Starting BTK Project Backend..."

# Migration'ı çalıştır
echo "📦 Running database migration..."
python migrate_db.py

# Gunicorn'u başlat
echo "🌐 Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 300 --keep-alive 5 --max-requests 1000 --max-requests-jitter 100 app:app