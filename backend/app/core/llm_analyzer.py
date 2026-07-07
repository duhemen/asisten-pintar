import httpx
import json
from app.config import settings

class LocalLLMAnalyzer:
    def __init__(self):
        # Mengambil konfigurasi dari app/config.py yang sudah kita buat
        self.ollama_url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        self.model_name = settings.OLLAMA_MODEL

    async def analyze_disposisi(self, surat_text: str) -> dict:
        """
        Menganalisis teks surat masuk secara offline menggunakan Qwen 2.5 14B
        untuk menyarankan rute disposisi kedinasan.
        """
        prompt = f"""
        Anda adalah AI Asistent profesional untuk Sekretaris di instansi Pemerintah Indonesia.
        Tugas Anda adalah membaca dan menganalisis teks surat masuk secara akurat.
        
        Ekstrak informasi penting dari surat tersebut dan kembalikan hasilnya HANYA dalam format JSON dengan struktur seperti ini:
        {{
            "ringkasan": "Ringkasan isi surat maksimal 2 kalimat jelas.",
            "kategori": "Kategori (Keuangan / Kepegawaian / Infrastruktur / Protokoler / Umum)",
            "rekomendasi_tujuan": "Nama Bagian/Bidang/Seksi yang paling tepat menerima disposisi ini",
            "urgensi": "Biasa / Penting / Segera"
        }}

        Teks Surat:
        \"\"\"{surat_text}\"\"\"

        Ingat: Jangan berikan teks pembuka atau penutup. Berikan langsung raw JSON yang valid.
        """

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,  # Di-set False agar model berpikir tuntas baru mengirim jawaban
            "format": "json"  # Fitur Ollama untuk memaksa output berupa JSON valid
        }

        # Menggunakan httpx untuk koneksi asinkronus (async) yang efisien
        async with httpx.AsyncClient() as client:
            try:
                # Batas waktu diperpanjang ke 60 detik karena model 14B butuh waktu berpikir di GPU 8GB
                response = await client.post(self.ollama_url, json=payload, timeout=60.0)
                
                if response.status_code == 200:
                    raw_response = response.json().get("response", "{}")
                    # Mengubah string JSON dari AI menjadi Python Dictionary
                    return json.loads(raw_response)
                else:
                    return {"error": f"Ollama mengembalikan status {response.status_code}"}
                    
            except json.JSONDecodeError:
                return {"error": "Gagal parsing format JSON dari model AI."}
            except Exception as e:
                return {"error": f"Gagal menghubungi Ollama: {str(e)}"}