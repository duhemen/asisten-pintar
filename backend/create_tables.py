# backend/create_tables.py
import sys
import os

# Tambahkan path agar bisa import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, engine
from app import models  # Import models agar terdaftar

if __name__ == "__main__":
    print("🔄 Membuat tabel database...")
    try:
        init_db()
        print("✅ Tabel berhasil dibuat!")
    except Exception as e:
        print(f"❌ Error: {e}")