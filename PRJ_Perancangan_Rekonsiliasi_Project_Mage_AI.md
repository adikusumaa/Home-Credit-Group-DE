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
  - [ ] Akses Airflow UI sukses.
  - [ ] Cek status HDFS NameNode aktif dan memiliki kapasitas storage.
  - [ ] Tes koneksi JDBC ke HiveServer2 berhasil.
- **Status Eksekusi:** [ ] PASS / [ ] FAIL

---

## 3. Fase 2: Layer Bronze (Raw Data Ingestion)

### 3.1. Spesifikasi Fitur
Menelan (ingest) data statis (10 CSV Home Credit) dari sumber lokal ke Hadoop Distributed File System (HDFS) menggunakan Apache Airflow tanpa mengubah struktur data.

### 3.2. Task Checklist
- [ ] Membuat direktori HDFS `/data/bronze/home_credit/raw/`.
- [ ] Membuat struktur folder DAGs pada direktori Airflow.
- [ ] Menulis file `dag_bronze_ingestion.py`.
  - [ ] Mendefinisikan task ekstraksi 10 file CSV.
  - [ ] Mendefinisikan task pemindahan file ke HDFS menggunakan hook/operator WebHDFS atau bash command.
- [ ] Melakukan deploy DAG ke Airflow dan memicu eksekusi manual (trigger DAG).

### 3.3. Rekonsiliasi & Testing (Fase 2)
- **Input:** 10 file CSV pada sistem lokal. Eksekusi DAG `dag_bronze_ingestion`.
- **Expected Output:** DAG berstatus `Success`. 10 file CSV berada persis di path HDFS `/data/bronze/home_credit/raw/` dengan ukuran file (byte) yang identik dengan sumber.
- **Kriteria Validasi:**
  - [ ] Status Airflow DAG: Success.
  - [ ] Eksekusi perintah `hdfs dfs -ls /data/bronze/home_credit/raw/` menampilkan 10 file.
  - [ ] Pengecekan ukuran file sumber vs ukuran file di HDFS (Checksum matching).
- **Status Eksekusi:** [ ] PASS / [ ] FAIL

---

## 4. Fase 3: Layer Silver (Data Cleansing & Quality Assurance)

### 4.1. Spesifikasi Fitur
Membaca data dari Layer Bronze, melakukan transformasi (pembersihan data, standardisasi), memvalidasi integritas data dengan Great Expectations, dan menyimpannya dalam format Parquet di HDFS.

### 4.2. Task Checklist
- [ ] Menulis skrip PySpark `job_silver_transformation.py`.
  - [ ] Logika pembacaan CSV dari `/data/bronze/...`.
  - [ ] Logika transformasi: Konversi integer negatif pada `DAYS_BIRTH`, `DAYS_EMPLOYED` menjadi date format.
  - [ ] Logika transformasi: Penanganan nilai Null dan de-duplikasi baris.
- [ ] Mengonfigurasi suite Great Expectations (GE) di dalam PySpark.
  - [ ] Mendefinisikan aturan: `SK_ID_CURR` not null, unique.
  - [ ] Mendefinisikan aturan: Kolom target pada rentang 0 atau 1.
- [ ] Menulis logika PySpark untuk menyimpan data yang lolos validasi ke `/data/silver/home_credit/cleaned/` dengan format Parquet.
- [ ] Membuat `dag_silver_processing.py` di Airflow (dependen pada DAG Bronze) untuk mengeksekusi PySpark job.

### 4.3. Rekonsiliasi & Testing (Fase 3)
- **Input:** Raw CSV di Layer Bronze. Trigger DAG `dag_silver_processing`.
- **Expected Output:** Log PySpark menunjukkan transformasi selesai. Validasi GE mengembalikan status `Success`. File berekstensi `.parquet` terbentuk di direktori Silver HDFS.
- **Kriteria Validasi:**
  - [ ] Laporan Great Expectations Data Docs terbentuk dan 100% Passed.
  - [ ] Perintah `hdfs dfs -ls /data/silver/home_credit/cleaned/` menampilkan file Parquet.
  - [ ] Pembacaan sampel `.parquet` menggunakan PySpark shell menunjukkan tipe data tanggal telah berubah dan data duplikat hilang.
- **Status Eksekusi:** [ ] PASS / [ ] FAIL

---

## 5. Fase 4: Layer Gold (Aggregation & Data Warehouse Hive)

### 5.1. Spesifikasi Fitur
Melakukan agregasi metrik dari tabel kardinalitas N (contoh: `bureau_balance`, `installments_payments`) dan menggabungkannya ke tabel utama (`application`). Menyimpan hasil akhir (Feature Store) ke dalam tabel Apache Hive.

### 5.2. Task Checklist
- [ ] Menulis skrip PySpark `job_gold_aggregation.py`.
  - [ ] Logika aggregasi `bureau_balance` (GROUP BY `SK_ID_BUREAU`).
  - [ ] Logika aggregasi `installments_payments` (GROUP BY `SK_ID_CURR`).
  - [ ] Logika JOIN seluruh hasil aggregasi dengan tabel dimensi utama.
- [ ] Menulis logika PySpark untuk memuat DataFrame akhir ke Apache Hive (menggunakan `saveAsTable` atau konektivitas JDBC ke HiveServer2).
- [ ] Membuat `dag_gold_aggregation.py` di Airflow (dependen pada DAG Silver).

### 5.3. Rekonsiliasi & Testing (Fase 4)
- **Input:** File Parquet di Layer Silver. Trigger DAG `dag_gold_aggregation`.
- **Expected Output:** DataFrame gabungan berhasil dihitung. Hive Metastore mencatat tabel baru. Data agregat dapat di-query menggunakan HiveQL.
- **Kriteria Validasi:**
  - [ ] PySpark job selesai tanpa error Memory/OOM.
  - [ ] Eksekusi kueri via Beeline: `SELECT * FROM default.home_credit_gold LIMIT 5;` mengembalikan hasil yang valid.
  - [ ] Validasi perhitungan agregasi (misal: verifikasi nilai total pinjaman sesuai dengan kalkulasi manual pada sampel kecil).
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
