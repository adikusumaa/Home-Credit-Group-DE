# 🏗️ Project Mage AI - Data Engineering Pipeline for Home Credit Risk

[![Docker](https://img.shields.io/badge/Docker-24.0+-blue.svg)](https://www.docker.com/) [![Apache Spark](https://img.shields.io/badge/Spark-3.4+-orange.svg)](https://spark.apache.org/) [![Apache Airflow](https://img.shields.io/badge/Airflow-2.7+-green.svg)](https://airflow.apache.org/) [![Hadoop](https://img.shields.io/badge/Hadoop-3.3+-yellow.svg)](https://hadoop.apache.org/) [![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/) [![Status](https://img.shields.io/badge/Status-Completed-brightgreen.svg)]()

**Project Mage AI** adalah implementasi end-to-end Data Engineering pipeline untuk Portfolio DANA Data Engineer Intern. Proyek ini membangun arsitektur data modern menggunakan **Medallion Architecture** (Bronze → Silver → Gold) dengan ekosistem Big Data (Hadoop, Spark, Hive, Airflow) serta mengintegrasikan **Autonomous DataOps** menggunakan CrewAI untuk schema evolution, auto-remediasi, dan dokumentasi otomatis.

Dataset yang digunakan adalah **Home Credit Default Risk** (10 file CSV) dengan total > 1 juta baris data. Pipeline ini dirancang dengan pendekatan **Feature-by-Feature Validation**, di mana setiap fase harus melalui proses rekonsiliasi dan testing ketat sebelum melanjutkan ke fase berikutnya.

![Arsitektur Pipeline](img/Data%20Engineer%20AI.png)
*Arsitektur Data Lake dengan Hadoop, Spark, Hive, dan Airflow*
![Home Credit](data/home_credit.png)
*Data Table Info*

---

## ✨ Fitur Utama
- 🗄️ **Layer Bronze (Raw Ingestion)**: Ingest 10 file CSV statis ke HDFS tanpa modifikasi menggunakan Apache Airflow DAG dengan verifikasi checksum.
- 🧹 **Layer Silver (Cleansing & Feature Engineering)**:
  - Pembersihan data (handling missing values, konversi tipe data, deduplikasi)
  - Feature engineering agregat dari 6 tabel pendukung
  - Integrasi seluruh fitur ke tabel master per aplikasi (`SK_ID_CURR`)
  - Quality Assurance dengan **Great Expectations**
- 📊 **Layer Gold (Data Warehouse)**: Agregasi metrik dan penyimpanan final ke **Apache Hive** untuk dashboard risk monitoring dan ML modeling.
- 🤖 **Autonomous DataOps (CrewAI)** — **Fase 5 Selesai**:
  - **Agent Analyst**: Menganalisis error log dari OpenSearch, mendeteksi Schema Drift atau OOM.
  - **Agent Engineer**: Menghasilkan kode patch (perbaikan) dengan PySpark, menambahkan handling kolom hilang.
  - **Agent Reviewer**: Meninjau kode patch, memastikan keamanan data (tidak ada `overwrite` berbahaya) dan memutuskan APPROVED/REJECTED.
  - **GitPatchTool**: Membuat branch baru, melakukan commit, push ke GitHub, dan membuka Pull Request secara otomatis.
  - **Hasil**: Branch `fix/incident-*` dan PR telah berhasil dibuat untuk error `dag_silver_processing` (Schema Drift).
- 🐳 **Infrastruktur Terisolasi**: Full Docker Compose cluster dengan 10+ layanan (Hadoop, Hive, Spark, Airflow, OpenSearch).

---

## 🛠️ Teknologi yang Digunakan (Tech Stack)
Proyek ini menggunakan arsitektur **Monorepo** terisolasi via Docker Compose.

### Data Platform
| Komponen | Teknologi | Fungsi |
|----------|-----------|--------|
| **Distributed Storage** | Apache Hadoop (HDFS) 3.3 | Penyimpanan data layer Bronze, Silver, Gold |
| **Batch Processing** | Apache Spark 3.4 (PySpark) | Cleansing, ETL, Feature Engineering, Agregasi |
| **Data Warehouse** | Apache Hive 3.1 + Metastore (PostgreSQL) | Query layer Gold, Feature Store |
| **Orchestration** | Apache Airflow 2.7 | Workflow pipeline & scheduling |
| **Log Management** | OpenSearch 2.11 | Sentralisasi log & monitoring error |

### Data Quality & DevOps
- **Great Expectations**: Validasi data otomatis (Data Docs HTML)
- **CrewAI**: Autonomous agent framework untuk DataOps
- **GitPython**: Auto-commit patch hasil remediasi
- **Pinecone** (opsional): RAG untuk dokumentasi (ekspansi)

### Bahasa & Libraries
- **Python 3.10**: PySpark, CrewAI, FastAPI (untuk monitoring)
- **SQL**: HiveQL untuk query warehouse
- **Bash**: Scripting untuk Hadoop CLI commands

---

## 🚀 Cara Menjalankan Proyek (Instalasi)
Ikuti langkah-langkah berikut untuk menjalankan pipeline Project Mage AI di lingkungan lokal Anda.

### Prasyarat
- **Docker** & **Docker Compose** (v2.0+)
- **Python** 3.10+ (untuk menjalankan skrip lokal)
- **Git** (untuk cloning repositori)
- **Resource**: Minimal 16GB RAM, 4 CPU Core (recommended 32GB untuk full cluster)

### 1. Clone Repositori
```bash
git clone https://github.com/adikusumaa/project-mage-ai.git
cd project-mage-ai
```

### 2. Setup Infrastruktur (Docker Compose - Fase 1)
Build dan jalankan seluruh container cluster:
```bash
# Buat direktori untuk persistent volumes
mkdir -p hadoop_data/hdfs hive_data postgres_data airflow_logs opensearch_data

# Jalankan Docker Compose
docker-compose up -d

# Cek status semua container
docker-compose ps
```

**Verifikasi Layanan (Rekonsiliasi Fase 1):**
- ✅ Akses Airflow UI: http://localhost:8080 (user: airflow / pass: airflow)
- ✅ Akses Spark Master UI: http://localhost:8081
- ✅ Akses HDFS NameNode UI: http://localhost:9870
- ✅ Akses HiveServer2: `beeline -u jdbc:hive2://localhost:10000`

### 3. Setup Environment Python (untuk Skrip PySpark & CrewAI)
Buat virtual environment dan install dependencies:
```bash
# Buat virtual environment
python -m venv venv

# Aktivasi (Windows)
venv\Scripts\activate

# Aktivasi (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Konfigurasi Environment untuk CrewAI:**
Buat file `.env` di root proyek (untuk Autonomous DataOps):
```env
GROQ_API_KEY=your_groq_api_key        # Untuk LLM reasoning di CrewAI
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
HIVE_JDBC_URL=jdbc:hive2://localhost:10000
GIT_REPO_PATH=/path/to/repo
```

### 4. Menjalankan Pipeline Data (Fase 2 → 5)

**🔹 Fase 2: Bronze Layer (Ingestion)**
```bash
# Trigger DAG di Airflow UI atau via CLI
docker exec -it airflow-webserver airflow dags trigger dag_bronze_ingestion

# Verifikasi file di HDFS
docker exec -it namenode hdfs dfs -ls /data/bronze/home_credit/raw/
```

**🔹 Fase 3: Silver Layer (Cleansing & Integration)**
```bash
# Jalankan PySpark jobs secara berurutan (testing manual)
spark-submit --master spark://localhost:7077 jobs/silver_cleaning.py
spark-submit --master spark://localhost:7077 jobs/silver_feature_engineering.py
spark-submit --master spark://localhost:7077 jobs/silver_integration.py

# Atau via Airflow DAG (rekomendasi)
# Trigger dag_silver_processing di Airflow UI
```

**🔹 Fase 4: Gold Layer (Hive Aggregation)**
```bash
spark-submit --master spark://localhost:7077 jobs/gold_aggregation.py
```

**🔹 Fase 5: Autonomous DataOps (CrewAI Daemon)**
```bash
python crewai_dataops_daemon.py --mode daemon

# Atau jalankan agent secara spesifik:
python crewai_dataops_daemon.py --agent schema_observer
python crewai_dataops_daemon.py --agent incident_reporter
python crewai_dataops_daemon.py --agent data_steward
```

---

## 📂 Struktur Direktori Utama
```text
project-mage-ai/
├── config/                         # Konfigurasi service
│   ├── hive-site.xml
│   ├── spark-defaults.conf
│   └── airflow.cfg
├── dags/                           # Airflow DAGs
│   ├── dag_bronze_ingestion.py     # ✅ Fase 2 (Completed)
│   ├── dag_silver_processing.py    # ✅ Fase 3 (Completed)
│   ├── dag_gold_aggregation.py     # ✅ Fase 4 (Completed)
│   └── dag_crewai_ops.py           # ✅ Fase 5 (Completed)
├── data/                           # Dataset lokal (10 CSV)
│   ├── application_train.csv       (307,511 rows)
│   ├── application_test.csv        (48,744 rows)
│   ├── bureau.csv
│   ├── bureau_balance.csv
│   ├── credit_card_balance.csv
│   ├── installments_payments.csv
│   ├── POS_CASH_balance.csv
│   ├── previous_application.csv
│   ├── sample_submission.csv
│   └── HomeCredit_columns_description.csv
├── jobs/                           # PySpark Jobs
│   ├── silver_cleaning.py          # Pembersihan data
│   ├── silver_feature_engineering.py  # Fitur agregat dari 6 tabel
│   ├── silver_integration.py       # Left join ke master table
│   ├── gold_aggregation.py         # Agregasi ke Hive
│   └── application_profile.py      # Profiling & EDA
├── notebooks/                      # Jupyter Notebooks for EDA
│   ├── EDA.ipynb
│   ├── Explore.ipynb
│   └── Silver_Cleaning.ipynb
├── pyspark/                        # Great Expectations config
│   └── great_expectations/
│       ├── expectations/
│       └── data_docs/              # HTML reports (generated)
├── img/                            # Dokumentasi visual
│   ├── Hadoop Data Lake Bronze.png
│   ├── Hadoop Data Lake Silver.png
│   ├── Orchestration Airflow.png
│   └── Spark.png
├── docker-compose.yml              # Infrastruktur cluster
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables
├── README.md                       # Dokumentasi ini
└── TIMELINE.md                     # Progress tracking
```

---

## ✅ Validation Checklist (Progress Status)

| Fase | Nama | Status | Validasi Key |
|------|------|--------|--------------|
| **Fase 1** | Infrastructure Setup | ✅ PASS | Docker containers healthy, all UIs accessible |
| **Fase 2** | Bronze Ingestion | ✅ PASS | 10 CSV files in HDFS, checksum matching |
| **Fase 3** | Silver Processing | ✅ PASS | Cleaning + Aggregation + Integration + GE |
| **Fase 4** | Gold Hive DW | ✅ PASS | Hive tables queryable via Beeline |
| **Fase 5** | Autonomous DataOps (CrewAI) | ✅ PASS | Agents berhasil analisis, generate patch, review, dan buat PR di GitHub |

*Current Progress: Seluruh fase utama (Fase 1 hingga Fase 5) telah berhasil diselesaikan.*

---

## 🔍 Detail Fase yang Telah Dikerjakan

### ✅ Fase 1: Setup Infrastruktur & Environment (Completed)
- [x] Docker Compose dengan 10+ service (Hadoop, Hive, Spark, Airflow, OpenSearch)
- [x] Volume persistence untuk HDFS, PostgreSQL, dan logs
- [x] Rekonsiliasi: Semua container status Up, UIs accessible

### ✅ Fase 2: Layer Bronze - Raw Data Ingestion (Completed)
- [x] DAG `dag_bronze_ingestion.py` dengan 10 task parallel
- [x] Upload CSV ke HDFS path `/data/bronze/home_credit/raw/`
- [x] Validasi: File size identical (checksum matching)

![HDFS Bronze](img/Hadoop%20Data%20Lake%20Bronze.png)
*Screenshot HDFS Web UI menampilkan 10 file CSV ter-ingest*

![Airflow DAG](img/Orchestration%20Airflow.png)
*DAG Bronze Ingestion berstatus Success di Airflow UI*

---

## 🚀 Fase 5: Autonomous DataOps (CrewAI) – Selesai!

CrewAI telah diimplementasikan sebagai sistem autonomous untuk menangani error pipeline secara otomatis. Berikut alur kerjanya:
1. **Analyst** membaca log error dari OpenSearch dan HDFS schema, lalu memberikan rekomendasi perbaikan.
2. **Engineer** menulis ulang file kode (misal `dags/dag_silver_processing.py`) dengan tambahan handling kolom hilang.
3. **Reviewer** mengecek kode patch, memastikan tidak ada risiko data loss (misal `mode("overwrite")` langsung) dan memberikan status **APPROVED** atau **REJECTED**.
4. **GitPatchTool** (jika APPROVED) membuat branch `fix/incident-{timestamp}`, commit, push ke GitHub, dan membuka Pull Request.

**Hasil dari pengujian akhir:**
![Terminal CrewAI Agents](img/Ai_agents_CrewTerminal.png)
*Log terminal saat CrewAI menjalankan Analyst → Engineer → Reviewer hingga status APPROVED.*

![Branch Git yang dibuat oleh AI](img/AICrew%20Branch%20Git.png)
*Branch `fix/incident-*` dan Pull Request otomatis muncul di GitHub.*

---

### 📸 Screenshot Pipeline Silver & Hive Warehouse
Proses Silver Layer telah berhasil dijalankan dan data Gold di Hive siap diakses.

![Dev Silver 1](img/DEV%20SILVER.png)
*Proses cleansing & feature engineering pada Silver Layer.*

![Dev Silver 2](img/DEV%20SILVER%202.png)
*Validasi data dan Great Expectations report.*

![Error Test](img/Error%20Test.png)
*Simulasi error pada DAG `dag_silver_processing` yang memicu CrewAI.*

![Warehouse Hive](img/Warehouse%20Hive.png)
*Tabel Gold di Hive yang dapat diquery via Beeline.*

---

### 🧪 Hasil Akhir
- ✅ CrewAI berhasil menganalisis error `Column not found` (Schema Drift).
- ✅ Engineer menghasilkan patch yang valid dengan penanganan kolom hilang (menggunakan `F.lit(None).cast(...)`).
- ✅ Reviewer menyetujui patch (APPROVED) setelah memastikan keamanan data.
- ✅ GitPatchTool membuat branch, push, dan Pull Request ke GitHub.
- ✅ Seluruh pipeline (Bronze → Silver → Gold) berjalan otomatis melalui Airflow.

---

## 📈 Monitoring & Observability
- **Airflow UI**: http://localhost:8080 (user: airflow / pass: airflow)
- **Spark Master**: http://localhost:8081
- **Spark Worker**: http://localhost:8082
- **HDFS NameNode**: http://localhost:9870
- **OpenSearch Dashboards**: http://localhost:5601
- **Great Expectations Data Docs**: `./pyspark/great_expectations/data_docs/`

---

## 🧪 Cara Testing & Rekonsiliasi (Per Fase)

**Rekonsiliasi Fase 2 (Bronze):**
```bash
# Cek jumlah file di HDFS
hdfs dfs -ls /data/bronze/home_credit/raw/ | wc -l
# Expected: 10

# Cek checksum (contoh untuk 1 file)
md5sum data/application_train.csv
hdfs dfs -cat /data/bronze/home_credit/raw/application_train.csv | md5sum
# Expected: Sama
```

**Rekonsiliasi Fase 3 (Silver):**
```bash
# Jalankan validasi GE
great_expectations checkpoint run silver_checkpoint

# Cek hasil di Parquet
spark-shell
val df = spark.read.parquet("/data/silver/home_credit/integrated/train_integrated.parquet")
df.select("SK_ID_CURR", "TARGET").distinct().count()  # Harus sama dengan row count
df.filter("TARGET NOT IN (0,1)").count()  # Harus 0
```

---

## 🤝 Kontribusi
Karena proyek ini merupakan bagian dari DANA Data Engineer Intern Portfolio, kontribusi eksternal saat ini tidak dibuka. Namun, jika Anda tertarik dengan arsitektur data engineering modern atau Autonomous DataOps, silakan fork repositori ini untuk referensi pribadi.

---

## 📜 Referensi Akademik & Inspirasi
- Medallion Architecture (Databricks, 2020) - Multi-layer data pipeline
- Home Credit Default Risk (Kaggle Competition, 2018)
- Great Expectations - Data validation framework
- CrewAI - Autonomous agent orchestration (2024)
- Designing Data-Intensive Applications (Martin Kleppmann)

---

## 📬 Kontak
- **Author**: [adikusumaa]
- **LinkedIn**: [linkedin.com/in/adikusumaa](https://linkedin.com/in/adikusumaa)