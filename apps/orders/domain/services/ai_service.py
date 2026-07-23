"""
AI Triage Domain Service.
Integrates with Google Gemini API to analyze raw customer vehicle complaints and generate structured technical diagnosis JSON.
"""
import json
import logging
from typing import Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)


class AITriageService:
    """
    Service class for Google Gemini AI Triage Engine.
    """

    SYSTEM_PROMPT = """
Anda adalah Master Mekanik Otomotif AI senior untuk sistem darurat OtoGrid.
Tugas Anda adalah menerima deskripsi keluhan awam tentang kerusakan kendaraan dari pengguna dan memberikan diagnosis teknis awal.

Berikan output HANYA dalam format JSON yang valid tanpa teks tambahan atau Markdown codeblock formatting di luar JSON.

Format JSON yang diwajibkan:
{
  "possible_issues": ["Masalah 1", "Masalah 2"],
  "danger_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "recommended_tools": ["Alat 1", "Alat 2"],
  "recommended_parts": ["Suku Cadang 1", "Suku Cadang 2"],
  "summary": "Ringkasan diagnosis teknis dalam 1-2 kalimat."
}
"""

    @classmethod
    def diagnose_complaint(cls, complaint_text: str) -> Dict[str, Any]:
        """
        Invokes Gemini API with hidden System Prompt to analyze vehicle complaint.

        Args:
            complaint_text (str): Raw user description of breakdown.

        Returns:
            Dict[str, Any]: Validated JSON object containing technical diagnosis.
        """
        api_key = getattr(settings, 'GEMINI_API_KEY', '')

        if not api_key:
            logger.warning("GEMINI_API_KEY tidak dikonfigurasi. Menggunakan diagnosis fallback.")
            return cls._generate_fallback_diagnosis(complaint_text)

        candidate_models = ['gemini-2.0-flash', 'gemini-1.5-flash-latest', 'gemini-2.5-flash', 'gemini-pro']

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)

            response = None
            last_error = None
            for model_name in candidate_models:
                try:
                    model = genai.GenerativeModel(model_name)
                    prompt = f"{cls.SYSTEM_PROMPT}\n\nKeluhan Pengguna: \"{complaint_text}\""
                    response = model.generate_content(prompt)
                    if response and response.text:
                        break
                except Exception as e:
                    last_error = e
                    continue

            if not response or not response.text:
                raise RuntimeError(f"Tidak ada model Gemini yang dapat diakses. Error terakhir: {last_error}")

            raw_text = response.text.strip()

            # Clean potential markdown block formatting
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

            data = json.loads(raw_text)

            # Validate mandatory keys
            required_keys = ["possible_issues", "danger_level", "recommended_tools", "recommended_parts", "summary"]
            for key in required_keys:
                if key not in data:
                    raise ValueError(f"Kunci wajib '{key}' tidak ditemukan pada output Gemini.")

            return data

        except Exception as exc:
            logger.warning(f"Gagal memproses Gemini AI Triage ({str(exc)}). Menggunakan fallback diagnosis.")
            return cls._generate_fallback_diagnosis(complaint_text)

    @staticmethod
    def _generate_fallback_diagnosis(complaint_text: str) -> Dict[str, Any]:
        """
        Generates structured fallback JSON when Gemini API is unavailable.
        """
        return {
            "possible_issues": ["Pemeriksaan Kendala Otomotif Umum"],
            "danger_level": "MEDIUM",
            "recommended_tools": ["Kotak Alat Mekanik Standar", "Senter", "Multitester"],
            "recommended_parts": ["Suku Cadang Umum / Busi / Sekring"],
            "summary": f"Diagnosis otomatis sementara untuk keluhan: '{complaint_text}'. Mekanik akan melakukan inspeksi fisik langsung di lokasi."
        }
