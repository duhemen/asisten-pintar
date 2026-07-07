import os
import tempfile
import logging
from typing import Optional, List, Dict, Any
import io
import subprocess

# Import dengan try-except
try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None
    print("Warning: pdf2image tidak terinstal. OCR PDF tidak akan didukung.")

try:
    import pytesseract
except ImportError:
    pytesseract = None
    print("Warning: pytesseract tidak terinstal. Tesseract OCR tidak akan didukung.")

try:
    from PIL import Image
except ImportError:
    Image = None
    print("Warning: PIL tidak terinstal. OCR gambar tidak akan didukung.")

# PaddleOCR optional
try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None
    print("Warning: paddleocr tidak terinstal. PaddleOCR tidak akan didukung.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRProcessor:
    def __init__(self):
        """Inisialisasi OCR dengan PaddleOCR dan Tesseract"""
        self.ocr = None
        self.tesseract_available = False
        self.poppler_available = False
        self.poppler_path = None
        
        # Cek poppler di berbagai lokasi
        self._check_poppler()
        
        # Inisialisasi PaddleOCR
        if PaddleOCR is not None:
            try:
                self.ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang='id',
                    show_log=False
                )
                logger.info("PaddleOCR berhasil diinisialisasi")
            except Exception as e:
                logger.warning(f"PaddleOCR gagal dimuat: {e}")
        else:
            logger.warning("PaddleOCR tidak tersedia")
        
        # Cek Tesseract
        if pytesseract is not None:
            try:
                pytesseract.get_tesseract_version()
                self.tesseract_available = True
                logger.info("Tesseract tersedia")
            except Exception as e:
                logger.warning(f"Tesseract tidak tersedia: {e}")
        else:
            logger.warning("pytesseract tidak terinstal")
        
        # Cek pdf2image
        if convert_from_path is None:
            logger.warning("pdf2image tidak terinstal. PDF OCR tidak akan didukung.")
        
        # Cek PIL
        if Image is None:
            logger.warning("PIL tidak terinstal. OCR gambar tidak akan didukung.")
    
    def _check_poppler(self):
        """Cek apakah poppler terinstall di berbagai lokasi"""
        # Dapatkan current working directory
        cwd = os.getcwd()
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/app/core -> backend
        
        possible_paths = [
            # Lokasi umum
            r"C:\poppler\bin",
            r"C:\Program Files\poppler\bin",
            
            # Lokasi di project dengan berbagai versi
            os.path.join(backend_dir, "poppler-26.02.0", "bin"),
            os.path.join(backend_dir, "poppler", "bin"),
            os.path.join(cwd, "poppler-26.02.0", "bin"),
            os.path.join(cwd, "poppler", "bin"),
            
            # Relative path dari backend
            os.path.join("..", "poppler-26.02.0", "bin"),
            os.path.join("..", "poppler", "bin"),
        ]
        
        logger.info(f"🔍 Mencari Poppler di: {possible_paths}")
        
        for path in possible_paths:
            if os.path.exists(path):
                # Cek apakah ada pdftoppm.exe
                pdftoppm_path = os.path.join(path, "pdftoppm.exe")
                if os.path.exists(pdftoppm_path):
                    self.poppler_path = path
                    self.poppler_available = True
                    logger.info(f"✅ Poppler ditemukan di: {path}")
                    
                    # Tambahkan ke PATH untuk proses ini
                    os.environ["PATH"] = path + os.pathsep + os.environ["PATH"]
                    
                    # Test dengan subprocess
                    try:
                        result = subprocess.run(
                            [pdftoppm_path, "-v"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        # Poppler output version ke stderr
                        version_info = result.stderr.strip() if result.stderr else result.stdout.strip()
                        logger.info(f"✅ Poppler version: {version_info.split()[1] if version_info else 'Unknown'}")
                    except Exception as e:
                        logger.warning(f"Poppler test failed: {e}")
                    
                    return
        
        # Jika tidak ditemukan, coba cek di PATH
        try:
            result = subprocess.run(
                ['pdftoppm', '-v'],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.poppler_available = True
            logger.info("✅ Poppler ditemukan di PATH")
        except Exception as e:
            self.poppler_available = False
            logger.warning("❌ Poppler tidak ditemukan. PDF scan tidak akan didukung.")
            logger.warning("📥 Download poppler dari: https://github.com/oschwartz10612/poppler-windows/releases/")
            logger.warning("📁 Ekstrak ke C:\\poppler atau project folder")
            logger.warning("🔄 Restart aplikasi setelah install")
    
    def extract_text_from_pdf(self, pdf_path: str, use_vision: bool = True) -> Dict[str, Any]:
        """Ekstrak teks dari PDF dengan OCR atau Vision AI"""
        if not os.path.exists(pdf_path):
            return {
                'text': '',
                'method': 'error',
                'pages': 0,
                'confidence': 0
            }
        
        try:
            logger.info(f"Memproses PDF: {pdf_path}")
            
            # Cek poppler availability
            if not self.poppler_available:
                error_msg = """❌ Poppler tidak ditemukan. 

📥 Download Poppler dari:
https://github.com/oschwartz10612/poppler-windows/releases/

📁 Ekstrak ke salah satu lokasi:
- C:\\poppler
- C:\\asisten-pintar\\backend\\poppler-26.02.0
- C:\\asisten-pintar\\backend\\poppler

🔧 Pastikan folder berisi: pdftoppm.exe, pdfinfo.exe, dll

🔄 Restart aplikasi setelah install

💡 Atau gunakan file PDF digital (bukan scan) untuk diproses langsung.
"""
                return {
                    'text': error_msg,
                    'method': 'error_poppler',
                    'pages': 0,
                    'confidence': 0
                }
            
            if convert_from_path is None:
                raise ImportError("pdf2image tidak terinstal. Install dengan: pip install pdf2image")
            
            # Konversi PDF ke gambar
            try:
                # Gunakan poppler_path jika tersedia
                if self.poppler_path:
                    logger.info(f"🔄 Menggunakan poppler_path: {self.poppler_path}")
                    images = convert_from_path(
                        pdf_path, 
                        dpi=150,
                        fmt='jpeg',
                        poppler_path=self.poppler_path
                    )
                else:
                    images = convert_from_path(
                        pdf_path, 
                        dpi=150,
                        fmt='jpeg'
                    )
                total_pages = len(images)
                logger.info(f"✅ Berhasil konversi {total_pages} halaman")
                
            except Exception as e:
                logger.error(f"Gagal konversi PDF: {e}")
                return {
                    'text': f"❌ Gagal mengkonversi PDF: {str(e)}\n\nPastikan Poppler terinstall dengan benar.",
                    'method': 'error_conversion',
                    'pages': 0,
                    'confidence': 0
                }
            
            if total_pages == 0:
                return {
                    'text': '',
                    'method': 'failed',
                    'pages': 0,
                    'confidence': 0
                }
            
            # Jika hanya 1-3 halaman, gunakan Vision AI
            if total_pages <= 3 and use_vision:
                logger.info(f"📄 PDF {total_pages} halaman, menggunakan Vision AI")
                return self._process_with_vision(images)
            
            # Untuk banyak halaman, gunakan OCR
            logger.info(f"📄 PDF {total_pages} halaman, menggunakan OCR")
            return self._process_with_ocr(images)
            
        except Exception as e:
            logger.error(f"Error saat ekstraksi PDF: {e}")
            return {
                'text': f"Error: {str(e)}",
                'method': 'error',
                'pages': 0,
                'confidence': 0
            }
    
    def _process_with_vision(self, images: List) -> Dict[str, Any]:
        """Proses dengan Vision AI (Qwen2-VL)"""
        try:
            from app.core.llm_engine import local_llm
            
            all_text = []
            
            for page_num, image in enumerate(images, 1):
                try:
                    # Konversi image ke bytes
                    img_bytes = io.BytesIO()
                    image.save(img_bytes, format='JPEG', quality=85)
                    img_bytes = img_bytes.getvalue()
                    
                    # Prompt khusus untuk ekstraksi dokumen
                    prompt = f"""
Anda adalah asisten AI yang bertugas mengekstrak teks dari dokumen rapat.

INSTRUKSI:
1. Bacalah gambar halaman {page_num} ini dengan teliti
2. Ekstrak semua teks yang terbaca
3. Jika ada tabel, deskripsikan dengan jelas
4. Jaga format dan struktur teks

HASIL EKSTRAKSI:
"""
                    
                    # Gunakan Vision AI
                    response = local_llm.generate_with_vision(prompt, img_bytes)
                    if response and len(response.strip()) > 10:
                        all_text.append(f"Halaman {page_num}:\n{response}\n")
                    else:
                        # Jika vision gagal, coba OCR
                        logger.warning(f"Vision AI halaman {page_num} hasil kosong, menggunakan OCR")
                        from pdf2image import convert_from_path
                        # Gunakan image yang sudah ada, OCR langsung
                        if self.ocr:
                            result = self.ocr.ocr(image, cls=True)
                            if result and len(result) > 0:
                                page_text = []
                                for line in result:
                                    if line and len(line) > 0:
                                        for word_info in line:
                                            if len(word_info) >= 2:
                                                page_text.append(word_info[1][0])
                                all_text.append(f"Halaman {page_num} (OCR):\n{' '.join(page_text)}\n")
                            else:
                                all_text.append(f"Halaman {page_num}: [Teks tidak terbaca]\n")
                        else:
                            all_text.append(f"Halaman {page_num}: [Teks tidak terbaca]\n")
                    
                except Exception as e:
                    logger.error(f"Error vision page {page_num}: {e}")
                    all_text.append(f"Halaman {page_num}: [Error: {str(e)}]\n")
            
            final_text = '\n'.join(all_text)
            
            # Jika hasil terlalu pendek, coba OCR
            if len(final_text.strip()) < 100:
                logger.info("Hasil Vision AI terlalu pendek, mencoba OCR...")
                return self._process_with_ocr(images)
            
            return {
                'text': final_text,
                'method': 'vision_ai',
                'pages': len(images),
                'confidence': 0.85
            }
        except Exception as e:
            logger.error(f"Vision AI error: {e}")
            return {
                'text': f"Error Vision AI: {str(e)}",
                'method': 'vision_error',
                'pages': len(images) if images else 0,
                'confidence': 0
            }
    
    def _process_with_ocr(self, images: List) -> Dict[str, Any]:
        """Proses dengan OCR (PaddleOCR/Tesseract)"""
        all_text = []
        confidence_sum = 0
        total_processed = 0
        
        for page_num, image in enumerate(images, 1):
            page_text = []
            confidence = 0
            
            logger.info(f"📄 Memproses halaman {page_num}/{len(images)}")
            
            # Gunakan PaddleOCR jika tersedia
            if self.ocr:
                try:
                    result = self.ocr.ocr(image, cls=True)
                    if result and len(result) > 0:
                        for line in result:
                            if line and len(line) > 0:
                                for word_info in line:
                                    if len(word_info) >= 2:
                                        text = word_info[1][0]
                                        conf = word_info[1][1] if len(word_info[1]) > 1 else 0
                                        if text and text.strip():
                                            page_text.append(text)
                                            confidence += conf
                                            total_processed += 1
                    else:
                        # Fallback Tesseract
                        if self.tesseract_available and pytesseract is not None:
                            text = pytesseract.image_to_string(image, lang='ind')
                            if text and text.strip():
                                page_text.append(text)
                                confidence += 50
                except Exception as e:
                    logger.warning(f"PaddleOCR gagal untuk halaman {page_num}: {e}")
                    # Fallback Tesseract
                    if self.tesseract_available and pytesseract is not None:
                        text = pytesseract.image_to_string(image, lang='ind')
                        if text and text.strip():
                            page_text.append(text)
                            confidence += 50
            else:
                # Hanya Tesseract
                if self.tesseract_available and pytesseract is not None:
                    text = pytesseract.image_to_string(image, lang='ind')
                    if text and text.strip():
                        page_text.append(text)
                        confidence += 50
            
            if page_text:
                all_text.append(f"Halaman {page_num}:\n{' '.join(page_text)}\n")
            else:
                all_text.append(f"Halaman {page_num}: [Tidak ada teks terbaca]\n")
            
            confidence_sum += confidence
        
        avg_confidence = confidence_sum / (len(images) * 10) if confidence_sum > 0 and len(images) > 0 else 0.5
        
        return {
            'text': '\n'.join(all_text),
            'method': 'ocr',
            'pages': len(images),
            'confidence': min(avg_confidence, 1.0)
        }
    
    def extract_text_from_image(self, image_path: str, use_vision: bool = True) -> Dict[str, Any]:
        """Ekstrak teks dari gambar"""
        try:
            if not os.path.exists(image_path):
                return {
                    'text': '',
                    'method': 'error',
                    'confidence': 0
                }
            
            if Image is None:
                raise ImportError("PIL tidak terinstal")
            
            if use_vision:
                try:
                    from app.core.llm_engine import local_llm
                    
                    with open(image_path, 'rb') as f:
                        img_bytes = f.read()
                    
                    prompt = """
Anda adalah asisten AI yang mengekstrak teks dari gambar dokumen.

INSTRUKSI:
1. Baca gambar ini dengan teliti
2. Ekstrak semua teks yang terbaca
3. Jika ada tulisan tangan, interpretasikan sebisa mungkin
4. Berikan hasil ekstraksi yang akurat

TEKS DARI GAMBAR:
"""
                    
                    response = local_llm.generate_with_vision(prompt, img_bytes)
                    return {
                        'text': response,
                        'method': 'vision_ai',
                        'confidence': 0.85
                    }
                except Exception as e:
                    logger.warning(f"Vision AI gagal untuk gambar: {e}")
                    # Fallback ke OCR
                    use_vision = False
            
            # Gunakan OCR
            image = Image.open(image_path)
            text = ""
            
            if self.ocr:
                try:
                    result = self.ocr.ocr(image_path, cls=True)
                    if result and len(result) > 0:
                        for line in result:
                            if line and len(line) > 0:
                                for word_info in line:
                                    if len(word_info) >= 2:
                                        text += word_info[1][0] + " "
                    else:
                        if self.tesseract_available and pytesseract is not None:
                            text = pytesseract.image_to_string(image, lang='ind')
                except:
                    if self.tesseract_available and pytesseract is not None:
                        text = pytesseract.image_to_string(image, lang='ind')
            elif self.tesseract_available and pytesseract is not None:
                text = pytesseract.image_to_string(image, lang='ind')
            
            return {
                'text': text.strip(),
                'method': 'ocr',
                'confidence': 0.7
            }
                
        except Exception as e:
            logger.error(f"Error ekstraksi gambar: {e}")
            return {
                'text': f"Error: {str(e)}",
                'method': 'error',
                'confidence': 0
            }

# Singleton
ocr_processor = OCRProcessor()