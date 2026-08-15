# PRJ: Perancangan & Rekonsiliasi Project Mage AI

## 1. Informasi Proyek
- **Nama Proyek:** Project Mage AI (DANA Data Engineer Intern Portfolio)
- **Tujuan:** Membangun end-to-end Data Engineering pipeline menggunakan arsitektur Medallion (Pure Batch Processing) dengan ekosistem Hadoop, Spark, Hive, Airflow, dan mengintegrasikan Autonomous DataOps menggunakan CrewAI.
- **Dataset:** Home Credit Default Risk (10 file CSV).
- **Metodologi Eksekusi:** Feature-by-Feature Validation. Setiap fase harus melalui tahap rekonsiliasi dan testing (Input -> Proses -> Expected Output). Kegagalan pada satu fase akan menghentikan progres ke fase berikutnya hingga isu terselesaikan.

---

## 2. Fase 1: Setup Infrastruktur & Environment (Docker)

### 2.1. Spesifikasi Fitur
Membangun klaster infrastruktur data lokal secara terisolasi menggunakan Docker Compose.

### 2.2. Task Checklist
- [x] Membuat direktori proyek dan inisialisasi Git repository lokal.
- [x] Menyusun `docker-compose.yml` untuk komponen berikut:
  - [x] Hadoop Cluster (NameNode, DataNode).
  - [x] Apache Hive (Hive Metastore, HiveServer2, PostgreSQL backend untuk Metastore).
  - [x] Apache Spark (Spark Master, Spark Worker).
  - [x] Apache Airflow (Webserver, Scheduler, Worker, PostgreSQL backend).
  - [x] OpenSearch (Single-node cluster untuk sentralisasi log).
  - [x] Jaringan internal Docker (bridge network) agar semua layanan saling terhubung.
- [x] Konfigurasi volume Docker untuk persistensi data HDFS dan database relasional.
- [x] Mengeksekusi instruksi `docker-compose up -d`.

### 2.3. Rekonsiliasi & Testing (Fase 1)
- **Input:** Perintah eksekusi `docker-compose up -d`.
- **Expected Output:** 
  - Seluruh container berstatus `Up` dan `Healthy`.
  - Airflow Web UI dapat diakses (HTTP 200).
  - Spark Master UI dapat diakses.
  - HDFS Web UI dapat diakses.
  - HiveServer2 menerima koneksi via Beeline/JDBC.
- **Kriteria Validasi:**
  - [PASS] Akses Airflow UI sukses.
  - [PASS] Cek status HDFS NameNode aktif dan memiliki kapasitas storage.
  - [PASS] Tes koneksi JDBC ke HiveServer2 berhasil.
- **Status Eksekusi:** [ ] PASS / [ ] FAIL

---

## 3. Fase 2: Layer Bronze (Raw Data Ingestion)

### 3.1. Spesifikasi Fitur
Menelan (ingest) data statis (10 CSV Home Credit) dari sumber lokal ke Hadoop Distributed File System (HDFS) menggunakan Apache Airflow tanpa mengubah struktur data.

### 3.2. Task Checklist
- [x] Membuat direktori HDFS `/data/bronze/home_credit/raw/`.
- [x] Membuat struktur folder DAGs pada direktori Airflow.
- [x] Menulis file `dag_bronze_ingestion.py`.
  - [x] Mendefinisikan task ekstraksi 10 file CSV.
  - [x] Mendefinisikan task pemindahan file ke HDFS menggunakan hook/operator WebHDFS atau bash command.
- [x] Melakukan deploy DAG ke Airflow dan memicu eksekusi manual (trigger DAG).

### 3.3. Rekonsiliasi & Testing (Fase 2)
- **Input:** 10 file CSV pada sistem lokal. Eksekusi DAG `dag_bronze_ingestion`.
- **Expected Output:** DAG berstatus `Success`. 10 file CSV berada persis di path HDFS `/data/bronze/home_credit/raw/` dengan ukuran file (byte) yang identik dengan sumber.
- **Kriteria Validasi:**
  - [x] Status Airflow DAG: Success.
  - [x] Eksekusi perintah `hdfs dfs -ls /data/bronze/home_credit/raw/` menampilkan 10 file.
  - [x] Pengecekan ukuran file sumber vs ukuran file di HDFS (Checksum matching).
- **Status Eksekusi:** [ ] PASS / [ ] FAIL

---

## 4. Fase 3: Layer Silver (Data Cleansing, Feature Engineering, Integration & Quality Assurance)

### 4.1. Spesifikasi Fitur
Membaca data mentah dari Layer Bronze (10 file CSV Home Credit), melakukan pembersihan data, standarisasi tipe data, **membuat fitur agregat dari tabel pendukung (bureau, previous_application, dll.) yang relevan untuk analisis risiko kredit**, menggabungkan semua fitur tersebut ke dalam satu tabel terintegrasi per aplikasi (`SK_ID_CURR`), memvalidasi integritas dan kualitas data dengan Great Expectations, dan menyimpan hasil akhir dalam format Parquet di HDFS.  
Tabel terintegrasi ini akan menjadi dasar bagi **Dashboard Portfolio Risk Monitoring** (Fase 4 Gold) dan **pemodelan machine learning**.

### 4.2. Task Checklist
- [x] **A. Persiapan & Analisis Data**  
  - [x] Memahami kamus data (`HomeCredit_columns_description.csv`) dan menentukan kolom penting.  
  - [x] Menentukan daftar fitur agregat yang akan dibuat dari setiap tabel pendukung (contoh: jumlah kredit aktif, rata‑rata tunggakan, utilisasi kartu kredit, dll.) sesuai kebutuhan dashboard dan prediksi.  
  - [x] Menentukan primary key setiap tabel (`SK_ID_CURR`, `SK_ID_BUREAU`, `SK_ID_PREV`) untuk proses join.

- [x] **B. Menulis skrip PySpark `silver_cleaning.py` (Pembersihan & Standarisasi)**  
  - [x] Logika pembacaan CSV dari `/data/bronze/home_credit/raw/`.  
  - [x] Konversi kolom hari negatif: `DAYS_BIRTH` → `AGE_YEARS`, `DAYS_EMPLOYED` → `YEARS_EMPLOYED` (tangani nilai khusus 365243 sebagai *unemployed*).  
  - [x] Penanganan nilai *missing*: imputasi median untuk numerik, mode/“Unknown” untuk kategorikal, atau drop kolom dengan missing > threshold.  
  - [x] Deduplikasi berdasarkan primary key masing‑masing tabel.  
  - [x] Pembersihan serupa untuk tabel pendukung (`bureau`, `previous_application`, dll.).

- [x] **C. Menulis skrip PySpark `silver_feature_engineering.py` (Agregasi & Fitur Baru)**  
  - [x] Untuk setiap tabel pendukung (`bureau`, `bureau_balance`, `previous_application`, `POS_CASH_balance`, `installments_payments`, `credit_card_balance`):  
     - [x] Menghitung fitur agregat pada level `SK_ID_CURR` (contoh: `BUREAU_ACTIVE_CNT`, `PREV_APPROVED_CNT`, `INSTAL_AVG_PAYMENT_RATIO`, `CC_AVG_UTILIZATION`, dll.).  
     - [x] Menyimpan DataFrame agregat sementara.  
  - [x] Membuat fitur tambahan dari tabel utama (`application_train`/`test`) jika diperlukan (misal: `INCOME_CREDIT_RATIO`, `ANNUITY_INCOME_RATIO`, `AGE_GROUP`, dll.).

- [x] **D. Menulis skrip PySpark `silver_integration.py` (Integrasi)**  
  - [x] Membaca tabel utama yang sudah bersih (`application_train_clean`, `application_test_clean`).  
  - [x] Melakukan **left join** dengan seluruh DataFrame agregat menggunakan kunci `SK_ID_CURR`.  
  - [x] Menghasilkan dua tabel terintegrasi: `train_integrated` (dengan label `TARGET`) dan `test_integrated` (tanpa label).  
  - [x] Validasi jumlah baris setelah join (tidak boleh bertambah/berkurang).

- [x] **E. Konfigurasi Great Expectations (GE)**  
  - [x] Membuat Expectation Suite untuk tabel terintegrasi, minimal:  
     - [x] `expect_column_values_to_not_be_null("SK_ID_CURR")`  
     - [x] `expect_column_values_to_be_unique("SK_ID_CURR")`  
     - [x] Untuk `train_integrated`: `expect_column_values_to_be_in_set("TARGET", [0,1])`  
     - [x] `expect_column_values_to_be_between` untuk kolom numerik penting (misal `AGE_YEARS` antara 18–100).  
  - [x] Menjalankan validasi GE dan menghasilkan Data Docs (HTML laporan).

- [x] **F. Menyimpan Data Lolos Validasi**  
  - [x] Menulis `train_integrated` dan `test_integrated` ke HDFS path `/data/silver/home_credit/integrated/` dalam format Parquet.  
  - [x] Menyimpan laporan GE sebagai artefak.

- [x] **G. Membuat DAG Airflow `dag_silver_processing.py`**  
  - [x] Dependensi: menunggu DAG Bronze sukses.  
  - [x] Task paralel: cleaning per tabel, lalu agregasi per tabel pendukung.  
  - [x] Task integrasi dan validasi GE setelah semua agregasi selesai.  
  - [x] Menggunakan `SparkSubmitOperator` atau `BashOperator` dengan `spark-submit`.  

### 4.3. Rekonsiliasi & Testing (Fase 3)
- **Input:**  
  - 10 file CSV mentah di Layer Bronze.  
  - Trigger DAG `dag_silver_processing` (atau eksekusi bertahap manual).

- **Expected Output:**  
  - Log PySpark menunjukkan seluruh tahap (cleaning, agregasi, integrasi) selesai tanpa error.  
  - Validasi GE mengembalikan status **Success** untuk semua expectation yang ditentukan.  
  - File `train_integrated.parquet` dan `test_integrated.parquet` terbentuk di `/data/silver/home_credit/integrated/`.  
  - Jumlah baris `train_integrated` sama dengan `application_train.csv` awal (setelah dedup).  
  - Laporan GE Data Docs tersimpan dan dapat diakses.

- **Kriteria Validasi:**
  - [x] Semua tabel berhasil dibersihkan dan tidak ada duplikat pada primary key.  
  - [x] Kolom hasil konversi hari (misal `AGE_YEARS`, `YEARS_EMPLOYED`) bertipe numerik positif.  
  - [x] Jumlah fitur agregat sesuai dengan daftar yang direncanakan (minimal 5 fitur per tabel pendukung).  
  - [x] Tabel terintegrasi dapat dibaca oleh PySpark dan menampilkan skema yang benar (termasuk kolom agregat).  
  - [x] Query sederhana di PySpark shell menunjukkan bahwa `SK_ID_CURR` unik dan `TARGET` hanya bernilai 0/1.  
  - [x] Laporan Great Expectations Data Docs menunjukkan **100% Passed** untuk semua expectation.  
  - [x] Perintah `hdfs dfs -ls /data/silver/home_credit/integrated/` menampilkan file Parquet.

- **Status Eksekusi:** [ ] PASS / [ ] FAIL

## 5. Fase 4: Layer Gold (Aggregation & Data Warehouse Hive)

### 5.1. Spesifikasi Fitur
Melakukan agregasi metrik dari tabel kardinalitas N (contoh: `bureau_balance`, `installments_payments`) dan menggabungkannya ke tabel utama (`application`). Menyimpan hasil akhir (Feature Store) ke dalam tabel Apache Hive.

### 5.2. Task Checklist
- [x] Menulis skrip PySpark `job_gold_aggregation.py`.
  - [x] Logika aggregasi `bureau_balance` (GROUP BY `SK_ID_BUREAU`).
  - [x] Logika aggregasi `installments_payments` (GROUP BY `SK_ID_CURR`).
  - [x] Logika JOIN seluruh hasil aggregasi dengan tabel dimensi utama.
- [x] Menulis logika PySpark untuk memuat DataFrame akhir ke Apache Hive (menggunakan `saveAsTable` atau konektivitas JDBC ke HiveServer2).
- [x] Membuat `dag_gold_aggregation.py` di Airflow (dependen pada DAG Silver).

### 5.3. Rekonsiliasi & Testing (Fase 4)
- **Input:** File Parquet di Layer Silver. Trigger DAG `dag_gold_aggregation`.
- **Expected Output:** DataFrame gabungan berhasil dihitung. Hive Metastore mencatat tabel baru. Data agregat dapat di-query menggunakan HiveQL.
- **Kriteria Validasi:**
  - [x] PySpark job selesai tanpa error Memory/OOM.
  - [x] Eksekusi kueri via Beeline: `SELECT * FROM default.home_credit_gold LIMIT 5;` mengembalikan hasil yang valid.
  - [x] Validasi perhitungan agregasi (misal: verifikasi nilai total pinjaman sesuai dengan kalkulasi manual pada sampel kecil).
- **Status Eksekusi:** [ ] PASS / [ ] FAIL

---

## 6. Fase 5: Autonomous DataOps (CrewAI Integration)

### 6.1. Spesifikasi Fitur
Mendeploy daemon service Python berbasis CrewAI untuk menangani Schema Evolution, Auto-remediasi Log, dan Pembuatan Dokumentasi secara otonom.

### 6.2. Task Checklist
- [ ] Menulis skrip `crewai_dataops_daemon.py`.
- [ ] Mengonfigurasi Agent 1 (Schema Evolution Observer):
  - [ ] Menulis custom tool untuk membandingkan skema HDFS Bronze terbaru dengan skema yang terdaftar.
  - [ ] Menulis logika untuk update file JSON Great Expectations jika ada kolom baru.
- [ ] Mengonfigurasi Agent 2 (Incident Response Specialist):
  - [ ] Menulis custom tool untuk kueri ke OpenSearch API mengambil log Airflow berstatus ERROR.
  - [ ] Mengintegrasikan library GitPython untuk melakukan commit otomatis terhadap patch yang dihasilkan LLM.
- [ ] Mengonfigurasi Agent 3 (Data Steward):
  - [ ] Menulis custom tool untuk koneksi ke Hive Metastore JDBC.
  - [ ] Mengekstrak metadata dan membuat file Markdown statis.
- [ ] Menjadwalkan/memicu daemon ini pada Airflow (misalnya melalui DAG khusus yang dijalankan pada akhir seluruh pipeline).

### 6.3. Rekonsiliasi & Testing (Fase 5)
Skenario ini akan dites satu per satu dengan simulasi.

#### Skenario 5A: Schema Evolution Test
- **Input:** Memasukkan file CSV dummy ke direktori Bronze dengan tambahan satu kolom baru `NEW_FEATURE_COL`.
- **Expected Output:** Agent 1 mendeteksi kolom, mengedit file JSON GE secara otomatis, dan mencatat aktivitas di log CrewAI.
- **Kriteria Validasi:** [ ] File JSON GE berubah.
- **Status Eksekusi:** [ ] PASS / [ ] FAIL

#### Skenario 5B: Incident Response Test
- **Input:** Mematikan paksa salah satu DataNode atau menyisipkan sintaks error pada script PySpark, lalu menjalankan DAG.
- **Expected Output:** Airflow DAG Gagal. Log error masuk ke OpenSearch. Agent 2 membaca log, menganalisis stack trace, dan menghasilkan branch Git baru berisi usulan perbaikan.
- **Kriteria Validasi:** [ ] Pull Request/Branch baru muncul di repositori Git dengan detail error.
- **Status Eksekusi:** [ ] PASS / [ ] FAIL

#### Skenario 5C: Documentation Update Test
- **Input:** Trigger Agent 3 setelah tabel Gold berhasil dikonfigurasi di Hive.
- **Expected Output:** File `DATA_DICTIONARY.md` tercipta atau terupdate di repositori proyek.
- **Kriteria Validasi:** [ ] File `DATA_DICTIONARY.md` di repositori mencantumkan seluruh kolom yang sesuai dengan skema Hive tabel Gold terakhir.
- **Status Eksekusi:** [ ] PASS / [ ] FAIL