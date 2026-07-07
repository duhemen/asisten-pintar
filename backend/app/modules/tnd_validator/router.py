# backend/app/modules/tnd_validator/router.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import shutil
import logging
from typing import Optional

from .service import tnd_validator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tnd", tags=["TND Validator"])

@router.get("/info")
async def get_tnd_info():
    """Informasi tentang fitur TND Validator"""
    return {
        "status": "ready",
        "features": [
            "Validasi format nomor surat",
            "Cek kesesuaian font",
            "Deteksi kop surat",
            "Validasi tanda tangan",
            "Cek struktur surat"
        ],
        "supported_formats": [".docx", ".pdf", ".txt"]
    }

@router.post("/validate")
async def validate_document(file: UploadFile = File(...)):
    """
    Validasi dokumen sesuai Tata Naskah Dinas (TND)
    """
    try:
        # Validasi format
        ext = os.path.splitext(file.filename)[1].lower()
        supported = ['.docx', '.pdf', '.txt']
        
        if ext not in supported:
            raise HTTPException(
                status_code=400,
                detail=f"Format {ext} tidak didukung. Gunakan: {', '.join(supported)}"
            )
        
        # Simpan file sementara
        temp_dir = "temp_tnd"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validasi
        hasil = tnd_validator.validate_file(file_path, file.filename)
        
        # Hapus file sementara
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Tambahkan info file
        hasil["file_info"] = {
            "filename": file.filename,
            "extension": ext,
            "size_kb": round(file.size / 1024, 1) if file.size else 0
        }
        
        return hasil
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validasi TND: {e}")
        raise HTTPException(status_code=500, detail=f"Gagal validasi: {str(e)}")

@router.get("/standar")
async def get_standar_tnd():
    """Dapatkan standar TND yang digunakan"""
    return {
        "standar": {
            "font": {
                "nama": ["Arial", "Times New Roman", "Calibri"],
                "ukuran": "12pt",
                "spasi": "1.5"
            },
            "margin": {
                "top": "4 cm",
                "bottom": "3 cm",
                "left": "4 cm",
                "right": "3 cm"
            },
            "nomor_surat": "000/000/Instansi/Kode/Bulan/Tahun",
            "contoh_nomor": "005/123/Diskominfo/A/2024"
        }
    }