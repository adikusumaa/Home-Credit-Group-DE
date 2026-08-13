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

**Kesimpulan Teknis – Group 1:**
_(Kosong)_

**🛠️ Feature Engineering Recommendations:**
_(Kosong)_

---

### Group 2: Sisa Angsuran

**Columns involved:** `posCntInstalment`, `posCntInstalmentFuture`  
**Hypothesis:**  
- Semakin banyak sisa angsuran (`posCntInstalmentFuture`), semakin besar beban yang masih harus dibayar, sehingga risiko lebih tinggi.

**What to analyze:**  
- Rata-rata `posCntInstalmentFuture` per target.  
- Bucket sisa angsuran (misal: 0, 1-6, 7-12, >12) dan default rate-nya.

**Kesimpulan Teknis – Group 2:**
_(Kosong)_

**🛠️ Feature Engineering Recommendations:**
_(Kosong)_

---

### Group 3: Durasi dan Riwayat Bulanan

**Columns involved:** `posMonthsBalance`  
**Hypothesis:**  
- Panjangnya riwayat saldo (`posMonthsBalance`) dapat menunjukkan seberapa lama pinjaman sudah berjalan. Nasabah dengan pinjaman yang sudah lama mungkin lebih stabil.

**What to analyze:**  
- Rata-rata `posMonthsBalance` terbaru dan tertua per target.  
- Tren status dari waktu ke waktu (misal: apakah status memburuk).

**Kesimpulan Teknis – Group 3:**
_(Kosong)_

**🛠️ Feature Engineering Recommendations:**
_(Kosong)_

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

**Kesimpulan Teknis – Group 1:**
_(Kosong)_

**🛠️ Feature Engineering Recommendations:**
_(Kosong)_

---

### Group 2: Jumlah dan Nilai Pembayaran

**Columns involved:** `instAmount`, `instPaid`, `instNumber`  
**Hypothesis:**  
- Nasabah yang membayar kurang dari jumlah yang seharusnya (`instPaid < instAmount`) menunjukkan kesulitan keuangan.  
- Jumlah cicilan yang sudah dibayar vs total cicilan bisa menjadi indikator kepatuhan.

**What to analyze:**  
- Rata-rata selisih pembayaran (`instPaid - instAmount`) per target.  
- Persentase cicilan yang dibayar kurang dari seharusnya.

**Kesimpulan Teknis – Group 2:**
_(Kosong)_

**🛠️ Feature Engineering Recommendations:**
_(Kosong)_

---

### Group 3: Versi dan Urutan Cicilan

**Columns involved:** `instVersion`, `instNumber`  
**Hypothesis:**  
- Perubahan versi (`instVersion`) mungkin menunjukkan adanya penyesuaian jadwal, yang bisa jadi tanda masalah.

**What to analyze:**  
- Rata-rata jumlah versi per pinjaman.

**Kesimpulan Teknis – Group 3:**
_(Kosong)_

**🛠️ Feature Engineering Recommendations:**
_(Kosong)_

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

**Kesimpulan Teknis – Group 1:**
_(Kosong)_

**🛠️ Feature Engineering Recommendations:**
_(Kosong)_

---

### Group 2: Penarikan dan Pembayaran

**Columns involved:** `ccDrawCurrent`, `ccPayment`, `ccPaymentTotal`  
**Hypothesis:**  
- Nasabah yang sering menarik dana (`ccDrawCurrent`) mungkin memiliki kebutuhan finansial yang tinggi.  
- Rasio pembayaran terhadap penarikan dapat menunjukkan kemampuan membayar.

**What to analyze:**  
- Rata-rata total penarikan dan total pembayaran per target.  
- Rasio pembayaran/penarikan per target.

**Kesimpulan Teknis – Group 2:**
_(Kosong)_

**🛠️ Feature Engineering Recommendations:**
_(Kosong)_

---

### Group 3: Status dan DPD

**Columns involved:** `ccContractStatus`, `ccDpd`, `ccDpdDef`  
**Hypothesis:**  
- Status kartu kredit dan DPD memberikan sinyal yang sama dengan POS_CASH.

**What to analyze:**  
- Rata-rata DPD maksimum per nasabah.

**Kesimpulan Teknis – Group 3:**
_(Kosong)_

**🛠️ Feature Engineering Recommendations:**
_(Kosong)_

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