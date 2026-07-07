import os
import sys

# MANTRA KHUSUS: Memaksa Python Windows mendeteksi pustaka CUDA baru yang di-download
if sys.platform == "win32":
    # Jalur folder tempat site-packages env kamu menyimpan file DLL NVIDIA
    cuda_path = os.path.join(os.path.dirname(sys.executable), "Lib", "site-packages", "nvidia", "cublas", "bin")
    cudnn_path = os.path.join(os.path.dirname(sys.executable), "Lib", "site-packages", "nvidia", "cudnn", "bin")
    
    if os.path.exists(cuda_path):
        os.add_dll_directory(cuda_path)
    if os.path.exists(cudnn_path):
        os.add_dll_directory(cudnn_path)

from faster_whisper import WhisperModel

class LocalWhisperEngine:
    def __init__(self):
        # Menggunakan model 'small' (hanya butuh ~2GB VRAM) agar muat bersama Qwen 14B kamu
        self.model_size = "small"
        
        # Inisialisasi model langsung ke GPU NVIDIA via CUDA
        print("Menginisialisasi Model Faster-Whisper di GPU CUDA...")
        self.model = WhisperModel(self.model_size, device="cuda", compute_type="float16")
        print("Model Faster-Whisper SIAP!")

    def transcribe_audio(self, audio_path: str) -> str:
        """
        Menerima file audio (.mp3 atau .wav) lalu mentranskripsikannya ke dalam teks.
        """
        if not os.path.exists(audio_path):
            return "Error: File audio tidak ditemukan di direktori lokal."
        
        # Eksekusi transkripsi otomatis fokus ke Bahasa Indonesia ('id')
        segments, info = self.model.transcribe(audio_path, language="id", beam_size=5)
        
        print(f"Mendeteksi bahasa: {info.language} dengan probabilitas {info.language_probability:.2f}")
        
        # Gabungkan semua potongan teks rapat/lagu berdasarkan durasi menit:detik
        full_text = []
        for segment in segments:
            timestamp = f"[{int(segment.start)//60:02d}:{int(segment.start)%60:02d} - {int(segment.end)//60:02d}:{int(segment.end)%60:02d}]"
            full_text.append(f"{timestamp} {segment.text}")
            
        return "\n".join(full_text)