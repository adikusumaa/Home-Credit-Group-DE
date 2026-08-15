from crewai import Task
from .agents import analyst, engineer, reviewer

task_analyze = Task(
    description="""
    1. Ambil log error dari DAG yang gagal menggunakan tool `fetch_airflow_error_logs`.
    2. Jika tool gagal, JANGAN mengarang. Laporkan 'Gagal mengambil log' dan berhenti.
    3. Periksa apa pun error yang muncul di log (misal: SyntaxError, Column not found, OutOfMemoryError, FileNotFoundError, dll).
    4. Berikan rekomendasi singkat (1 paragraf) tentang file mana yang harus diubah dan mengapa.
    Catatan: file yang sering bermasalah adalah dags/dag_silver_processing.py atau script di /opt/jobs/pyspark/.
    """,
    expected_output="Laporan singkat: 'Error ditemukan di file X karena Y' ATAU 'Gagal mengambil log: ...'",
    agent=analyst
)

task_fix = Task(
    description="""Berdasarkan laporan dari Analyst, perbaiki file yang bermasalah.

**LANGKAH WAJIB (tidak boleh dilewati):**
1. Panggil tool `read_file` dengan `file_path` yang disebutkan Analyst (contoh: '/opt/jobs/pyspark/application_s.py') untuk mendapatkan isi file asli.
2. **JANGAN menulis ulang seluruh file.** Hanya hapus atau perbaiki baris yang menyebabkan error.
3. **PERTAHANKAN SEMUA logika bisnis asli.** Jangan menambahkan logic baru, jangan menghapus fungsi/transformasi lain.
4. Hasil akhir harus merupakan file asli dengan hanya perubahan minimal pada bagian yang error.
5. Setelah selesai, panggil tool `create_git_branch_with_patch_and_pr` dengan DUA argumen:
   - `file_path`: path file yang diperbaiki
   - `patch_content`: isi file lengkap (asli + perbaikan minimal)

**CONTOH INPUT/OUTPUT:**
- Input file asli: 100 baris berisi business logic.
- Error: SyntaxError di baris 188 (misal `SELECT * FROM DBDUELIST;`)
- Output patch_content: **file asli 100 baris tersebut** dengan baris `SELECT * FROM DBDUELIST;` dihapus/diperbaiki. JANGAN menulis file pendek 20 baris.

Tool `create_git_branch_with_patch_and_pr` akan **menolak** patch jika `patch_content` lebih pendek dari 80% file asli. Jadi kamu wajib membaca file asli terlebih dahulu.

Jika laporan Analyst tidak menyebutkan error spesifik, jawab 'TIDAK ADA PERBAIKAN' dan jangan panggil tool apa pun.
""",
    expected_output="Full content file yang sudah diperbaiki (bukan hanya potongan).",
    agent=engineer,
    context=[task_analyze]
)

task_review = Task(
    description="""Review hasil patch dari Engineer.
    Jika Engineer menjawab 'TIDAK ADA PERBAIKAN', setujui dengan alasan 'Tidak ada perbaikan yang diperlukan'.
    Jika ada patch, periksa apakah kode aman dan tidak ada syntax error.
    Berikan status APPROVED atau REJECTED.
    JANGAN memanggil tool GitPatchTool lagi, karena Engineer sudah membuat PR.
    """,
    expected_output="Status: 'APPROVED' atau 'REJECTED' beserta alasan singkat.",
    agent=reviewer,
    context=[task_fix]
)