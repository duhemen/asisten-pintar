---

## 📝 README.md untuk Asisten Pintar

```markdown
<div align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.11-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/AI-Ollama-orange" alt="AI">
  <img src="https://img.shields.io/badge/OCR-PaddleOCR%20%7C%20Tesseract-brightgreen" alt="OCR">
</div>

<br>

<div align="center">
  <h1>🏛️ Asisten Pintar</h1>
  <p><strong>AI-Powered Secretary Assistant for Government Offices</strong></p>
  <p><em>Asisten Sekretaris Cerdas Berbasis AI untuk Instansi Pemerintah</em></p>
  <br>
  <p>
    <a href="#-fitur-unggulan">Fitur</a> •
    <a href="#-demo-aplikasi">Demo</a> •
    <a href="#-teknologi">Teknologi</a> •
    <a href="#-instalasi">Instalasi</a> •
    <a href="#-panduan-penggunaan">Panduan</a> •
    <a href="#-kontribusi">Kontribusi</a>
  </p>
</div>

---

## 📖 Tentang Aplikasi

**Asisten Pintar** adalah aplikasi desktop berbasis AI yang dirancang khusus untuk membantu Sekretaris di instansi pemerintah dalam mengelola administrasi perkantoran secara **offline** dan **aman**. Aplikasi ini berjalan 100% di lokal tanpa memerlukan koneksi internet, sehingga data sensitif tetap terjaga kerahasiaannya.

### 🎯 Tujuan

- Membantu sekretaris dalam **menyusun notulensi rapat** secara otomatis
- Memberikan **rekomendasi disposisi surat** masuk dengan analisis AI
- Memvalidasi format surat sesuai **Tata Naskah Dinas (TND)**
- Mengelola **arsip digital** dengan standar ANRI
- Menyediakan **dashboard** untuk memonitor kinerja

---

## ✨ Fitur Unggulan

| Fitur | Deskripsi | Status |
|-------|-----------|--------|
| 📝 **Notulensi Rapat** | Upload dokumen rapat (PDF/Word/Gambar) → Notulensi otomatis dengan AI | ✅ |
| 📨 **Disposisi Surat** | Analisis surat masuk → Rekomendasi tujuan disposisi & urgensi | ✅ |
| 📋 **TND Validator** | Validasi format surat sesuai Peraturan Tata Naskah Dinas | ✅ |
| 📂 **Arsip Digital** | Manajemen arsip dengan klasifikasi Aktif/Inaktif/Statis | ✅ |
| 📊 **Dashboard** | Statistik & monitoring kinerja sekretaris | ✅ |
| 👁️ **Vision AI** | OCR cerdas untuk dokumen scan dan gambar | ✅ |
| 🎙️ **Transkripsi Audio** | Konversi rekaman rapat ke teks (Faster-Whisper) | ✅ |

---

## 🖥️ Demo Aplikasi

### Dashboard
![Dashboard](https://via.placeholder.com/800x400/2d3748/ffffff?text=Dashboard+Pimpinan)

### Notulensi Rapat
![Notulensi](https://via.placeholder.com/800x400/2d3748/ffffff?text=Notulensi+Rapat)

### Disposisi Surat
![Disposisi](https://via.placeholder.com/800x400/2d3748/ffffff?text=Disposisi+Surat)

---

## 🛠️ Teknologi

### Backend
| Teknologi | Fungsi |
|-----------|--------|
| ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white) | REST API Server |
| ![Ollama](https://img.shields.io/badge/Ollama-000000?style=flat&logo=ollama&logoColor=white) | Local LLM (Qwen2.5 14B) |
| ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white) | Database |
| ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2C2255?style=flat&logo=sqlalchemy&logoColor=white) | ORM |
| ![PaddleOCR](https://img.shields.io/badge/PaddleOCR-0052CC?style=flat&logo=paddlepaddle&logoColor=white) | OCR Engine |
| ![Tesseract](https://img.shields.io/badge/Tesseract-00B4D8?style=flat&logo=tesseract&logoColor=white) | OCR Fallback |
| ![Faster-Whisper](https://img.shields.io/badge/Faster--Whisper-FF6B6B?style=flat&logo=openai&logoColor=white) | Audio Transcription |

### Frontend
| Teknologi | Fungsi |
|-----------|--------|
| ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white) | UI Framework |
| ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) | Programming Language |

### AI Models
| Model | Ukuran | Fungsi |
|-------|--------|--------|
| Qwen2.5 14B Instruct | 9 GB | Text generation (Notulensi & Disposisi) |
| Qwen2-VL 2B | 2.3 GB | Vision AI (OCR gambar/PDF scan) |

---

## 📋 Prasyarat

| Komponen | Minimum | Rekomendasi |
|----------|---------|-------------|
| **OS** | Windows 10/11 | Windows 10/11 Pro |
| **RAM** | 16 GB | 32 GB |
| **VRAM (GPU)** | 6 GB | 8 GB+ (NVIDIA RTX) |
| **Storage** | 30 GB | 50 GB+ |
| **Python** | 3.10 - 3.11 | 3.11 |
| **PostgreSQL** | 14+ | 15+ |

---

## 🚀 Instalasi Cepat

### 1. Clone Repository

```bash
git clone https://github.com/duhemen/asisten-pintar.git
cd asisten-pintar
```

### 2. Setup Virtual Environment

```bash
# Windows
python -m venv env_asisten
env_asisten\Scripts\activate

# Mac/Linux
python3 -m venv env_asisten
source env_asisten/bin/activate
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Install Ollama & Pull Models

```bash
# Download Ollama: https://ollama.com/download/windows

# Pull Text Model (9GB)
ollama pull qwen2.5:14b-instruct-q4_K_M

# Pull Vision Model (2.3GB)
ollama pull hf.co/bartowski/Qwen2-VL-2B-Instruct-GGUF:Q4_K_M
```

### 5. Setup Database

```bash
# Install PostgreSQL: https://www.postgresql.org/download/
# Buat database:
psql -U postgres
CREATE DATABASE asisten_pintar;
\q

# Inisialisasi tabel
python create_tables.py
```

### 6. Konfigurasi Environment

```bash
# Copy .env.example ke .env
cp .env.example .env

# Edit .env dengan konfigurasi kamu
```

### 7. Jalankan Aplikasi

```bash
# Terminal 1 - Ollama
ollama serve

# Terminal 2 - Backend
uvicorn app.main:app --reload --port 8000

# Terminal 3 - Frontend
streamlit run ../frontend/app.py
```

### 8. Akses Aplikasi

Buka browser: **http://localhost:8501**

---

## 📱 Panduan Penggunaan

### 📝 Notulensi Rapat

1. Pilih menu **"Notulensi Rapat"**
2. Upload dokumen rapat (PDF/Word/Gambar)
3. Pilih mode pemrosesan (Auto/Vision AI/OCR)
4. Klik **"Proses Notulensi"**
5. Notulensi AI akan muncul dalam hitungan detik
6. Download hasil dalam format TXT

### 📨 Disposisi Surat

1. Pilih menu **"Disposisi Surat"**
2. Upload surat masuk
3. Sistem akan mengekstrak teks dan menganalisis
4. Dapatkan rekomendasi:
   - Ringkasan surat
   - Kategori (Keuangan/Kepegawaian/Infrastruktur/Protokoler/Umum)
   - Tujuan disposisi
   - Tingkat urgensi (Biasa/Penting/Segera)

### 📋 TND Validator

1. Pilih menu **"TND Validator"**
2. Upload dokumen surat (DOCX/PDF/TXT)
3. Sistem akan memeriksa:
   - Format nomor surat
   - Jenis font (Arial/Times New Roman 12pt)
   - Keberadaan kop surat
   - Tanda tangan
   - Struktur surat

### 📂 Arsip Digital

1. Pilih menu **"Arsip Digital"**
2. Kelola arsip dengan klasifikasi (Aktif/Inaktif/Statis)
3. Cari arsip berdasarkan kata kunci, tanggal, atau nomor surat
4. Lihat riwayat akses dokumen

---

## 📁 Struktur Proyek

```text
asisten-pintar/
├── backend/
│   ├── app/
│   │   ├── core/              # AI & OCR Engine
│   │   │   ├── document_engine.py
│   │   │   ├── llm_analyzer.py
│   │   │   ├── llm_engine.py
│   │   │   ├── ocr_engine.py
│   │   │   ├── prompts.py
│   │   │   └── whisper_engine.py
│   │   ├── modules/           # Modul Fitur
│   │   │   └── tnd_validator/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── storage/               # Penyimpanan file
│   ├── temp/                  # File temporary
│   ├── .env.example           # Contoh konfigurasi
│   ├── create_tables.py       # Inisialisasi database
│   └── requirements.txt
├── frontend/
│   └── app.py                 # Streamlit UI
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🔧 Troubleshooting

### PaddleOCR Gagal Dimuat

```bash
pip uninstall paddleocr paddlepaddle
pip install paddleocr==2.6.1.3 paddlepaddle==2.5.2
```

### Ollama Connection Error

```bash
# Jalankan Ollama
ollama serve

# Atau restart
taskkill /F /IM ollama.exe
ollama serve
```

### Database Connection Error

```bash
# Pastikan PostgreSQL berjalan
services.msc
# Cari "postgresql" → Start

# Cek koneksi
psql -U postgres -d asisten_pintar
```

---

## 🤝 Kontribusi

Kami sangat terbuka untuk kontribusi! 

1. Fork repository
2. Buat branch fitur (`git checkout -b feature/AmazingFeature`)
3. Commit perubahan (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📝 Lisensi

Distributed under the MIT License. See `LICENSE` for more information.

---

## 👨‍💻 Tim Pengembang

| Nama | Peran |
|------|-------|
| **Muhammad Haramein** | Lead Developer & AI Engineer |

---

## 🙏 Terima Kasih

- **Ollama** - Local LLM Platform
- **PaddlePaddle** - OCR Framework
- **FastAPI** - Web Framework
- **Streamlit** - UI Framework
- **PostgreSQL** - Database

---

## 📞 Kontak

- **GitHub**: [duhemen](https://github.com/duhemen)

---

<div align="center">
  <p>Made with ❤️ by <strong>duhemen</strong></p>
  <p>
    <a href="https://github.com/duhemen/asisten-pintar/issues">Report Bug</a> •
    <a href="https://github.com/duhemen/asisten-pintar/issues">Request Feature</a>
  </p>
</div>
```

---

## 📝 Cara Menambahkan README ke GitHub

```bash
# 1. Buat file README.md di root proyek
# 2. Copy paste kode di atas
# 3. Simpan

# 4. Add dan commit
git add README.md
git commit -m "docs: add professional README.md"

# 5. Push ke GitHub
git push
```

---
