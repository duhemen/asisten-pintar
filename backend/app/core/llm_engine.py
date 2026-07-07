import requests
import json
import base64
import logging
from typing import Optional, Union
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaLLMEngine:
    def __init__(self, base_url: str = "http://localhost:11434", text_model: str = "qwen2.5:14b-instruct-q4_K_M"):
        self.base_url = base_url
        self.text_model = text_model  # Model untuk teks
        self.vision_model = "hf.co/bartowski/Qwen2-VL-2B-Instruct-GGUF:Q4_K_M"  # Model vision
        self.model = text_model  # Untuk kompatibilitas dengan kode lama
        
        logger.info(f"📝 Text Model: {self.text_model}")
        logger.info(f"👁️ Vision Model: {self.vision_model}")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate teks dengan model biasa"""
        try:
            data = {
                "model": self.text_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "num_predict": 2048
                }
            }
            
            if system_prompt:
                data["system"] = system_prompt
            
            logger.info(f"Mengirim request ke Ollama: {self.text_model}")
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"Error dari Ollama: {response.status_code} - {response.text}")
                return ""
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout pada model {self.text_model}")
            return "Maaf, pemrosesan memakan waktu terlalu lama. Silakan coba lagi."
        except Exception as e:
            logger.error(f"Error dalam generate: {e}")
            return ""
    
    def generate_with_vision(self, prompt: str, image_data: Union[str, bytes]) -> str:
        """
        Generate menggunakan Qwen2-VL untuk gambar/PDF scan
        """
        try:
            # Encode gambar ke base64
            if isinstance(image_data, str):
                with open(image_data, "rb") as image_file:
                    image_bytes = image_file.read()
                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            else:
                image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            data = {
                "model": self.vision_model,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 2048
                }
            }
            
            logger.info(f"Mengirim request vision ke: {self.vision_model}")
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"Vision error: {response.status_code} - {response.text}")
                return self._fallback_vision(prompt, image_data)
                
        except Exception as e:
            logger.error(f"Error dalam generate_with_vision: {e}")
            return self._fallback_vision(prompt, image_data)
    
    def _fallback_vision(self, prompt: str, image_data: Union[str, bytes]) -> str:
        """Fallback jika vision gagal, gunakan OCR biasa"""
        try:
            from app.core.ocr_engine import ocr_processor
            
            if isinstance(image_data, str):
                text = ocr_processor.extract_text_from_image(image_data)
            else:
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                    tmp.write(image_data)
                    tmp_path = tmp.name
                text = ocr_processor.extract_text_from_image(tmp_path)
                os.unlink(tmp_path)
            
            return self.generate(f"{prompt}\n\nTeks dari OCR:\n{text}")
            
        except Exception as e:
            logger.error(f"Fallback vision error: {e}")
            return "Maaf, tidak dapat memproses gambar."

# Singleton
local_llm = OllamaLLMEngine()