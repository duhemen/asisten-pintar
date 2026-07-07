# backend/app/database.py
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
import os
from dotenv import load_dotenv

load_dotenv()

# Ambil komponen database dari .env
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Bp2jk%40kalteng123")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "asisten_pintar")

# Encode password jika belum encoded
# URL encoding akan mengubah @ menjadi %40, # menjadi %23, dll
if '%' not in DB_PASSWORD:  # Jika password belum di-encode
    DB_PASSWORD = quote_plus(DB_PASSWORD)

# Build DATABASE_URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Atau gunakan langsung dari .env (jika sudah di-encode)
# DATABASE_URL = os.getenv("DATABASE_URL")

# Buat engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False  # Set True untuk debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dapatkan session database"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Inisialisasi database - buat semua tabel"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")


# backend/app/database.py
# Tambahkan di bagian bawah (setelah get_db)

from sqlalchemy.orm import Session
from app.models import Dokumen, SuratMasuk, Disposisi, Arsip, RiwayatAkses
from datetime import datetime
from typing import Optional, List, Dict, Any

# ==================== CRUD DOKUMEN ====================

def save_dokumen(
    db: Session,
    filename: str,
    file_path: str,
    teks_ekstraksi: str,
    notulensi: str,
    metode: str,
    confidence: float,
    pages: int = 0,
    extra_data: Optional[Dict] = None
) -> Dokumen:
    """Simpan dokumen dan notulensi ke database"""
    dokumen = Dokumen(
        filename=filename,
        file_path=file_path,
        teks_ekstraksi=teks_ekstraksi,
        notulensi=notulensi,
        metode=metode,
        confidence=confidence,
        pages=pages,
        extra_data=extra_data or {}
    )
    db.add(dokumen)
    db.commit()
    db.refresh(dokumen)
    return dokumen

def get_dokumen_by_id(db: Session, dokumen_id: int) -> Optional[Dokumen]:
    """Ambil dokumen berdasarkan ID"""
    return db.query(Dokumen).filter(Dokumen.id == dokumen_id).first()

def get_all_dokumen(db: Session, limit: int = 100, offset: int = 0) -> List[Dokumen]:
    """Ambil semua dokumen dengan pagination"""
    return db.query(Dokumen).order_by(Dokumen.created_at.desc()).offset(offset).limit(limit).all()

def search_dokumen(db: Session, keyword: str) -> List[Dokumen]:
    """Cari dokumen berdasarkan keyword di teks atau filename"""
    return db.query(Dokumen).filter(
        Dokumen.filename.contains(keyword) | 
        Dokumen.teks_ekstraksi.contains(keyword)
    ).all()

def count_dokumen(db: Session) -> int:
    """Hitung total dokumen"""
    return db.query(Dokumen).count()

# ==================== CRUD SURAT MASUK ====================

def save_surat_masuk(
    db: Session,
    nomor_surat: str,
    tanggal: datetime,
    pengirim: str,
    perihal: str,
    teks: str,
    file_path: Optional[str] = None
) -> SuratMasuk:
    """Simpan surat masuk"""
    surat = SuratMasuk(
        nomor_surat=nomor_surat,
        tanggal=tanggal,
        pengirim=pengirim,
        perihal=perihal,
        teks=teks,
        file_path=file_path
    )
    db.add(surat)
    db.commit()
    db.refresh(surat)
    return surat

def update_surat_disposisi(
    db: Session,
    surat_id: int,
    kategori: str,
    disposisi_tujuan: str,
    urgensi: str
) -> Optional[SuratMasuk]:
    """Update surat dengan hasil disposisi"""
    surat = db.query(SuratMasuk).filter(SuratMasuk.id == surat_id).first()
    if surat:
        surat.kategori = kategori
        surat.disposisi_tujuan = disposisi_tujuan
        surat.urgensi = urgensi
        surat.status = "proses"
        db.commit()
        db.refresh(surat)
    return surat

# ==================== CRUD DISPOSISI ====================

def save_disposisi(
    db: Session,
    surat_id: int,
    ringkasan: str,
    kategori: str,
    rekomendasi_tujuan: str,
    urgensi: str,
    catatan: Optional[str] = None
) -> Disposisi:
    """Simpan hasil disposisi"""
    disposisi = Disposisi(
        surat_id=surat_id,
        ringkasan=ringkasan,
        kategori=kategori,
        rekomendasi_tujuan=rekomendasi_tujuan,
        urgensi=urgensi,
        catatan=catatan
    )
    db.add(disposisi)
    db.commit()
    db.refresh(disposisi)
    return disposisi

def get_disposisi_by_surat(db: Session, surat_id: int) -> Optional[Disposisi]:
    """Ambil disposisi berdasarkan surat_id"""
    return db.query(Disposisi).filter(Disposisi.surat_id == surat_id).first()

# ==================== CRUD ARSIP ====================

def save_arsip(
    db: Session,
    dokumen_id: int,
    judul: str,
    kategori: str,
    klasifikasi: str,
    tanggal_terbit: datetime,
    tanggal_retensi: Optional[datetime] = None,
    nomor_surat: Optional[str] = None,
    lokasi: Optional[str] = None,
    created_by: Optional[str] = None
) -> Arsip:
    """Simpan arsip"""
    arsip = Arsip(
        dokumen_id=dokumen_id,
        nomor_surat=nomor_surat,
        judul=judul,
        kategori=kategori,
        klasifikasi=klasifikasi,
        tanggal_terbit=tanggal_terbit,
        tanggal_retensi=tanggal_retensi,
        lokasi=lokasi,
        created_by=created_by
    )
    db.add(arsip)
    db.commit()
    db.refresh(arsip)
    return arsip

def search_arsip(
    db: Session,
    keyword: Optional[str] = None,
    kategori: Optional[str] = None,
    klasifikasi: Optional[str] = None,
    tanggal_awal: Optional[datetime] = None,
    tanggal_akhir: Optional[datetime] = None,
    limit: int = 50
) -> List[Arsip]:
    """Cari arsip dengan berbagai filter"""
    query = db.query(Arsip)
    
    if keyword:
        query = query.filter(
            Arsip.judul.contains(keyword) | 
            Arsip.nomor_surat.contains(keyword)
        )
    
    if kategori:
        query = query.filter(Arsip.kategori == kategori)
    
    if klasifikasi:
        query = query.filter(Arsip.klasifikasi == klasifikasi)
    
    if tanggal_awal:
        query = query.filter(Arsip.tanggal_terbit >= tanggal_awal)
    
    if tanggal_akhir:
        query = query.filter(Arsip.tanggal_terbit <= tanggal_akhir)
    
    return query.order_by(Arsip.created_at.desc()).limit(limit).all()

# ==================== CRUD RIWAYAT AKSES ====================

def log_akses(
    db: Session,
    arsip_id: int,
    user: str,
    aksi: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> RiwayatAkses:
    """Catat riwayat akses arsip"""
    riwayat = RiwayatAkses(
        arsip_id=arsip_id,
        user=user,
        aksi=aksi,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(riwayat)
    db.commit()
    db.refresh(riwayat)
    return riwayat

def get_riwayat_arsip(db: Session, arsip_id: int, limit: int = 50) -> List[RiwayatAkses]:
    """Ambil riwayat akses suatu arsip"""
    return db.query(RiwayatAkses).filter(
        RiwayatAkses.arsip_id == arsip_id
    ).order_by(RiwayatAkses.akses_at.desc()).limit(limit).all()

# ==================== STATISTIK DASHBOARD ====================

def get_dashboard_stats(db: Session) -> Dict[str, Any]:
    """Dapatkan statistik untuk dashboard"""
    from sqlalchemy import func, extract
    
    today = datetime.now().date()
    
    # Total dokumen
    total_dokumen = db.query(Dokumen).count()
    
    # Dokumen hari ini
    dokumen_hari_ini = db.query(Dokumen).filter(
        func.date(Dokumen.created_at) == today
    ).count()
    
    # Total surat masuk
    total_surat = db.query(SuratMasuk).count()
    
    # Surat hari ini
    surat_hari_ini = db.query(SuratMasuk).filter(
        func.date(SuratMasuk.created_at) == today
    ).count()
    
    # Status disposisi
    disposisi_terkirim = db.query(SuratMasuk).filter(
        SuratMasuk.status == "proses"
    ).count()
    
    disposisi_selesai = db.query(SuratMasuk).filter(
        SuratMasuk.status == "selesai"
    ).count()
    
    # Arsip per klasifikasi
    arsip_aktif = db.query(Arsip).filter(Arsip.klasifikasi == "aktif").count()
    arsip_inaktif = db.query(Arsip).filter(Arsip.klasifikasi == "inaktif").count()
    arsip_statis = db.query(Arsip).filter(Arsip.klasifikasi == "statis").count()
    
    return {
        "total_dokumen": total_dokumen,
        "dokumen_hari_ini": dokumen_hari_ini,
        "total_surat": total_surat,
        "surat_hari_ini": surat_hari_ini,
        "disposisi_terkirim": disposisi_terkirim,
        "disposisi_selesai": disposisi_selesai,
        "arsip_aktif": arsip_aktif,
        "arsip_inaktif": arsip_inaktif,
        "arsip_statis": arsip_statis,
    }