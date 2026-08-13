# Project Plan: Analisis Tabel Tambahan (Previous Application, POS, Installments, Credit Card)

## Tujuan
Setelah menganalisis data **application** dan **bureau**, langkah selanjutnya adalah memperluas analisis ke tabel-tabel yang merekam **riwayat pengajuan pinjaman sebelumnya di Home Credit** serta **perilaku pembayaran cicilan** nasabah. Tujuannya adalah untuk menemukan fitur-fitur baru yang kuat untuk memprediksi gagal bayar (`target`).

Semua tabel ini terhubung dengan `application` melalui kolom `SK_ID_CURR` (atau `loanId`). Untuk tabel yang berhubungan dengan pinjaman sebelumnya, kita akan menggunakan `SK_ID_PREV` sebagai penghubung antar tabel detail.

---

## Pendekatan
Kita akan mengelompokkan kolom dari setiap tabel ke dalam grup logis berdasarkan makna bisnis. Untuk setiap grup, kita akan merumuskan hipotesis dan kemudian mengujinya dengan melakukan agregasi dan membandingkan metrik antara nasabah yang gagal bayar (`target=1`) dan yang lancar (`target=0`).

---

## Tabel 1: previous_application

Tabel ini berisi data **pengajuan pinjaman sebelumnya** yang pernah dilakukan nasabah di Home Credit. Setiap baris mewakili satu pengajuan sebelumnya.

**Skema kolom utama (yang sudah direname):**
- `SK_ID_PREV` → `prevId`
- `SK_ID_CURR` → `loanId`
- `NAME_CONTRACT_TYPE` → `prevContractType`
- `AMT_ANNUITY` → `prevAnnuity`
- `AMT_APPLICATION` → `prevApplicationAmt`
- `AMT_CREDIT` → `prevCreditAmt`
- `AMT_DOWN_PAYMENT` → `prevDownPayment`
- `AMT_GOODS_PRICE` → `prevGoodsPrice`
- `WEEKDAY_APPR_PROCESS_START` → `prevWeekdayApp`
- `HOUR_APPR_PROCESS_START` → `prevHourApp`
- `FLAG_LAST_APPL_PER_CONTRACT` → `prevLastAppFlag`
- `NFLAG_LAST_APPL_IN_DAY` → `prevLastAppInDay`
- `RATE_DOWN_PAYMENT` → `prevDownPaymentRate`
- `RATE_INTEREST_PRIMARY` → `prevInterestPrimary`
- `RATE_INTEREST_PRIVILEGED` → `prevInterestPrivileged`
- `NAME_CASH_LOAN_PURPOSE` → `prevCashLoanPurpose`
- `NAME_CONTRACT_STATUS` → `prevContractStatus`
- `DAYS_DECISION` → `prevDaysDecision`
- `NAME_PAYMENT_TYPE` → `prevPaymentType`
- `CODE_REJECT_REASON` → `prevRejectReason`
- `NAME_TYPE_SUITE` → `prevSuiteType`
- `NAME_CLIENT_TYPE` → `prevClientType`
- `NAME_GOODS_CATEGORY` → `prevGoodsCategory`
- `NAME_PORTFOLIO` → `prevPortfolio`
- `NAME_PRODUCT_TYPE` → `prevProductType`
- `CHANNEL_TYPE` → `prevChannel`
- `SELLERPLACE_AREA` → `prevSellerArea`
- `NAME_SELLER_INDUSTRY` → `prevSellerIndustry`
- `CNT_PAYMENT` → `prevPaymentCount`
- `NAME_YIELD_GROUP` → `prevYieldGroup`
- `PRODUCT_COMBINATION` → `prevProductCombination`
- `DAYS_FIRST_DRAWING` → `prevFirstDrawing`
- `DAYS_FIRST_DUE` → `prevFirstDue`
- `DAYS_LAST_DUE_1ST_VERSION` → `prevLastDue1st`
- `DAYS_LAST_DUE` → `prevLastDue`
- `DAYS_TERMINATION` → `prevTermination`
- `NFLAG_INSURED_ON_APPROVAL` → `prevInsured`

---

### Group 1: Status Kontrak dan Keputusan Pengajuan

**Columns involved:** `prevContractStatus`, `prevRejectReason`, `prevDaysDecision`  
**Hypothesis:**  
- Nasabah yang sering ditolak (`Refused`) atau pengajuannya dibatalkan (`Canceled`) memiliki risiko gagal bayar lebih tinggi karena mereka mungkin memiliki profil kredit yang buruk.  
- Alasan penolakan (`prevRejectReason`) dapat memberikan sinyal spesifik tentang kelemahan nasabah (misal: pendapatan tidak cukup, riwayat kredit buruk).  
- Waktu pengambilan keputusan (`prevDaysDecision`) yang sangat cepat atau sangat lambat mungkin mencerminkan proses yang tidak normal.

**What to analyze:**  
- Distribusi `target` berdasarkan `prevContractStatus`.  
- Rata-rata jumlah pengajuan yang ditolak per nasabah dibandingkan antara target 1 dan 0.  
- Frekuensi alasan penolakan tertentu pada nasabah gagal bayar.  
- Rata-rata `prevDaysDecision` per target.

**Kesimpulan Teknis – Group 1:**
_(Kosong, akan diisi setelah analisis)_

**🛠️ Feature Engineering Recommendations:**
_(Kosong)_

---

### Group 2: Nominal dan Rasio Pinjaman

**Columns involved:** `prevApplicationAmt`, `prevCreditAmt`, `prevDownPayment`, `prevGoodsPrice`, `prevDownPaymentRate`, `prevInterestPrimary`, `prevInterestPrivileged`  
**Hypothesis:**  
- Jumlah pinjaman yang diajukan (`prevApplicationAmt`) dan yang disetujui (`prevCreditAmt`) bisa mencerminkan kebutuhan dan kemampuan nasabah.  
- Rasio uang muka (`prevDownPaymentRate`) yang rendah mungkin menandakan nasabah tidak memiliki dana cukup, sehingga risiko lebih tinggi.  
- Suku bunga (`prevInterestPrimary`) yang tinggi bisa menjadi indikator bahwa nasabah dianggap berisiko oleh sistem.

**What to analyze:**  
- Rata-rata `prevCreditAmt` dan `prevApplicationAmt` per target.  
- Rata-rata `prevDownPaymentRate` dan `prevInterestPrimary` per target.  
- Distribusi default rate berdasarkan kelompok rasio uang muka (misal: <10%, 10-20%, >20%).

**Kesimpulan Teknis – Group 2:**
_(Kosong)_

**🛠️ Feature Engineering Recommendations:**
_(Kosong)_

---

### Group 3: Perilaku Waktu dan Durasi

**Columns involved:** `prevDaysDecision`, `prevFirstDrawing`, `prevFirstDue`, `prevLastDue`, `prevTermination`  
**Hypothesis:**  
- Waktu yang dibutuhkan untuk keputusan (`prevDaysDecision`) mungkin mencerminkan kompleksitas pengajuan.  
- Durasi pinjaman (dari `prevFirstDue` sampai `prevLastDue`) dapat memberi gambaran jangka waktu pinjaman, yang mungkin berkorelasi dengan risiko.  
- Pinjaman dengan jangka waktu panjang mungkin memiliki risiko lebih tinggi karena ketidakpastian yang lebih besar.

**What to analyze:**  
- Rata-rata `prevDaysDecision` dan durasi pinjaman per target.  
- Bucket durasi pinjaman (misal: <12 bulan, 12-24 bulan, >24 bulan) dan default rate-nya.

**Kesimpulan Teknis – Group 3:**
_(Kosong)_

**🛠️ Feature Engineering Recommendations:**
_(Kosong)_

---

### Group 4: Jenis Produk dan Saluran

**Columns involved:** `prevContractType`, `prevCashLoanPurpose`, `prevPortfolio`, `prevProductType`, `prevChannel`, `prevSellerIndustry`, `prevGoodsCategory`  
**Hypothesis:**  
- Jenis produk pinjaman (`prevContractType`), tujuan pinjaman tunai (`prevCashLoanPurpose`), dan kategori barang (`prevGoodsCategory`) dapat mengindikasikan risiko yang berbeda.  
- Saluran akuisisi (`prevChannel`) dan industri penjual (`prevSellerIndustry`) mungkin mempengaruhi kualitas nasabah.

**What to analyze:**  
- Default rate untuk setiap `prevContractType`, `prevCashLoanPurpose`, dan `prevGoodsCategory`.  
- Apakah ada saluran yang menghasilkan nasabah dengan risiko lebih tinggi.

**Kesimpulan Teknis – Group 4:**
_(Kosong)_

**🛠️ Feature Engineering Recommendations:**
_(Kosong)_

---

### Group 5: Jumlah dan Frekuensi Pengajuan

**Columns involved:** `prevLastAppInDay`, `prevLastAppFlag`, `prevPaymentCount`  
**Hypothesis:**  
- Nasabah yang mengajukan banyak pinjaman dalam satu hari (`prevLastAppInDay`) mungkin sedang dalam kondisi mendesak, sehingga risiko lebih tinggi.  
- Jumlah angsuran (`prevPaymentCount`) menunjukkan tenor pinjaman, yang bisa jadi indikator beban.

**What to analyze:**  
- Rata-rata jumlah pengajuan per hari dan per kontrak per target.  
- Distribusi default rate berdasarkan jumlah angsuran (tenor).

**Kesimpulan Teknis – Group 5:**
_(Kosong)_

**🛠️ Feature Engineering Recommendations:**
_(Kosong)_

---

## Tabel 2: POS_CASH_balance

Tabel ini mencatat **saldo bulanan** dari pinjaman POS (Point of Sales) atau pinjaman tunai yang sedang berjalan di Home Credit. Setiap baris adalah snapshot bulanan dari satu pinjaman.

**Skema kolom utama (renamed):**
- `SK_ID_PREV` → `posPrevId`
- `SK_ID_CURR` → `loanId`
- `MONTHS_BALANCE` → `posMonthsBalance`
- `CNT_INSTALMENT` → `posCntInstalment`
- `CNT_INSTALMENT_FUTURE` → `posCntInstalmentFuture`
- `NAME_CONTRACT_STATUS` → `posContractStatus`
- `SK_DPD` → `posDpd`
- `SK_DPD_DEF` → `posDpdDef`

---

### Group 1: Status Kontrak dan DPD (Days Past Due)

**Columns involved:** `posContractStatus`, `posDpd`, `posDpdDef`  
**Hypothesis:**  
- Pinjaman yang statusnya `Active` dan memiliki DPD (`posDpd`) yang tinggi menunjukkan bahwa nasabah sedang bermasalah.  
- `posDpdDef` (DPD dengan toleransi) mungkin lebih halus, tapi tetap menunjukkan risiko.

**What to analyze:**  
- Rata-rata DPD maksimum dan rata-rata DPD per nasabah, dibandingkan antara target 1 dan 0.  
- Proporsi bulan dengan status `Active` dan `Completed` per nasabah.
Kesimpulan Teknis – Group 1 (Status Kontrak dan Keputusan Pengajuan)
Metrik	Insight	Rekomendasi untuk Fitur
prevContractStatus = 'Refused'	Pengajuan ditolak adalah sinyal risiko kuat.	Wajib digunakan sebagai binary flag: has_refused_prev = 1 jika ada Refused di riwayat.
refused_count	Semakin banyak ditolak, semakin berisiko.	Wajib digunakan sebagai numerik (refused_count).
prevRejectReason	SCOFR dan LIMIT adalah red flag.	Gunakan sebagai kategorikal atau binary flag: is_high_risk_reason = 1 jika reason = SCOFR atau LIMIT.
prevDaysDecision	Keputusan ≤ 30 hari memiliki risiko lebih tinggi.	Gunakan sebagai binary flag: is_recent_decision = 1 jika prevDaysDecision >= -30.
🛠️ Feature Engineering Recommendations for Gold Layer
Berdasarkan Group 1, fitur-fitur yang paling direkomendasikan:

has_refused_prev (Binary) – 1 jika ada pengajuan dengan status Refused di riwayat.
Ini adalah fitur wajib! Menangkap esensi "pernah ditolak".

refused_count (Numerik) – Jumlah total pengajuan dengan status Refused per nasabah.
Sinyal valid: semakin banyak, semakin berisiko.

is_high_risk_reason (Binary) – 1 jika alasan penolakan adalah SCOFR atau LIMIT, 0 jika lainnya.
Menangkap alasan penolakan yang paling berbahaya.

is_recent_decision (Binary) – 1 jika keputusan pengajuan terakhir terjadi dalam 30 hari terakhir (prevDaysDecision >= -30).
Menangkap nasabah dengan kebutuhan mendesak.

Fitur yang TIDAK perlu dibuat:

prevContractStatus mentah sebagai one-hot (terlalu banyak kategori, beberapa seperti Canceled atau Unused mungkin tidak signifikan).

avg_days_decision mentah (karena sinyalnya lebih kuat saat di-binary-kan menjadi is_recent_decision).

prevRejectReason one-hot penuh (terlalu banyak kategori langka).
---

### Group 2: Sisa Angsuran

**Columns involved:** `posCntInstalment`, `posCntInstalmentFuture`  
**Hypothesis:**  
- Semakin banyak sisa angsuran (`posCntInstalmentFuture`), semakin besar beban yang masih harus dibayar, sehingga risiko lebih tinggi.

**What to analyze:**  
- Rata-rata `posCntInstalmentFuture` per target.  
- Bucket sisa angsuran (misal: 0, 1-6, 7-12, >12) dan default rate-nya.

 Kesimpulan Teknis – Group 2 (Sisa Angsuran POS)
Metrik	Insight	Rekomendasi untuk Fitur
posCntInstalmentFuture	Perbedaan sangat tipis (11,3 vs 10,4).	Tidak digunakan (tidak informatif sebagai fitur utama).
remaining_installment_bucket	Selisih default rate hanya 0,6%.	Tidak digunakan (tidak informatif).
risk_profile = High Remaining + DPD	Red flag terkuat (12,87%).	Wajib digunakan sebagai fitur silang: is_pos_high_risk = 1 jika posCntInstalmentFuture > 12 AND posDpd > 0.
posDpd (DPD)	DPD saja sudah menaikkan risiko ke 9,64%.	Wajib digunakan secara terpisah: has_pos_dpd = 1 jika posDpd > 0.
🛠️ Feature Engineering Recommendations for Gold Layer
Berdasarkan Group 2, fitur-fitur yang paling direkomendasikan dari tabel POS_CASH_balance:

has_pos_dpd (Binary) – 1 jika terdapat DPD (posDpd > 0) pada pinjaman POS.
Sinyal valid: DPD adalah indikator tunggakan yang langsung meningkatkan risiko.

is_pos_high_risk (Binary) – 1 jika posCntInstalmentFuture > 12 AND posDpd > 0.
Ini adalah fitur interaksi terkuat! Menangkap nasabah yang memiliki beban angsuran panjang sekaligus sedang menunggak.

Fitur yang TIDAK perlu dibuat:

posCntInstalmentFuture mentah (sangat lemah).

remaining_installment_bucket (perbedaannya kecil dan tidak informatif).

💡 Ringkasan Akhir untuk Anda
Dari Group 2, kita belajar bahwa beban angsuran yang panjang tidak selalu berbahaya, tetapi kombinasi beban panjang dengan tunggakan (DPD) adalah sinyal bahaya yang sesungguhnya. DPD adalah trigger yang mengubah nasabah biasa menjadi nasabah berisiko tinggi.

Fitur is_pos_high_risk dan has_pos_dpd harus masuk ke dalam tabel Gold Layer Anda.

---

### Group 3: Durasi dan Riwayat Bulanan

**Columns involved:** `posMonthsBalance`  
**Hypothesis:**  
- Panjangnya riwayat saldo (`posMonthsBalance`) dapat menunjukkan seberapa lama pinjaman sudah berjalan. Nasabah dengan pinjaman yang sudah lama mungkin lebih stabil.

**What to analyze:**  
- Rata-rata `posMonthsBalance` terbaru dan tertua per target.  
- Tren status dari waktu ke waktu (misal: apakah status memburuk).

Kesimpulan Teknis – Group 3 (Durasi dan Riwayat Bulanan)
Metrik	Insight	Rekomendasi untuk Fitur
history_length	Defaulter memiliki riwayat 6 bulan lebih pendek.	Wajib digunakan sebagai numerik (pos_history_length).
history_duration = >24 bulan	Kelompok paling stabil (7,45% default rate).	Gunakan sebagai biner: is_pos_long_history = 1 jika history_length > 24 bulan.
avg_status_score	Tidak ada perbedaan (1,82 vs 1,82).	Tidak digunakan (tidak informatif).
status_trend	Tren negatif identik pada kedua kelompok.	Tidak digunakan (tidak informatif).
🛠️ Feature Engineering Recommendations for Gold Layer
Berdasarkan Group 3, fitur-fitur yang paling direkomendasikan dari tabel POS_CASH_balance:

pos_history_length (Numerik) – Durasi riwayat pinjaman POS (dalam bulan).
Ini adalah sinyal utama: semakin panjang, semakin aman.

is_pos_long_history (Binary) – 1 jika riwayat pinjaman POS > 24 bulan.
Menangkap kelompok nasabah paling stabil.

Fitur yang TIDAK perlu dibuat:

avg_pos_status_score (lemah dan tidak informatif).

pos_status_trend (tidak informatif).

💡 Ringkasan Akhir untuk Anda
Dari Group 3, kita belajar bahwa panjangnya riwayat pinjaman POS jauh lebih penting daripada status pinjaman saat ini:

Nasabah dengan riwayat pinjaman POS yang panjang (>2 tahun) terbukti jauh lebih aman (default rate 7,45%).

Nasabah dengan riwayat menengah (1-2 tahun) justru memiliki risiko paling tinggi (10,5%).

Kedua fitur ini (pos_history_length dan is_pos_long_history) harus dipertimbangkan untuk masuk ke dalam tabel Gold Layer Anda.
---

## Tabel 3: installments_payments

Tabel ini mencatat **detail pembayaran cicilan** dari pinjaman sebelumnya. Setiap baris adalah satu cicilan (instalment) yang seharusnya dibayar dan apakah sudah dibayar.

**Skema kolom utama (renamed):**
- `SK_ID_PREV` → `instPrevId`
- `SK_ID_CURR` → `loanId`
- `NUM_INSTALMENT_VERSION` → `instVersion`
- `NUM_INSTALMENT_NUMBER` → `instNumber`
- `DAYS_INSTALMENT` → `instDueDay`
- `DAYS_ENTRY_PAYMENT` → `instPayDay`
- `AMT_INSTALMENT` → `instAmount`
- `AMT_PAYMENT` → `instPaid`

---

### Group 1: Keterlambatan Pembayaran

**Columns involved:** `instDueDay`, `instPayDay`  
**Hypothesis:**  
- Selisih antara hari jatuh tempo (`instDueDay`) dan hari pembayaran (`instPayDay`) mengukur keterlambatan. Semakin sering dan semakin lama keterlambatan, semakin tinggi risiko.

**What to analyze:**  
- Rata-rata jumlah hari keterlambatan per nasabah (`instPayDay - instDueDay`).  
- Persentase cicilan yang dibayar tepat waktu vs terlambat per nasabah.  
- Rata-rata keterlambatan untuk target 1 vs 0.

Kesimpulan Teknis – Group 1 (Keterlambatan Pembayaran)
Metrik	Insight	Rekomendasi untuk Fitur
avg_late_days	Selisih sangat kecil (1 hari), tidak informatif.	Tidak digunakan (tidak informatif).
late_ratio	Nasabah gagal bayar memiliki proporsi telat 3% lebih tinggi.	Wajib digunakan sebagai numerik (inst_late_ratio = late_count / total_installments).
late_bucket = Keterlambatan Sedang	Bucket paling berisiko (13,9% default rate).	Gunakan sebagai fitur biner: is_inst_medium_late = 1 jika avg_late_days antara 6-15 hari.
🛠️ Feature Engineering Recommendations for Gold Layer
Berdasarkan Group 1, fitur-fitur yang paling direkomendasikan dari tabel installments_payments:

inst_late_ratio (Numerik) – Proporsi cicilan yang dibayar terlambat (late_count / total_installments).
Sinyal valid: semakin tinggi proporsi, semakin berisiko.

is_inst_medium_late (Binary) – 1 jika rata-rata keterlambatan nasabah berada di rentang 6-15 hari.
Ini adalah fitur interaksi yang sangat kuat, menangkap kelompok paling berisiko.

Fitur yang TIDAK perlu dibuat:

avg_late_days mentah (lemah dan tidak informatif).

inst_on_time_ratio (redundan dengan inst_late_ratio).

💡 Ringkasan Akhir untuk Anda
Dari Group 1, kita belajar bahwa perilaku pembayaran masa lalu adalah cerminan yang kuat dari risiko masa depan, tetapi kita harus berhati-hati dalam memilih metrik yang tepat:

Proporsi keterlambatan (inst_late_ratio) adalah sinyal yang valid.

Keterlambatan menengah (6-15 hari) adalah zona bahaya yang paling mengkhawatirkan, karena nasabah masih berusaha tapi mulai kehilangan kendali.

Kedua fitur ini (inst_late_ratio dan is_inst_medium_late) harus dipertimbangkan untuk masuk ke dalam tabel Gold Layer Anda.

---

### Group 2: Jumlah dan Nilai Pembayaran

**Columns involved:** `instAmount`, `instPaid`, `instNumber`  
**Hypothesis:**  
- Nasabah yang membayar kurang dari jumlah yang seharusnya (`instPaid < instAmount`) menunjukkan kesulitan keuangan.  
- Jumlah cicilan yang sudah dibayar vs total cicilan bisa menjadi indikator kepatuhan.

**What to analyze:**  
- Rata-rata selisih pembayaran (`instPaid - instAmount`) per target.  
- Persentase cicilan yang dibayar kurang dari seharusnya.

Kesimpulan Teknis – Group 2 (Jumlah dan Nilai Pembayaran)
Metrik	Insight	Rekomendasi untuk Fitur
avg_payment_diff	Perbedaan ekstrem (-148 vs +409).	Wajib digunakan sebagai numerik (inst_avg_payment_diff).
payment_diff_bucket	Kurang Bayar Berat sangat berisiko (10,8%).	Gunakan sebagai kategorikal atau binary flag: is_inst_heavy_underpaid = 1 jika avg_payment_diff < -500.
underpaid_frequency	Sering kurang bayar (>30%) sangat berisiko (12,3%).	Wajib digunakan sebagai kategorikal: inst_underpaid_freq (Tidak Pernah, Jarang, Sedang, Sering).
🛠️ Feature Engineering Recommendations for Gold Layer
Berdasarkan Group 2, fitur-fitur yang paling direkomendasikan dari tabel installments_payments:

inst_avg_payment_diff (Numerik) – Rata-rata selisih pembayaran (instPaid - instAmount) per nasabah.
Fitur utama! Semakin negatif, semakin berisiko.

inst_underpaid_freq (Kategorikal) – Frekuensi kurang bayar dengan 4 level risiko: 'Tidak Pernah', 'Jarang', 'Sedang', 'Sering'.
Sinyal paling kuat: Sering (>30%) → default rate 12,3%.

is_inst_heavy_underpaid (Binary) – 1 jika rata-rata selisih pembayaran < -500.
Menangkap kelompok yang paling parah kurang bayar.

Fitur yang TIDAK perlu dibuat:

instPaid atau instAmount mentah (sudah terwakili oleh selisih dan frekuensi).

inst_on_time_ratio (sudah ada dari Group 1).

💡 Ringkasan Akhir untuk Anda
Dari Group 2, kita belajar bahwa perilaku pembayaran yang tidak disiplin (kurang bayar) adalah salah satu indikator risiko paling kuat:

Rata-rata selisih pembayaran (inst_avg_payment_diff) memberikan pemisahan yang sangat jelas (-148 vs +409).

Frekuensi kurang bayar (inst_underpaid_freq)—semakin sering kurang bayar, semakin tinggi risiko.

Kedua fitur ini wajib masuk ke dalam tabel Gold Layer Anda.

---

### Group 3: Versi dan Urutan Cicilan

**Columns involved:** `instVersion`, `instNumber`  
**Hypothesis:**  
- Perubahan versi (`instVersion`) mungkin menunjukkan adanya penyesuaian jadwal, yang bisa jadi tanda masalah.

**What to analyze:**  
- Rata-rata jumlah versi per pinjaman.

Kesimpulan Teknis – Group 3 (Versi dan Urutan Cicilan)
Metrik	Insight	Rekomendasi untuk Fitur
max_version_group = Versi 0	Risiko tertinggi (11,69% default rate).	Wajib digunakan sebagai fitur biner: is_inst_version_0 = 1 jika instVersion pernah bernilai 0.
avg_version_per_customer	Selisih sangat kecil (0,06).	Tidak digunakan (tidak informatif).
avg_installment_count	Selisih ~1 cicilan.	Tidak digunakan (tidak informatif).
🛠️ Feature Engineering Recommendations for Gold Layer
Berdasarkan Group 3, fitur-fitur yang paling direkomendasikan dari tabel installments_payments:

is_inst_version_0 (Binary) – 1 jika pernah ada cicilan dengan instVersion = 0.
Ini adalah sinyal utama: Versi 0 menandakan pinjaman baru atau belum teruji.

Fitur yang TIDAK perlu dibuat:

avg_version_per_customer (lemah).

avg_installment_count (selisih sangat kecil).

💡 Ringkasan Akhir untuk Anda
Dari Group 3, kita belajar bahwa versi cicilan yang rendah (khususnya 0) lebih berbahaya daripada versi yang lebih tinggi. Ini adalah temuan yang kontra-intuitif namun valid secara statistik dan masuk akal secara bisnis:

Versi 0 adalah "kategori risiko". Pinjaman yang belum memiliki riwayat versi atau belum mengalami penyesuaian dianggap lebih berisiko.

Versi 1, 2, atau 3+ justru menunjukkan bahwa pinjaman sudah "dewasa" dan risikonya lebih rendah.

Fitur is_inst_version_0 harus dipertimbangkan untuk masuk ke dalam tabel Gold Layer Anda.


---

## Tabel 4: credit_card_balance

Tabel ini mencatat **saldo bulanan kartu kredit** nasabah. Mirip dengan POS_CASH_balance tapi khusus untuk produk revolving (kartu kredit).

**Skema kolom utama (renamed):**
- `SK_ID_PREV` → `ccPrevId`
- `SK_ID_CURR` → `loanId`
- `MONTHS_BALANCE` → `ccMonthsBalance`
- `AMT_BALANCE` → `ccBalance`
- `AMT_CREDIT_LIMIT_ACTUAL` → `ccLimit`
- `AMT_DRAWINGS_ATM_CURRENT` → `ccDrawAtm`
- `AMT_DRAWINGS_CURRENT` → `ccDrawCurrent`
- `AMT_DRAWINGS_OTHER_CURRENT` → `ccDrawOther`
- `AMT_DRAWINGS_POS_CURRENT` → `ccDrawPos`
- `AMT_INST_MIN_REGULARITY` → `ccMinInst`
- `AMT_PAYMENT_CURRENT` → `ccPayment`
- `AMT_PAYMENT_TOTAL_CURRENT` → `ccPaymentTotal`
- `AMT_RECEIVABLE_PRINCIPAL` → `ccReceivablePrincipal`
- `AMT_RECIVABLE` → `ccReceivable`
- `AMT_TOTAL_RECEIVABLE` → `ccTotalReceivable`
- `CNT_DRAWINGS_ATM_CURRENT` → `ccCountDrawAtm`
- `CNT_DRAWINGS_CURRENT` → `ccCountDraw`
- `CNT_DRAWINGS_OTHER_CURRENT` → `ccCountDrawOther`
- `CNT_DRAWINGS_POS_CURRENT` → `ccCountDrawPos`
- `CNT_INSTALMENT_MATURE_CUM` → `ccPaidInstallments`
- `NAME_CONTRACT_STATUS` → `ccContractStatus`
- `SK_DPD` → `ccDpd`
- `SK_DPD_DEF` → `ccDpdDef`

---

### Group 1: Saldo dan Limit

**Columns involved:** `ccBalance`, `ccLimit`  
**Hypothesis:**  
- Rasio saldo terhadap limit (`ccBalance / ccLimit`) adalah indikator utilisasi kredit yang sangat kuat. Semakin tinggi utilisasi, semakin tinggi risiko.

**What to analyze:**  
- Rata-rata utilisasi kredit (`ccBalance / ccLimit`) per target.  
- Bucket utilisasi (misal: <30%, 30-70%, >70%) dan default rate-nya.

 Kesimpulan Teknis – Group 1 (Saldo dan Limit)
Metrik	Insight	Rekomendasi untuk Fitur
avg_utilization	Defaulter memiliki utilisasi 47% vs 31%.	Gunakan sebagai numerik (cc_avg_utilization).
utilization_bucket = Tinggi (>70%)	Red flag terkuat (15,57% default rate).	Wajib digunakan sebagai fitur biner: is_cc_high_utilization = 1 jika avg_utilization > 0.7.
recent_utilization	Defaulter mencapai 67% di bulan terakhir.	Wajib digunakan sebagai numerik (cc_recent_utilization).
🛠️ Feature Engineering Recommendations for Gold Layer
Berdasarkan Group 1, fitur-fitur yang paling direkomendasikan dari tabel credit_card_balance:

is_cc_high_utilization (Binary) – 1 jika rata-rata utilisasi kartu kredit nasabah > 70%.
Ini adalah fitur wajib! Menangkap nasabah yang "terjepit" secara finansial.

cc_recent_utilization (Numerik) – Utilisasi kartu kredit pada bulan terakhir (ccMonthsBalance = -1).
Sinyal terkuat: semakin mendekati 1, semakin berisiko.

cc_avg_utilization (Numerik) – Rata-rata utilisasi kartu kredit sepanjang riwayat.
Sinyal yang valid, meskipun tidak sekuat recent_utilization.

Fitur yang TIDAK perlu dibuat:

ccBalance atau ccLimit mentah (sudah terwakili oleh rasio dan bucket utilisasi).

ccContractStatus (status kartu kredit mungkin tidak sepenting utilisasi).

💡 Ringkasan Akhir untuk Anda
Dari Group 1, kita belajar bahwa kartu kredit adalah produk yang sangat menentukan risiko gagal bayar:

Utilisasi kredit > 70% adalah red flag paling kuat (default rate 15,57%).

Utilisasi pada bulan terakhir bahkan lebih informatif daripada rata-rata historis.

Kedua fitur ini (is_cc_high_utilization dan cc_recent_utilization) wajib masuk ke dalam tabel Gold Layer Anda.


---

### Group 2: Penarikan dan Pembayaran

**Columns involved:** `ccDrawCurrent`, `ccPayment`, `ccPaymentTotal`  
**Hypothesis:**  
- Nasabah yang sering menarik dana (`ccDrawCurrent`) mungkin memiliki kebutuhan finansial yang tinggi.  
- Rasio pembayaran terhadap penarikan dapat menunjukkan kemampuan membayar.

**What to analyze:**  
- Rata-rata total penarikan dan total pembayaran per target.  
- Rasio pembayaran/penarikan per target.

Kesimpulan Teknis – Group 2 (Penarikan dan Pembayaran)
Metrik	Insight	Rekomendasi untuk Fitur
avg_pay_draw_ratio mentah	Anomali data (5,35 vs 0,97)	Tidak digunakan (tidak reliable).
pay_ratio_bucket = Pembayaran Sangat Rendah	Red flag terkuat (18,89% default rate).	Wajib digunakan sebagai fitur biner: is_cc_low_pay_ratio = 1 jika pay_draw_ratio < 0.4.
pay_ratio_bucket = Tidak Ada Penarikan	Nasabah paling aman (5,62% default rate).	Gunakan sebagai fitur biner: has_cc_activity = 0 jika ccDrawCurrent = 0 atau NULL.
net_borrowing_bucket = Menambah Hutang Ringan	Sinyal risiko yang valid (14,16% default rate).	Gunakan sebagai fitur biner: is_cc_accruing_debt = 1 jika avg_net_borrowing positif dan tidak ekstrem.
net_borrowing_bucket = Menambah Hutang Berat	Anomali data (default rate rendah).	Tidak digunakan (tidak reliable).
🛠️ Feature Engineering Recommendations for Gold Layer
Berdasarkan Group 2, fitur-fitur yang paling direkomendasikan dari tabel credit_card_balance:

is_cc_low_pay_ratio (Binary) – 1 jika rasio pembayaran/penarikan nasabah < 0.4.
Ini adalah fitur wajib! Menangkap nasabah yang membayar sangat sedikit dibandingkan penarikannya.

has_cc_activity (Binary) – 1 jika nasabah memiliki aktivitas penarikan (ccDrawCurrent > 0).
Sinyal penting: nasabah yang tidak aktif menggunakan kartu kredit justru sangat aman.

is_cc_accruing_debt (Binary) – 1 jika nasabah secara konsisten menambah hutang (net borrowing positif) dengan jumlah yang wajar (tidak ekstrem).
Menangkap nasabah yang aktif menambah beban hutang secara bertahap.

Fitur yang TIDAK perlu dibuat:

avg_pay_draw_ratio mentah (anomali data).

net_borrowing_bucket = Menambah Hutang Berat (tidak reliable).

💡 Ringkasan Akhir untuk Anda
Dari Group 2, kita belajar bahwa perilaku penarikan dan pembayaran kartu kredit adalah indikator risiko yang sangat kuat, namun kita harus waspada terhadap data quality issues:

Rasio pembayaran yang sangat rendah (<0.4) adalah red flag paling kuat (18,89% default rate).

Nasabah yang tidak memiliki aktivitas penarikan justru adalah kelompok paling aman.

Nasabah yang menambah hutang secara ringan juga menunjukkan sinyal risiko yang valid.

Fitur is_cc_low_pay_ratio dan has_cc_activity wajib masuk ke dalam tabel Gold Layer Anda.

---

### Group 3: Status dan DPD

**Columns involved:** `ccContractStatus`, `ccDpd`, `ccDpdDef`  
**Hypothesis:**  
- Status kartu kredit dan DPD memberikan sinyal yang sama dengan POS_CASH.

**What to analyze:**  
- Rata-rata DPD maksimum per nasabah.

esimpulan Teknis – Group 3 (Status dan DPD)
Metrik	Insight	Rekomendasi untuk Fitur
avg_max_dpd	Defaulter memiliki DPD lebih rendah.	Tidak digunakan (tidak informatif).
dpd_history = Pernah Tunggakan	Default rate lebih rendah (8,22% vs 8,79%).	Tidak digunakan (tidak valid secara bisnis).
dpd_type	Selisih default rate sangat kecil (≤0,5%).	Tidak digunakan (tidak signifikan).
🛠️ Feature Engineering Recommendations for Gold Layer
Berdasarkan Group 3, tidak ada fitur yang direkomendasikan dari kelompok ini.

Kesimpulan Akhir: Data DPD pada kartu kredit terbukti tidak reliable dan tidak memberikan sinyal risiko yang valid. Sebaiknya kita fokus pada fitur-fitur yang sudah terbukti kuat dari Group 1 (Utilisasi) dan Group 2 (Rasio Pembayaran).

💡 Ringkasan Akhir untuk Anda
Dari Group 3, kita belajar bahwa tidak semua data DPD bisa dipercaya. Meskipun secara intuisi "tunggakan" seharusnya menjadi sinyal bahaya, data quality issue bisa membuat sinyal tersebut menjadi noise.

Jangan paksakan fitur dari Group 3 ini ke dalam Gold Layer, karena akan merusak performa model. Terus fokus pada fitur-fitur kuat dari Group 1 dan Group 2 yang sudah kita temukan sebelumnya.

---

## Important Considerations

- Karena hubungan antara `application` dan tabel-tabel ini adalah **one-to-many** (satu `loanId` dapat memiliki banyak baris di tabel previous_application, POS_CASH, installments, credit_card), kita harus melakukan **agregasi** per `loanId` sebelum membandingkan dengan `target`.  
- Semua analisis harus dilakukan pada tingkat **nasabah (`loanId`)**, bukan pada tingkat record individual.  
- Untuk setiap grup, kita akan membuat tabel agregasi (misal `AVG`, `SUM`, `COUNT`, `MAX`) dan kemudian melakukan JOIN dengan `application` untuk mendapatkan `target`.  
- Hasil akhir dari proyek ini adalah serangkaian wawasan yang secara langsung akan menginformasikan fitur-fitur dari tabel-tabel tambahan yang akan dimasukkan ke dalam Gold Layer.

---

## Next Steps

1. Tulis query agregasi untuk setiap grup pada masing-masing tabel.  
2. Gabungkan hasil agregasi dengan `application`.  
3. Jalankan EDA pada dataset gabungan dan catat kesimpulan.  
4. Prioritaskan fitur berdasarkan dampak yang diamati dan logika bisnis.  
5. Integrasikan fitur-fitur terpilih ke dalam satu tabel final `APPLICATION_W_PREVIOUS` (gabungan application + previous_application) dan kemudian ke tabel Gold akhir.