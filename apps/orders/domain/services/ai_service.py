"""
AI Triage Domain Service.
Integrates with Google Gemini API to analyze raw customer vehicle complaints and generate structured technical diagnosis JSON.
Includes strict domain guardrails to reject non-automotive inputs (e.g. food, medical, general chat).
"""
import json
import logging
from typing import Dict, Any
# pyrefly: ignore [missing-import]
from django.conf import settings
# pyrefly: ignore [missing-import]
import google.generativeai as genai

logger = logging.getLogger(__name__)


class AITriageService:
    """
    Service class for Google Gemini AI Triage Engine with Automotive Domain Guardrails.
    """

    SYSTEM_PROMPT = """
Anda adalah Master Mekanik Otomotif AI senior untuk sistem penanganan darurat kendaraan OtoGrid.
Tugas Anda HANYA menganalisis keluhan tentang kendala teknis, perbaikan, dan kerusakan kendaraan otomotif (Sepeda Motor, Mobil, Truk, Bus).

INSTRUKSI PENATAN DOMAIN MANDATORI:
1. Evaluasi apakah keluhan pengguna BERHUBUNGAN DENGAN KENDARAAN OTOMOTIF (mesin, kelistrikan, transmisi, rem, ban, oli, bodi, suara aneh kendaraan, mogok, dsb).
2. JIKA INPUT TIDAK BERHUBUNGAN DENGAN OTOMOTIF (misalnya tentang makanan, memasak, resep, kesehatan manusia, percakapan umum, komputasi, kuis, atau hal non-otomotif lainnya):
   Anda WAJIB mengembalikan JSON berikut:
   {
     "is_valid_automotive": false,
     "category": "Input Luar Domain Otomotif",
     "estimated_duration": "-",
     "complexity": "-",
     "danger_level": "LOW",
     "possible_issues": [
       "Input tidak terdeteksi sebagai keluhan/kendala teknis kendaraan."
     ],
     "action_steps": [
       "Mohon masukkan deskripsi kendala teknis kendaraan (contoh: mesin mati, rem bunyi, aki drop, matic gredeg)."
     ],
     "recommended_tools": [],
     "recommended_parts": [],
     "summary": "Maaf, AI Triage Engine OtoGrid khusus dirancang hanya untuk mendiagnosa kerusakan dan kendala teknis kendaraan otomotif. Input yang Anda masukkan tidak berkaitan dengan perbaikan kendaraan."
   }

3. JIKA INPUT ADALAH KELUHAN OTOMOTIF VALID, berikan output JSON dengan format:
{
  "is_valid_automotive": true,
  "category": "Sistem Terpengaruh (contoh: Mesin & Penggerak, Kelistrikan & Pengapian, Rem & Suspensi, Transmisi CVT)",
  "estimated_duration": "Estimasi durasi pengerjaan (contoh: 30 - 45 Menit)",
  "complexity": "RINGAN|SEDANG|RUMIT",
  "danger_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "possible_issues": [
    "Penjelasan spesifik masalah 1",
    "Penjelasan spesifik masalah 2"
  ],
  "action_steps": [
    "Langkah penanganan teknis 1",
    "Langkah penanganan teknis 2"
  ],
  "recommended_tools": [
    "Alat 1 yang wajib dibawa mekanik"
  ],
  "recommended_parts": [
    "Suku cadang 1"
  ],
  "summary": "Ringkasan teknis komprehensif 2-3 kalimat mengenai masalah kendaraan."
}

Berikan output HANYA dalam format JSON yang valid tanpa teks tambahan.
"""

    NON_AUTOMOTIVE_KEYWORDS = [
        'makanan', 'makan', 'minuman', 'minum', 'resep', 'masak', 'nasi', 'kue', 'roti',
        'baju', 'celana', 'sekolah', 'kucing', 'anjing', 'dokter', 'obat', 'sakit kepala',
        'laptop', 'hp', 'handphone', 'game', 'film', 'lagu', 'musik', 'cinta', 'pacar',
        'skripsi', 'tugas', 'presiden', 'politik', 'uang', 'pinjol', 'crypto'
    ]

    @classmethod
    def diagnose_complaint(cls, complaint_text: str) -> Dict[str, Any]:
        """
        Invokes Gemini API with hidden System Prompt to analyze vehicle complaint.

        Args:
            complaint_text (str): Raw user description of breakdown.

        Returns:
            Dict[str, Any]: Validated JSON object containing technical diagnosis.
        """
        text_lower = complaint_text.lower().strip()

        # Direct domain validation check for obvious non-automotive keywords
        if any(kw in text_lower for kw in cls.NON_AUTOMOTIVE_KEYWORDS):
            logger.info(f"Input '{complaint_text}' terdeteksi luar domain otomotif via keyword filter.")
            return cls._generate_non_automotive_response(complaint_text)

        api_key = getattr(settings, 'GEMINI_API_KEY', '')

        if not api_key:
            logger.warning("GEMINI_API_KEY tidak dikonfigurasi. Menggunakan diagnosis fallback cerdas.")
            return cls._generate_fallback_diagnosis(complaint_text)

        candidate_models = [
            'gemini-flash-latest',
            'gemini-2.0-flash',
            'gemini-2.5-flash',
            'gemini-pro-latest',
            'gemini-flash-lite-latest'
        ]

        try:
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
                raise RuntimeError(f"Semua model Gemini error/limit. Error terakhir: {last_error}")

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

            # Ensure all expected fields are present with safe fallbacks if missing
            defaults = {
                "is_valid_automotive": True,
                "category": "Mesin & Penggerak Otomotif",
                "estimated_duration": "30 - 60 Menit",
                "complexity": "SEDANG",
                "danger_level": "MEDIUM",
                "possible_issues": [f"Analisis kendala teknis pada: '{complaint_text}'"],
                "action_steps": ["Lakukan pemeriksaan fisik komprehensif oleh mekanik di lokasi."],
                "recommended_tools": ["Kotak Alat Mekanik Standar OtoGrid"],
                "recommended_parts": ["Suku Cadang Sesuai Hasil Inspeksi"],
                "summary": f"Hasil analisa AI untuk keluhan: '{complaint_text}'."
            }
            for k, v in defaults.items():
                if k not in data or data[k] is None:
                    data[k] = v

            return data

        except Exception as exc:
            logger.warning(f"Gagal memproses Gemini AI Triage ({str(exc)}). Menggunakan fallback cerdas.")
            return cls._generate_fallback_diagnosis(complaint_text)

    @classmethod
    def _generate_non_automotive_response(cls, complaint_text: str) -> Dict[str, Any]:
        """
        Returns structured rejection JSON for non-automotive inputs.
        """
        return {
            "is_valid_automotive": False,
            "category": "Input Luar Domain Otomotif",
            "estimated_duration": "-",
            "complexity": "-",
            "danger_level": "LOW",
            "possible_issues": [
                f"Input '{complaint_text}' terdeteksi bukan merupakan keluhan atau masalah teknis kendaraan."
            ],
            "action_steps": [
                "Masukkan deskripsi kendala teknis kendaraan spesifik (contoh: 'mesin mati mendadak', 'rem bunyi nyaring', 'aki drop', 'matic gredeg')."
            ],
            "recommended_tools": [],
            "recommended_parts": [],
            "summary": f"Maaf, AI Triage Engine OtoGrid khusus dirancang hanya untuk mendiagnosa kerusakan dan kendala teknis kendaraan otomotif. Input '{complaint_text}' tidak berkaitan dengan sistem atau perbaikan kendaraan."
        }

    @staticmethod
    def _generate_fallback_diagnosis(complaint_text: str) -> Dict[str, Any]:
        """
        Generates dynamic rule-based diagnosis matching complaint keywords when API is unavailable or rate-limited.
        """
        text_lower = complaint_text.lower()

        # Keyword 1: Water / Rain / Flood / Hujan / Menerobos Air
        if any(w in text_lower for w in ['hujan', 'air', 'banjir', 'genangan', 'basah', 'cuci']):
            return {
                "is_valid_automotive": True,
                "category": "Sistem Pengapian & Kelistrikan (Terkontaminasi Air)",
                "estimated_duration": "25 - 45 Menit",
                "complexity": "SEDANG",
                "danger_level": "HIGH",
                "possible_issues": [
                    "Cop busi/cangklong busi kemasukan air menyebabkan kebocoran arus pengapian",
                    "Air terhisap masuk ke dalam box filter udara atau mangkok karburator",
                    "Korsleting singkat pada komponen kelistrikan/relay starter karena lembab"
                ],
                "action_steps": [
                    "Lepaskan cop busi, bersihkan dari sisa air hujan, dan keringkan sebelum dipasang ulang",
                    "Cek stik oli mesin: jika oli berwarna keruh seperti kopi susu, JANGAN nyalakan mesin",
                    "Gunakan kick-starter (engkol) 5-10 kali dalam posisi kontak OFF untuk membuang embun"
                ],
                "recommended_tools": [
                    "Kunci Busi Otomotif 16mm/17mm",
                    "Lap Microfiber & Cairan Contact Cleaner",
                    "Kunci Pas Set 8-12mm & Senter LED"
                ],
                "recommended_parts": [
                    "Busi Baru (NGK / Denso)",
                    "Cop Busi Waterproof / Anti-Air",
                    "Oli Mesin Baru (Flushing Oil)"
                ],
                "summary": f"Keluhan '{complaint_text}' mengindikasikan masalah kontaminasi air pada sistem pengapian atau filter udara. Penanganan difokuskan pada pengeringan cop busi dan pengecekan oli agar mesin tidak macet."
            }

        # Keyword 2: Battery / Mati Total / Starter / Aki
        if any(w in text_lower for w in ['aki', 'mati total', 'starter', 'listrik', 'lampu', 'redup', 'spul']):
            return {
                "is_valid_automotive": True,
                "category": "Sistem Kelistrikan & Pengisian (Battery/Aki)",
                "estimated_duration": "20 - 40 Menit",
                "complexity": "RINGAN",
                "danger_level": "HIGH",
                "possible_issues": [
                    "Tegangan Aki (Battery) drop di bawah 12 Volt atau sel aki mati",
                    "Kiprok/Regulator pengisian rusak tidak mensuplai listrik ke aki",
                    "Kabel massa atau terminal aki longgar/teroksidasi"
                ],
                "action_steps": [
                    "Ukur tegangan aki menggunakan Multitester saat kontak ON",
                    "Lakukan Jumper Aki atau ganti aki dengan unit baru yang sesuai spesifikasi",
                    "Periksa kerapatan terminal kabel aki dan bersihkan dari kerak putih"
                ],
                "recommended_tools": [
                    "Digital Multimeter / Battery Tester",
                    "Kabel Jumper Aki Darurat",
                    "Obeng Plus & Kunci Pas 10mm"
                ],
                "recommended_parts": [
                    "Aki Motor GS Astra / Yuasa (12V)",
                    "Sekring / Fuse Tambahan (10A - 25A)",
                    "Cairan Pembersih Terminal Kontak"
                ],
                "summary": f"Keluhan '{complaint_text}' terdeteksi sebagai masalah sistem kelistrikan. Penanganan diutamakan pada pengukuran voltage aki, ketersediaan pengisian kiprok, dan pembersihan terminal arus."
            }

        # Keyword 3: CVT / Matic / Getar / Gredeg / Akselerasi
        if any(w in text_lower for w in ['cvt', 'getar', 'gredeg', 'matic', 'roller', 'vbelt', 'v-belt', 'kopling']):
            return {
                "is_valid_automotive": True,
                "category": "Transmisi Otomatis (CVT & Drive Belt)",
                "estimated_duration": "35 - 50 Menit",
                "complexity": "SEDANG",
                "danger_level": "MEDIUM",
                "possible_issues": [
                    "Mangkok ganda & kampas kopling CVT kotor/terkontaminasi debu dan oli",
                    "Roller CVT aus atau bentuknya sudah tidak bulat presisi",
                    "V-Belt mulai mengalami retak-retak atau keausan"
                ],
                "action_steps": [
                    "Buka blok CVT dan lakukan pembersihan total dari debu & sisa gesekan",
                    "Inspeksi kondisi fisik V-Belt dan ukur ketebalan kampas ganda",
                    "Beri gemuk/grease CVT khusus pada area sliding sheave"
                ],
                "recommended_tools": [
                    "Kunci Impact T-8 / Sok 17 & 22mm",
                    "Tahanan Tracker CVT",
                    "Cairan Brake/CVT Cleaner"
                ],
                "recommended_parts": [
                    "Set Roller CVT Standard",
                    "V-Belt Original Manufacturer",
                    "Kampas Ganda CVT"
                ],
                "summary": f"Keluhan '{complaint_text}' berhubungan dengan komponen CVT transmisi matic. Diperlukan servis pembersihan blok CVT, penggantian roller, atau pembersihan kampas ganda."
            }

        # Keyword 4: Brake / Rem / Bunyi / Blong
        if any(w in text_lower for w in ['rem', 'bunyi', 'blong', 'pad', 'tromol', 'cakram', 'nyaring']):
            return {
                "is_valid_automotive": True,
                "category": "Sistem Pengereman (Brake System)",
                "estimated_duration": "20 - 35 Menit",
                "complexity": "RINGAN",
                "danger_level": "CRITICAL",
                "possible_issues": [
                    "Kampas rem (Brake Pad) sudah tipis dan gesekannya menyentuh piringan cakram",
                    "Minyak rem berkurang atau terdapat gelembung udara pada master rem",
                    "Piringan cakram tergores atau tergelincir akibat minyak/kotoran"
                ],
                "action_steps": [
                    "Periksa ketebalan kampas rem depan dan belakang",
                    "Ganti kampas rem baru dan lakukan bleeding angin minyak rem",
                    "Bersihkan piringan cakram menggunakan cairan degreaser"
                ],
                "recommended_tools": [
                    "Kunci L Bintang & Kunci Pas 8-10mm",
                    "Obeng Min & Penekan Piston Kaliper",
                    "Cairan Brake Cleaner"
                ],
                "recommended_parts": [
                    "Kampas Rem Depan/Belakang (Brake Pad)",
                    "Minyak Rem DOT 3 / DOT 4",
                    "Piringan Cakram (jika aus parah)"
                ],
                "summary": f"Keluhan '{complaint_text}' tergolong kritikal pada sistem pengereman. Penanganan utama mencakup penggantian kampas rem dan pembersihan permukaan piringan cakram."
            }

        # Default Fallback for generic complaints
        return {
            "is_valid_automotive": True,
            "category": "Inspeksi Mesin & Penggerak Utama",
            "estimated_duration": "30 - 45 Menit",
            "complexity": "SEDANG",
            "danger_level": "MEDIUM",
            "possible_issues": [
                f"Indikasi gangguan mekanis atau kelistrikan pada: '{complaint_text}'",
                "Potensi kelonggaran pada komponen bergerak atau sistem suplai bahan bakar",
                "Penurunan performa akibat keausan pemakaian rutin"
            ],
            "action_steps": [
                "Lakukan tes hidupkan mesin dan amati indikator kode error pada spidometer",
                "Periksa volume dan kondisi oli mesin serta ketersediaan bahan bakar",
                "Lakukan penanganan awal oleh mekanik OtoGrid langsung di lokasi"
            ],
            "recommended_tools": [
                "Kotak Kunci Pas & Sok Set Lengkap",
                "Diagnostic Scanner / Multitester",
                "Senter LED Inspeksi"
            ],
            "recommended_parts": [
                "Busi & Sekring Otomotif",
                "Oli Mesin & Pelumas Rantai",
                "Suku Cadang Spesifik Hasil Inspeksi"
            ],
            "summary": f"Analisa teknis untuk keluhan: '{complaint_text}'. Mekanik OtoGrid akan melakukan inspeksi fisik komprehensif di lokasi untuk memverifikasi sumber masalah dan melakukan perbaikan."
        }
