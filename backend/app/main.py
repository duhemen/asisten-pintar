# backend/app/main.py
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil
import logging
from datetime import datetime
from typing import Optional

# Import konfigurasi dan core
from app.config import settings
from app.core.llm_analyzer import LocalLLMAnalyzer
from app.core.whisper_engine import LocalWhisperEngine
from app.core.llm_engine import local_llm
from app.core.prompts import PROMPT_NOTULENSI_RAPAT
from app.core.document_engine import local_doc_engine
from app.core.ocr_engine import ocr_processor

from app.modules.tnd_validator.router import router as tnd_router

from app.database import get_db, save_dokumen
from sqlalchemy.orm import Session
from fastapi import Depends

from app.database import log_akses
from fastapi import Request
import time

from app.database import save_arsip, search_arsip, get_riwayat_arsip
from app.database import get_dashboard_stats, get_all_dokumen
from sqlalchemy.orm import Session 

# ==================== SETUP LOGGING ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== INISIALISASI APP ====================
app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API Asisten Pintar untuk Sekretaris Instansi Pemerintah (Lokal) dengan OCR & Vision AI",
    version="2.0.0"
)
app.include_router(tnd_router)

# ==================== CORS ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== SCHEMA ====================
class SuratInput(BaseModel):
    teks: str

class DisposisiInput(BaseModel):
    teks_surat: str


# ==================== MIDDLEWARE LOGGING ====================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Catat semua request ke database"""
    start_time = time.time()
    
    # Proses request
    response = await call_next(request)
    
    # Log hanya untuk endpoint tertentu
    if "api" in request.url.path:
        try:
            # Ambil user dari header (nanti bisa pakai auth)
            user = request.headers.get("x-user", "anonymous")
            ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "")
            
            # Simpan ke database (async, tidak blocking)
            # Catatan: Ini async, kita jalankan di background
            import asyncio
            asyncio.create_task(
                log_activity(
                    user=user,
                    aksi=f"{request.method} {request.url.path}",
                    ip_address=ip,
                    user_agent=user_agent,
                    status_code=response.status_code
                )
            )
        except Exception as e:
            logger.warning(f"Gagal log aktivitas: {e}")
    
    response.headers["X-Process-Time"] = str(time.time() - start_time)
    return response

# Fungsi untuk log aktivitas (async)
async def log_activity(user: str, aksi: str, ip_address: str, user_agent: str, status_code: int):
    """Log aktivitas ke database"""
    try:
        from app.database import SessionLocal
        from app.models import RiwayatAkses
        
        db = SessionLocal()
        riwayat = RiwayatAkses(
            arsip_id=None,  # Untuk aktivitas umum
            user=user,
            aksi=f"{aksi} [{status_code}]",
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(riwayat)
        db.commit()
        db.close()
    except Exception as e:
        logger.error(f"Gagal log aktivitas: {e}")


# ==================== ENDPOINT DASAR ====================
@app.get("/")
def read_root():
    return {
        "status": "Online",
        "app_name": settings.APP_NAME,
        "version": "2.0.0",
        "message": "Selamat datang di Backend Asisten Pintar Lokal dengan OCR & Vision AI!"
    }

# ==================== ENDPOINT DISPOSISI ====================
@app.get("/api/disposisi/info")
async def disposisi_info():
    """Info tentang fitur disposisi"""
    return {
        "status": "ready",
        "model": settings.OLLAMA_MODEL,
        "features": [
            "Ekstraksi teks dari dokumen",
            "Klasifikasi kategori surat",
            "Rekomendasi tujuan disposisi",
            "Tingkat urgensi"
        ]
    }

@app.post("/api/disposisi/analisis")
async def analisis_disposisi(input_data: DisposisiInput):
    """
    Analisis teks surat dan berikan rekomendasi disposisi
    """
    try:
        if not input_data.teks_surat or len(input_data.teks_surat.strip()) < 50:
            return {
                "status": "error",
                "message": "Teks surat terlalu pendek (minimal 50 karakter)",
                "ringkasan": "",
                "kategori": "",
                "rekomendasi_tujuan": "",
                "urgensi": ""
            }
        
        analyzer = LocalLLMAnalyzer()
        hasil = await analyzer.analyze_disposisi(input_data.teks_surat)
        
        # Tambahkan metadata
        hasil["status"] = "success"
        hasil["timestamp"] = datetime.now().isoformat()
        hasil["panjang_teks"] = len(input_data.teks_surat)
        
        return hasil
        
    except Exception as e:
        logger.error(f"Error disposisi: {e}")
        raise HTTPException(status_code=500, detail=f"Gagal menganalisis disposisi: {str(e)}")

@app.post("/api/disposisi/dokumen")
async def disposisi_dari_dokumen(file: UploadFile = File(...)):
    """
    Upload dokumen surat, ekstrak teks, lalu analisis disposisi
    """
    try:
        # Validasi format
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.docx', '.txt']
        ext = os.path.splitext(file.filename)[1].lower()
        
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Format tidak didukung. Gunakan: {', '.join(allowed_extensions)}"
            )
        
        # 1. Simpan file sementara
        os.makedirs("temp_disposisi", exist_ok=True)
        file_path = os.path.join("temp_disposisi", file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. Ekstrak teks
        use_vision = ext in ['.jpg', '.jpeg', '.png']
        result = local_doc_engine.extract_text(file_path, file.filename, use_vision=use_vision)
        teks = result.get('text', '')
        metode = result.get('method', 'unknown')
        
        # 3. Bersihkan file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # 4. Validasi teks
        if not teks or len(teks.strip()) < 50:
            return {
                "status": "error",
                "message": "Teks surat terlalu pendek atau tidak terbaca. Pastikan dokumen memiliki teks yang jelas.",
                "teks_ekstraksi": teks or "",
                "ringkasan": "",
                "kategori": "",
                "rekomendasi_tujuan": "",
                "urgensi": "",
                "metode_ekstraksi": metode
            }
        
        # 5. Analisis disposisi
        analyzer = LocalLLMAnalyzer()
        disposisi = await analyzer.analyze_disposisi(teks)
        
        # 6. Gabungkan hasil
        return {
            "status": "success",
            "filename": file.filename,
            "teks_ekstraksi": teks,
            "metode_ekstraksi": metode,
            "ringkasan": disposisi.get('ringkasan', ''),
            "kategori": disposisi.get('kategori', 'Tidak terdeteksi'),
            "rekomendasi_tujuan": disposisi.get('rekomendasi_tujuan', 'Tidak terdeteksi'),
            "urgensi": disposisi.get('urgensi', 'Biasa'),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disposisi dokumen: {e}")
        raise HTTPException(status_code=500, detail=f"Gagal memproses dokumen: {str(e)}")

# ==================== ENDPOINT HEALTH CHECK ====================
@app.get("/api/health/ai")
def check_ai_status():
    """Cek status koneksi ke Ollama"""
    return {
        "configured_model": settings.OLLAMA_MODEL,
        "vision_model": local_llm.vision_model,
        "ollama_url": settings.OLLAMA_BASE_URL,
        "status": "Ready"
    }

@app.get("/api/health/ocr")
def check_ocr_status():
    """Cek status OCR dan Vision AI"""
    status = {
        "paddleocr_available": ocr_processor.ocr is not None,
        "tesseract_available": ocr_processor.tesseract_available,
        "vision_model": local_llm.vision_model,
        "status": "Ready"
    }
    
    # Cek tesseract version
    if ocr_processor.tesseract_available:
        try:
            import pytesseract
            status["tesseract_version"] = str(pytesseract.get_tesseract_version())
        except:
            status["tesseract_version"] = "Unknown"
    
    return status

@app.get("/api/health/vision")
def check_vision_status():
    """Cek status Vision AI (Qwen2-VL)"""
    return {
        "vision_model": local_llm.vision_model,
        "text_model": local_llm.model,
        "status": "Ready"
    }

# ==================== ENDPOINT TEST ====================
@app.post("/api/test/analisis-surat")
async def test_analisis(input_data: SuratInput):
    """Test analisis disposisi surat"""
    analyzer = LocalLLMAnalyzer()
    hasil = await analyzer.analyze_disposisi(input_data.teks)
    return hasil

# Inisialisasi engine Whisper
whisper_engine = LocalWhisperEngine()

@app.post("/api/test/transkrip-audio")
async def test_transkrip(file: UploadFile = File(...)):
    """Test transkripsi audio"""
    temp_dir = os.path.join("storage", "audio_rapat")
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    hasil_teks = whisper_engine.transcribe_audio(file_path)
    
    # Bersihkan file
    if os.path.exists(file_path):
        os.remove(file_path)
    
    return {
        "filename": file.filename,
        "transkrip": hasil_teks
    }

# ==================== ENDPOINT UTAMA DOKUMEN ====================
@app.post("/api/asisten/notulensi-dokumen")
async def buat_notulensi_dari_dokumen(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Endpoint Utama: Auto-detect dokumen dan pilih metode terbaik
    """
    try:
        # 1. Simpan file sementara
        os.makedirs("temp_docs", exist_ok=True)
        file_path = os.path.join("temp_docs", file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. Deteksi format dan pilih metode
        ext = os.path.splitext(file.filename)[1].lower()
        
        # Untuk gambar dan PDF (kemungkinan scan), aktifkan Vision AI
        use_vision = ext in ['.jpg', '.jpeg', '.png']
        
        logger.info(f"Memproses {file.filename} (ext: {ext}, use_vision: {use_vision})")
        
        # 3. Ekstrak teks
        result = local_doc_engine.extract_text(file_path, file.filename, use_vision=use_vision)
        
        # 4. Jika hasil kurang optimal dan bukan vision, coba dengan vision
        teks_dokumen = result.get('text', '')
        method = result.get('method', 'unknown')
        
        if (not teks_dokumen or len(teks_dokumen.strip()) < 50) and not use_vision and ext == '.pdf':
            logger.info("Hasil OCR kurang optimal, mencoba dengan Vision AI...")
            result = local_doc_engine.extract_text(file_path, file.filename, use_vision=True)
            teks_dokumen = result.get('text', '')
            method = result.get('method', 'vision_fallback')
        
        # 5. Bersihkan file sementara
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # 6. Validasi hasil
        if not teks_dokumen or len(teks_dokumen.strip()) < 50:
            return {
                "status": "error",
                "filename": file.filename,
                "message": "Tidak dapat membaca dokumen. Pastikan file memiliki teks yang jelas.",
                "teks_ekstraksi": teks_dokumen or "",
                "notulensi_ai": "Maaf, dokumen tidak dapat dibaca. Gunakan dokumen digital atau aktifkan mode Vision AI.",
                "metode": method,
                "confidence": result.get('confidence', 0)
            }
        
        # 7. Buat notulensi dengan AI
        prompt_final = PROMPT_NOTULENSI_RAPAT.format(teks_transkripsi=teks_dokumen)
        notulensi_ai = local_llm.generate(prompt_final)
        
        # 8. SIMPAN KE DATABASE
        try:
            saved_dokumen = save_dokumen(
                db=db,
                filename=file.filename,
                file_path=file_path,  # Atau path yang sesuai
                teks_ekstraksi=teks_dokumen,
                notulensi=notulensi_ai,
                metode=method,
                confidence=result.get('confidence', 0),
                pages=result.get('pages', 0)
            )
            logger.info(f"✅ Dokumen tersimpan dengan ID: {saved_dokumen.id}")
        except Exception as e:
            logger.error(f"Gagal menyimpan ke database: {e}")
            # Tetap return hasil meskipun gagal simpan
        
        # 9. Kembalikan hasil
        return {
            "status": "success",
            "filename": file.filename,
            "teks_ekstraksi": teks_dokumen,
            "notulensi_ai": notulensi_ai,
            "metode": method,
            "confidence": result.get('confidence', 0),
            "pages": result.get('pages', 0),
            "saved_to_db": True,  # Tambahkan indikator
            "dokumen_id": saved_dokumen.id if 'saved_dokumen' in locals() else None
        }
        
    except ValueError as ve:
        # Tangani error ValueError dengan ve
        logger.error(f"ValueError: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Tangani error umum dengan e
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Gagal memproses dokumen: {str(e)}")

# ==================== ENDPOINT VISION AI ====================
@app.post("/api/asisten/notulensi-dokumen-vision")
async def buat_notulensi_dengan_vision(file: UploadFile = File(...)):
    """
    Endpoint Khusus Vision AI (Qwen2-VL)
    Disediakan untuk pengguna yang ingin memaksa menggunakan Vision AI
    """
    try:
        # Validasi format
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        ext = os.path.splitext(file.filename)[1].lower()
        
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Format tidak didukung untuk Vision AI. Gunakan: {', '.join(allowed_extensions)}"
            )
        
        # Simpan file
        os.makedirs("temp_vision", exist_ok=True)
        file_path = os.path.join("temp_vision", file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Ekstrak dengan Vision AI
        result = local_doc_engine.extract_text(file_path, file.filename, use_vision=True)
        
        # Bersihkan file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        teks_dokumen = result.get('text', '')
        method = result.get('method', 'vision')
        
        # Validasi
        if not teks_dokumen or len(teks_dokumen.strip()) < 50:
            return {
                "status": "warning",
                "filename": file.filename,
                "message": "Teks hasil ekstraksi Vision AI terlalu pendek.",
                "teks_ekstraksi": teks_dokumen,
                "notulensi_ai": "Maaf, tidak dapat mengekstrak teks yang cukup untuk notulensi.",
                "metode": method,
                "confidence": result.get('confidence', 0)
            }
        
        # Buat notulensi
        prompt_final = PROMPT_NOTULENSI_RAPAT.format(teks_transkripsi=teks_dokumen)
        notulensi_ai = local_llm.generate(prompt_final)
        
        return {
            "status": "success",
            "filename": file.filename,
            "teks_ekstraksi": teks_dokumen,
            "notulensi_ai": notulensi_ai,
            "metode": method,
            "confidence": result.get('confidence', 0),
            "pages": result.get('pages', 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vision AI error: {e}")
        raise HTTPException(status_code=500, detail=f"Gagal memproses dengan Vision AI: {str(e)}")

# ==================== ENDPOINT OCR KHUSUS ====================
@app.post("/api/asisten/notulensi-dokumen-ocr")
async def buat_notulensi_dengan_ocr(file: UploadFile = File(...)):
    """
    Endpoint Khusus OCR (PaddleOCR/Tesseract)
    Disediakan untuk pengguna yang ingin memaksa menggunakan OCR biasa
    """
    try:
        # Validasi format
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.docx', '.txt']
        ext = os.path.splitext(file.filename)[1].lower()
        
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Format tidak didukung. Gunakan: {', '.join(allowed_extensions)}"
            )
        
        # Simpan file
        os.makedirs("temp_ocr", exist_ok=True)
        file_path = os.path.join("temp_ocr", file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Ekstrak dengan OCR (tanpa vision)
        result = local_doc_engine.extract_text(file_path, file.filename, use_vision=False)
        
        # Bersihkan file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        teks_dokumen = result.get('text', '')
        method = result.get('method', 'ocr')
        
        # Validasi
        if not teks_dokumen or len(teks_dokumen.strip()) < 50:
            return {
                "status": "warning",
                "filename": file.filename,
                "message": "Teks hasil OCR terlalu pendek. Coba gunakan mode Vision AI.",
                "teks_ekstraksi": teks_dokumen,
                "notulensi_ai": "Teks tidak cukup untuk dibuatkan notulensi.",
                "metode": method,
                "confidence": result.get('confidence', 0)
            }
        
        # Buat notulensi
        prompt_final = PROMPT_NOTULENSI_RAPAT.format(teks_transkripsi=teks_dokumen)
        notulensi_ai = local_llm.generate(prompt_final)
        
        return {
            "status": "success",
            "filename": file.filename,
            "teks_ekstraksi": teks_dokumen,
            "notulensi_ai": notulensi_ai,
            "metode": method,
            "confidence": result.get('confidence', 0),
            "pages": result.get('pages', 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR error: {e}")
        raise HTTPException(status_code=500, detail=f"Gagal memproses dengan OCR: {str(e)}")

# ==================== ENDPOINT EKSTRAKSI SAJA ====================
@app.post("/api/asisten/ekstrak-teks")
async def ekstrak_teks_saja(file: UploadFile = File(...)):
    """
    Endpoint untuk ekstraksi teks saja tanpa notulensi
    Berguna untuk debugging atau kebutuhan lain
    """
    try:
        os.makedirs("temp_extract", exist_ok=True)
        file_path = os.path.join("temp_extract", file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Deteksi format
        ext = os.path.splitext(file.filename)[1].lower()
        use_vision = ext in ['.jpg', '.jpeg', '.png']
        
        result = local_doc_engine.extract_text(file_path, file.filename, use_vision=use_vision)
        
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {
            "status": "success",
            "filename": file.filename,
            "teks": result.get('text', ''),
            "metode": result.get('method', 'unknown'),
            "confidence": result.get('confidence', 0),
            "pages": result.get('pages', 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ENDPOINT BATCH ====================
@app.post("/api/asisten/notulensi-batch")
async def buat_notulensi_batch(files: list[UploadFile] = File(...)):
    """
    Endpoint untuk memproses multiple file sekaligus
    """
    try:
        results = []
        
        for file in files:
            # Simpan sementara
            os.makedirs("temp_batch", exist_ok=True)
            file_path = os.path.join("temp_batch", file.filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            try:
                # Ekstrak
                ext = os.path.splitext(file.filename)[1].lower()
                use_vision = ext in ['.jpg', '.jpeg', '.png']
                
                result = local_doc_engine.extract_text(file_path, file.filename, use_vision=use_vision)
                teks = result.get('text', '')
                
                # Buat notulensi jika teks cukup
                if teks and len(teks.strip()) >= 50:
                    prompt = PROMPT_NOTULENSI_RAPAT.format(teks_transkripsi=teks)
                    notulensi = local_llm.generate(prompt)
                else:
                    notulensi = "Teks tidak cukup untuk notulensi"
                
                results.append({
                    "filename": file.filename,
                    "status": "success",
                    "teks_ekstraksi": teks,
                    "notulensi": notulensi,
                    "metode": result.get('method', 'unknown')
                })
                
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": str(e)
                })
            
            # Bersihkan
            if os.path.exists(file_path):
                os.remove(file_path)
        
        return {
            "status": "success",
            "total_files": len(files),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ENDPOINT INFORMASI ====================
@app.get("/api/info/formats")
def get_supported_formats():
    """Dapatkan daftar format yang didukung"""
    return {
        "supported_formats": {
            "text": [".txt", ".docx"],
            "pdf": [".pdf"],
            "excel": [".xlsx", ".xls"],
            "image": [".jpg", ".jpeg", ".png"],
            "audio": [".mp3", ".wav", ".m4a", ".flac"]
        },
        "methods": {
            "auto": "Deteksi otomatis metode terbaik",
            "vision": "Qwen2-VL untuk gambar dan PDF scan",
            "ocr": "PaddleOCR/Tesseract untuk ekstraksi teks",
            "text": "Ekstraksi langsung untuk dokumen teks"
        }
    }

@app.get("/api/info/models")
def get_models_info():
    """Dapatkan informasi model AI yang digunakan"""
    return {
        "text_model": getattr(local_llm, 'text_model', local_llm.model),
        "vision_model": getattr(local_llm, 'vision_model', 'Not configured'),
        "ollama_base_url": settings.OLLAMA_BASE_URL,
        "ocr_available": ocr_processor.ocr is not None,
        "tesseract_available": ocr_processor.tesseract_available
    }

# ==================== ENDPOINT DASHBOARD ====================

@app.get("/api/dashboard/stats")
async def dashboard_stats(db: Session = Depends(get_db)):
    """Dapatkan statistik untuk dashboard"""
    try:
        stats = get_dashboard_stats(db)
        return stats
    except Exception as e:
        logger.error(f"Error dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dokumen/recent")
async def get_recent_dokumen(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Dapatkan dokumen terbaru"""
    try:
        dokumen = get_all_dokumen(db, limit=limit)
        return [
            {
                "id": d.id,
                "filename": d.filename,
                "metode": d.metode,
                "created_at": d.created_at.isoformat() if d.created_at else None
            }
            for d in dokumen
        ]
    except Exception as e:
        logger.error(f"Error get recent dokumen: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== EVENT STARTUP ====================
@app.on_event("startup")
async def startup_event():
    """Inisialisasi pada saat server mulai"""
    logger.info(f"🚀 {settings.APP_NAME} v2.0.0 started!")
    
    # Gunakan attribute yang benar
    if hasattr(local_llm, 'text_model'):
        logger.info(f"📦 Text Model: {local_llm.text_model}")
    else:
        logger.info(f"📦 Text Model: {local_llm.model}")
    
    if hasattr(local_llm, 'vision_model'):
        logger.info(f"👁️ Vision Model: {local_llm.vision_model}")
    
    logger.info(f"🔍 OCR Available: {ocr_processor.ocr is not None}")
    logger.info(f"📝 Tesseract Available: {ocr_processor.tesseract_available}")
    logger.info("✅ Server siap menerima request!")

# ==================== ERROR HANDLERS ====================
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handler untuk HTTPException"""
    return {
        "status": "error",
        "code": exc.status_code,
        "detail": exc.detail
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handler untuk exception umum"""
    logger.error(f"Unhandled exception: {exc}")
    return {
        "status": "error",
        "code": 500,
        "detail": "Terjadi kesalahan internal server"
    }

# ==================== ENDPOINT ARSIP ====================

@app.post("/api/arsip/simpan")
async def simpan_arsip(
    dokumen_id: int,
    judul: str,
    kategori: str,
    klasifikasi: str,
    tanggal_terbit: str,
    tanggal_retensi: Optional[str] = None,
    nomor_surat: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Simpan dokumen ke arsip"""
    try:
        from datetime import datetime
        
        # Parse tanggal
        tgl_terbit = datetime.fromisoformat(tanggal_terbit)
        tgl_retensi = datetime.fromisoformat(tanggal_retensi) if tanggal_retensi else None
        
        arsip = save_arsip(
            db=db,
            dokumen_id=dokumen_id,
            judul=judul,
            kategori=kategori,
            klasifikasi=klasifikasi,
            tanggal_terbit=tgl_terbit,
            tanggal_retensi=tgl_retensi,
            nomor_surat=nomor_surat,
            created_by="admin"  # Nanti pakai auth
        )
        
        return {
            "status": "success",
            "message": "Arsip berhasil disimpan",
            "arsip_id": arsip.id,
            "data": {
                "judul": arsip.judul,
                "klasifikasi": arsip.klasifikasi,
                "tanggal_terbit": arsip.tanggal_terbit.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error simpan arsip: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/arsip/cari")
async def cari_arsip(
    keyword: Optional[str] = None,
    kategori: Optional[str] = None,
    klasifikasi: Optional[str] = None,
    tanggal_awal: Optional[str] = None,
    tanggal_akhir: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Cari arsip dengan filter"""
    try:
        from datetime import datetime
        
        tgl_awal = datetime.fromisoformat(tanggal_awal) if tanggal_awal else None
        tgl_akhir = datetime.fromisoformat(tanggal_akhir) if tanggal_akhir else None
        
        results = search_arsip(
            db=db,
            keyword=keyword,
            kategori=kategori,
            klasifikasi=klasifikasi,
            tanggal_awal=tgl_awal,
            tanggal_akhir=tgl_akhir
        )
        
        return {
            "status": "success",
            "total": len(results),
            "results": [
                {
                    "id": r.id,
                    "judul": r.judul,
                    "nomor_surat": r.nomor_surat,
                    "kategori": r.kategori,
                    "klasifikasi": r.klasifikasi,
                    "tanggal_terbit": r.tanggal_terbit.isoformat() if r.tanggal_terbit else None,
                    "tanggal_retensi": r.tanggal_retensi.isoformat() if r.tanggal_retensi else None,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                }
                for r in results
            ]
        }
    except Exception as e:
        logger.error(f"Error cari arsip: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/arsip/{arsip_id}/riwayat")
async def get_riwayat_arsip_endpoint(
    arsip_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Dapatkan riwayat akses suatu arsip"""
    try:
        riwayat = get_riwayat_arsip(db, arsip_id, limit)
        return {
            "status": "success",
            "arsip_id": arsip_id,
            "total": len(riwayat),
            "riwayat": [
                {
                    "user": r.user,
                    "aksi": r.aksi,
                    "ip_address": r.ip_address,
                    "akses_at": r.akses_at.isoformat() if r.akses_at else None
                }
                for r in riwayat
            ]
        }
    except Exception as e:
        logger.error(f"Error get riwayat: {e}")
        raise HTTPException(status_code=500, detail=str(e))
