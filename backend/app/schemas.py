# backend/app/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# ==================== SCHEMA DOKUMEN ====================

class DokumenBase(BaseModel):
    filename: str
    teks_ekstraksi: Optional[str] = None
    notulensi: Optional[str] = None
    metode: Optional[str] = None
    confidence: Optional[float] = None
    pages: Optional[int] = None

class DokumenCreate(DokumenBase):
    file_path: Optional[str] = None

class DokumenResponse(DokumenBase):
    id: int
    file_path: Optional[str] = None
    extra_data: Optional[dict] = None  # <-- UBAH
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==================== SCHEMA SURAT MASUK ====================

class SuratMasukBase(BaseModel):
    nomor_surat: str
    tanggal: datetime
    pengirim: str
    perihal: str
    teks: Optional[str] = None
    kategori: Optional[str] = None
    disposisi_tujuan: Optional[str] = None
    urgensi: Optional[str] = None
    status: Optional[str] = "draft"

class SuratMasukCreate(SuratMasukBase):
    pass

class SuratMasukResponse(SuratMasukBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==================== SCHEMA DISPOSISI ====================

class DisposisiBase(BaseModel):
    surat_id: int
    ringkasan: str
    kategori: str
    rekomendasi_tujuan: str
    urgensi: str
    status: Optional[str] = "pending"

class DisposisiCreate(DisposisiBase):
    pass

class DisposisiResponse(DisposisiBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==================== SCHEMA TND VALIDASI ====================

class TNDValidationRequest(BaseModel):
    file_path: str
    filename: str

class TNDValidationResponse(BaseModel):
    is_valid: bool
    status: str
    total_errors: int
    total_warnings: int
    total_suggestions: int
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    details: dict
    file_info: dict
    timestamp: datetime

# ==================== SCHEMA ARSIP ====================

class ArsipBase(BaseModel):
    dokumen_id: int
    nomor_surat: Optional[str] = None
    judul: str
    kategori: str
    klasifikasi: str  # aktif, inaktif, statis
    tanggal_terbit: datetime
    tanggal_retensi: Optional[datetime] = None

class ArsipCreate(ArsipBase):
    pass

class ArsipResponse(ArsipBase):
    id: int
    created_at: datetime
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True

# ==================== SCHEMA PENCARIAN ====================

class SearchRequest(BaseModel):
    keyword: Optional[str] = None
    tanggal_awal: Optional[datetime] = None
    tanggal_akhir: Optional[datetime] = None
    nomor_surat: Optional[str] = None
    kategori: Optional[str] = None
    klasifikasi: Optional[str] = None

class SearchResponse(BaseModel):
    total: int
    results: List[dict]