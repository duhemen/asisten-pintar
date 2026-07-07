# backend/app/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from typing import Optional

class Dokumen(Base):
    __tablename__ = "dokumen"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255))
    file_path = Column(String(500))
    teks_ekstraksi = Column(Text)
    notulensi = Column(Text)
    metode = Column(String(50))
    confidence = Column(Float)
    pages = Column(Integer, default=0)
    extra_data = Column(JSON, default={})  # <-- UBAH DARI 'metadata' JADI 'extra_data'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relasi
    arsip = relationship("Arsip", back_populates="dokumen", uselist=False)

class SuratMasuk(Base):
    __tablename__ = "surat_masuk"
    
    id = Column(Integer, primary_key=True, index=True)
    nomor_surat = Column(String(100), unique=True, index=True)
    tanggal = Column(DateTime)
    pengirim = Column(String(200))
    perihal = Column(String(255))
    teks = Column(Text)
    kategori = Column(String(50))
    disposisi_tujuan = Column(String(100))
    urgensi = Column(String(20))
    status = Column(String(50), default="draft")
    file_path = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relasi
    disposisi = relationship("Disposisi", back_populates="surat", uselist=False)

class Disposisi(Base):
    __tablename__ = "disposisi"
    
    id = Column(Integer, primary_key=True, index=True)
    surat_id = Column(Integer, ForeignKey("surat_masuk.id"))
    ringkasan = Column(Text)
    kategori = Column(String(50))
    rekomendasi_tujuan = Column(String(100))
    urgensi = Column(String(20))
    status = Column(String(50), default="pending")
    catatan = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relasi
    surat = relationship("SuratMasuk", back_populates="disposisi")

class Arsip(Base):
    __tablename__ = "arsip"
    
    id = Column(Integer, primary_key=True, index=True)
    dokumen_id = Column(Integer, ForeignKey("dokumen.id"))
    nomor_surat = Column(String(100))
    judul = Column(String(255))
    kategori = Column(String(50))
    klasifikasi = Column(String(20))
    tanggal_terbit = Column(DateTime)
    tanggal_retensi = Column(DateTime)
    lokasi = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100))
    
    # Relasi
    dokumen = relationship("Dokumen", back_populates="arsip")
    riwayat = relationship("RiwayatAkses", back_populates="arsip")

class RiwayatAkses(Base):
    __tablename__ = "riwayat_akses"
    
    id = Column(Integer, primary_key=True, index=True)
    arsip_id = Column(Integer, ForeignKey("arsip.id"))
    user = Column(String(100))
    aksi = Column(String(50))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    akses_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relasi
    arsip = relationship("Arsip", back_populates="riwayat")