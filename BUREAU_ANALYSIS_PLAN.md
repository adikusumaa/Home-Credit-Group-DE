# Project Plan: Analyzing Bureau & Bureau Balance Data with Application Target

**Objective:**  
Understand how historical credit bureau data (from `bureau` and `bureau_balance` tables) influences the likelihood of default (`target`) in the current loan application. This analysis will help identify key risk factors and guide feature engineering for the Gold Layer.

**Approach:**  
We will group columns into logical categories based on business meaning. For each group, we will formulate a hypothesis and then test it by aggregating and comparing metrics between defaulted (`target=1`) and non-defaulted (`target=0`) customers.

---

## Group 1: Credit Active Status (`creditActive`)

**Columns involved:** `creditActive`  
**Hypothesis:**  
- Customers with many **active** loans at the credit bureau are under greater financial pressure and thus have a higher default rate.  
- Customers whose loans are all **closed** may be more responsible or have settled past debts, leading to lower risk.

**What to analyze:**  
- Distribution of `target` across each `creditActive` value (`Active`, `Closed`, `Sold`, etc.).  
- Compare average number of active loans per customer between defaulters and non-defaulters.

 Kesimpulan Teknis – Group 1: Credit Active Status
creditActive	Total Loans	Default Rate	Interpretation
Sold	80,605	9.44%	Highest risk – indicates severe past delinquency (debt sold to collector). Strong red flag.
Active	3,860,307	8.31%	Moderate risk – ongoing credit obligations create financial pressure.
Closed	11,702,435	6.52%	Lowest risk – reflects responsible repayment behavior and completed credit history.
Bad debt	75	5.33%	Inconclusive – extremely small sample size; not statistically reliable.
Key metrics for Active loans per customer:

Target Group	Avg. Active Loans per Customer
Default (1)	15.74
Non-default (0)	14.56
Difference: ~1.18 active loans on average between defaulters and non-defaulters.

Statistical significance: Though the difference is modest, the large sample size (hundreds of thousands) confirms a consistent trend: higher number of active bureau loans is associated with elevated default risk.

🛠️ Feature Engineering Recommendations for Gold Layer
Create binary flags for creditActive statuses:

has_sold = 1 if any bureau loan is 'Sold', else 0.

has_active = 1 if at least one loan is 'Active'.

all_closed = 1 if all bureau loans are 'Closed'.

Use active_loan_count (number of active loans per customer) as a numeric feature. Consider capping outliers (e.g., upper 99th percentile) to avoid skew.

Ignore Bad debt as a separate category due to low occurrence; either merge with 'Sold' or treat as noise.

Final Notes:

creditActive status provides a strong categorical signal that should be included in the model.

The count of active loans is a weak-to-moderate predictor; use it as an auxiliary feature rather than a primary one.


---

## Group 2: Credit Debt and Utilization

**Columns involved:**  
`creditSum` (total credit amount), `debtSum` (current debt), `creditLimit` (credit limit), `overdueSum` (overdue amount)  
**Hypothesis:**  
- High `debtSum` and low `creditLimit` (i.e., high credit utilization) are strong indicators of financial strain.  
- Large `overdueSum` directly points to past payment problems.

**What to analyze:**  
- Average `debtSum`, `creditSum`, and `overdueSum` for defaulters vs. non-defaulters.  
- For each customer, compute:  
  - `utilization_ratio = debtSum / creditLimit` (where creditLimit > 0)  
  - `overdue_ratio = overdueSum / debtSum` (proportion of debt overdue)  
- Compare these ratios between the two target groups.


Analisis Temuan Group 2: Credit Debt and Utilization
1. overdueSum (Jumlah Tunggakan) → Sinyal Bahaya Paling Kuat
target	avg_overdue_sum
1 (Gagal)	57,65
0 (Lancar)	10,76
Kesimpulan: Rata-rata tunggakan nasabah gagal bayar 5,3 kali lebih besar daripada nasabah lancar. Ini adalah sinyal yang sangat valid dan independen. Nominal tunggakan yang tinggi di biro kredit lain secara langsung membuktikan ketidakmampuan membayar di masa lalu.

2. creditSum vs debtSum → Anomali yang Menceritakan Beban
target	avg_credit_sum	avg_debt_sum
1 (Gagal)	299.081	96.937
0 (Lancar)	341.344	92.014
Anomali: Nasabah yang gagal bayar (target=1) justru memiliki total pinjaman (creditSum) yang lebih kecil dibandingkan yang lancar, tetapi sisa utangnya (debtSum) lebih besar.

Logika bisnis: Ini menunjukkan bahwa nasabah gagal bayar mungkin memiliki akses kredit yang lebih terbatas (pinjaman lebih kecil), namun mereka tidak mampu melunasi bahkan pinjaman kecil tersebut, sehingga utangnya menumpuk akibat bunga atau denda. Sedangkan nasabah lancar bisa meminjam lebih banyak, tapi mampu melunasi sebagian besarnya.

3. utilization_ratio (Rasio Utilisasi) → Data Bermasalah, Tapi Sinyal Tetap Ada
target	avg_utilization_ratio
1	15,63
0	6,90
Anomali Teknis: Angka 15,63 tidak mungkin sebagai rasio (0-1). Ini terjadi karena sebagian besar pinjaman di biro kredit (seperti pinjaman tunai) tidak memiliki nilai creditLimit, sehingga bernilai 0 atau NULL. Saat dilakukan pembagian debtSum / creditLimit, angka tersebut menjadi sangat besar (tak hingga).

Solusi Analisis: Kita harus melihat distribusi berdasarkan grup utilisasi yang lebih realistis, yang Anda sudah jalankan.

4. util_group (Kelompok Utilisasi) → Sinyal yang Valid (dengan Catatan)
util_group	total_records	default_rate
Tinggi (>70%)	219.472	11,91%
Tidak ada limit	15.182.715	6,90%
Sedang (30-70%)	18.705	6,88%
Rendah (<30%)	222.530	6,72%
Kesimpulan: Nasabah yang memiliki batas kredit (creditLimit) dan sudah menggunakan lebih dari 70% limitnya (Tinggi >70%) memiliki risiko gagal bayar jauh lebih tinggi (11,9%) dibandingkan rata-rata dataset.

Data Mayoritas: Sebagian besar data (15 juta record) masuk kategori Tidak ada limit. Ini berarti fitur creditLimit sering kosong, dan kita tidak bisa mengandalkan rasio untuk seluruh populasi. Namun, untuk subset data yang memiliki limit, sinyalnya sangat kuat.

📌 Kesimpulan Teknis – Group 2 (Credit Debt and Utilization)
Metric	Insight	Impact on Risk
overdueSum	Defaulters have ~5x higher overdue amount.	Very Strong
creditSum	Defaulters actually have lower total credit access.	Weak / Contextual
debtSum	Defaulters have slightly higher remaining debt.	Moderate
avg_utilization_ratio	Prone to extreme values due to missing creditLimit.	Unreliable as-is
util_group = 'Tinggi (>70%)'	High utilization group has ~11.9% default rate (vs ~6.9% baseline).	Strong (subset)
util_group = 'Tidak ada limit'	Majority of data (15M+ records) falls here.	Neutral
🛠️ Feature Engineering Recommendations for Gold Layer
Gunakan overdueSum sebagai fitur numerik utama.

Karena nilainya sangat bervariasi, Anda bisa menormalisasinya dengan log(overdueSum + 1) atau mengelompokkannya menjadi kategori (0, Kecil, Besar).

Jangan gunakan rasio debtSum / creditLimit secara mentah karena data limit sering kosong.

Buat fitur kategorikal dari util_group:

is_high_utilization = 1 jika util_group = 'Tinggi (>70%)'.

has_credit_limit = 1 jika creditLimit > 0.

Kedua fitur biner ini bisa langsung dipakai tanpa merusak statistik model.

Gunakan debtSum dengan hati-hati.

Karena rata-rata pinjaman (creditSum) lebih tinggi pada nasabah lancar, kita tidak bisa menyimpulkan "pinjaman kecil berisiko". Jangan jadikan debtSum sebagai prediktor utama, tapi fitur ini tetap bisa digunakan sebagai pelengkap.

Kesimpulan untuk Gold Layer:

Wajib pakai: overdueSum, is_high_utilization.

Opsional: debtSum, has_credit_limit.

Abaikan: avg_utilization_ratio mentah.
---

## Group 3: Overdue Days and Delinquency Indicators

**Columns involved:**  
`overdueDays`, `maxOverdue`, `daysCreditUpdate`  
**Hypothesis:**  
- Longer `overdueDays` and higher `maxOverdue` are clear signals of past delinquency and should correlate strongly with default.  
- A recent `daysCreditUpdate` (i.e., small absolute value) might indicate fresh information, possibly reflecting a recent change in credit status.

**What to analyze:**  
- Average `overdueDays` and `maxOverdue` per customer for each target group.  
- Distribution of `maxOverdue` (e.g., >0 vs =0) and its impact on default.  
- How does the recency of the credit update (`daysCreditUpdate`) affect risk? (e.g., very recent updates might be more reliable, or could indicate recent changes).


esimpulan Teknis – Group 3 (Overdue Days & Delinquency Indicators)
Metric	Insight	Rekomendasi untuk Fitur
overdueDays	Hampir tidak ada perbedaan (0,99 vs 0,97).	Jangan digunakan (tidak informatif).
maxOverdue	Lebih tinggi pada nasabah lancar (anomali data).	Abaikan (rentan noise).
overdue_severity	Nasabah dengan tunggakan memiliki risiko 2% lebih tinggi.	Gunakan sebagai fitur biner: ever_overdue = 1 jika maxOverdue > 0, else 0.
update_recency	Data < 30 hari memiliki risiko tertinggi (8,86%).	Gunakan sebagai fitur biner: is_recent_update = 1 jika daysCreditUpdate >= -30, else 0.
🛠️ Feature Engineering Recommendations for Gold Layer
Berdasarkan Group 3, fitur-fitur berikut yang paling direkomendasikan:

ever_overdue (Binary): Menandakan apakah nasabah pernah memiliki tunggakan nominal (maxOverdue > 0) di masa lalu.

Meskipun pengaruhnya sedang, ini tetap memberi sinyal tambahan yang valid.

is_recent_update (Binary): Menandakan apakah data terakhir diperbarui dalam 30 hari terakhir (daysCreditUpdate >= -30).

Ini adalah fitur wajib! Data terbaru adalah indikator paling kuat dari ketidakstabilan nasabah saat ini.

Abaikan overdueDays dan maxOverdue mentah karena lemah dan anomali.

💡 Ringkasan Akhir untuk Anda (Analisis Silang)
Setelah 3 Group yang kita analisis, kita sudah mendapatkan gambaran kuat:

Group 1: Status pinjaman (Active / Closed / Sold) memberikan sinyal dasar.

Group 2: overdueSum (nominal tunggakan) dan utilization > 70% memberikan sinyal keuangan yang kuat.

Group 3: Kesegaran data (is_recent_update) ternyata lebih penting daripada riwayat tunggakan parah di masa lalu.
---

## Group 4: Credit Type (`creditType`)

**Columns involved:** `creditType`  
**Hypothesis:**  
- Different types of credit (e.g., `Consumer credit`, `Credit card`, `Car loan`) have inherently different risk profiles.  
- For example, mortgage-like loans may be more stable, while credit card debt could be more risky due to revolving nature.

**What to analyze:**  
- Default rate for each `creditType`.  
- Are there certain credit types that appear more frequently among defaulters?

Kesimpulan Teknis – Group 4 (Credit Type)
creditType	Risiko	Rekomendasi untuk Fitur
Microloan	Sangat Tinggi (16,2%)	Wajib dibuat fitur biner: is_microloan = 1 jika ada pinjaman tipe ini.
Credit card	Menengah (7,9%)	Bisa digunakan sebagai fitur biner: has_credit_card = 1 jika ada pinjaman kartu kredit. Efeknya sedang, tapi valid.
Car loan / Mortgage	Rendah (<5%)	Bisa digunakan sebagai fitur biner: has_collateral_loan = 1 jika ada pinjaman beragunan (Car/Mortgage). Ini menandakan stabilitas.
Consumer credit	Menengah (6,8%)	Jangan dijadikan fitur. Karena sangat dominan, kolom ini sudah tercakup oleh fitur lain.
Loan for equipment / Interbank / Mobile	Tidak valid (sample kecil)	Abaikan. Jika dipaksa, masukkan ke kategori Others.
Unknown type / Another type	Tidak jelas	Gabungkan ke Others agar tidak menambah noise.
🛠️ Feature Engineering Recommendations for Gold Layer
Berdasarkan Group 4, fitur-fitur yang paling direkomendasikan (hanya 3 fitur biner):

is_microloan: 1 jika creditType = 'Microloan' muncul di data biro kredit.
Sangat kuat dan valid (16% default rate).

has_credit_card: 1 jika creditType = 'Credit card' muncul.
Sinyal moderat, tapi tetap berguna.

has_collateral_loan: 1 jika creditType adalah 'Car loan' atau 'Mortgage'.
Menandakan nasabah yang disiplin dan memiliki aset.

Fitur yang TIDAK PERLU dibuat:

is_consumer_credit (terlalu dominan, tidak membedakan).

is_loan_for_equipment (sample kecil, tidak reliable).

creditType mentah sebagai kolom one-hot (terlalu banyak kategori, akan menyebabkan overfitting).

💡 Ringkasan Akhir untuk Anda
Dari Group 4, kita belajar bahwa jenis pinjaman memberikan sinyal yang valid, terutama untuk kategori ekstrem seperti Microloan dan Car loan/Mortgage. Namun, jangan pernah memasukkan semua nilai asli creditType ke dalam model. Cukup buat 3 fitur biner di atas, dan model ML Anda akan menangkap esensi risiko tanpa terjebak noise.

Sekarang, setelah kita menyelesaikan Group 4, kita sudah memiliki gambaran yang kuat tentang:

Group 1: Status pinjaman (Active, Sold, Closed) → sudah kuat.

Group 2: Nominal utang (overdueSum, utilisasi > 70%) → sangat kuat.

Group 3: Kesegaran data (is_recent_update) → paling kuat!

Group 4: Jenis pinjaman (is_microloan, has_collateral_loan) → kuat.
---

## Group 5: Bureau Balance Status (`status` from `bureau_balance`)

**Columns involved:** `status` (monthly status: `C`, `0`, `1`, `2`, `3`, `4`, `5`, `X`)  
**Hypothesis:**  
- The more months a customer has a status indicating delinquency (`1` to `5`), the higher the default risk.  
- Frequent `C` (closed) or `0` (no overdue) statuses indicate healthy repayment behavior.

**What to analyze:**  
- For each customer, count the number of months with status `1`–`5` (delinquent months).  
- Compare the average number of delinquent months between defaulters and non-defaulters.  
- Also compute:  
  - `max_status` (the worst status ever recorded)  
  - `avg_status_score` (numeric conversion: `0` for `C`/`X`, and `1`–`5` for status codes)  
- See how these metrics vary by target.


Kesimpulan Teknis – Group 5 (Bureau Balance Status)
Metric	Insight	Rekomendasi untuk Fitur
delinquent_months	Semakin banyak bulan tunggakan, semakin tinggi risiko.	Wajib digunakan. Bisa sebagai numerik (delinquent_months) atau kategorikal (0, 1, 2, 3+).
max_status	Status terburuk 5 sangat berisiko.	Gunakan sebagai fitur biner: ever_delinquent = 1 jika max_status > 0, dan ever_status_5 = 1 jika max_status = 5.
avg_status_score	Perbedaan kecil dan redundan dengan delinquent_months.	Abaikan (tidak menambah sinyal baru).
🛠️ Feature Engineering Recommendations for Gold Layer
Berdasarkan temuan di atas, berikut fitur-fitur yang direkomendasikan dari Group 5:

delinquent_months (Numerik) – Jumlah bulan dengan status tunggakan (1–5).
Jika ingin lebih sederhana, buat kategori: delinquent_category = 0 (0 bulan), 1 (1 bulan), 2 (2 bulan), 3+ (3+ bulan).

ever_delinquent (Binary) – 1 jika nasabah pernah menunggak (max_status > 0), 0 jika tidak.
Ini menangkap sinyal dasar “pernah bermasalah”.

ever_status_5 (Binary) – 1 jika nasabah pernah mencapai status 5 (max_status = 5).
Ini adalah red flag terkuat dari Group 5.

Fitur yang TIDAK perlu dibuat:

avg_status_score – terlalu kecil nilainya dan redundan dengan delinquent_months.

One-hot encoding untuk setiap status (1,2,3,4,5) – akan menyebabkan overfitting karena jumlah sample untuk status 2-4 kecil.

💡 Ringkasan Akhir untuk Anda
Dari Group 5, kita belajar bahwa perilaku pembayaran bulanan di biro kredit memberikan sinyal yang kuat, terutama:

Jumlah bulan menunggak (delinquent_months).

Pernah mencapai status terburuk (ever_status_5).

Kedua fitur ini harus masuk ke dalam tabel Gold Layer Anda.
---

## Group 6: Bureau Balance Time Series (`monthsBalance`)

**Columns involved:** `monthsBalance` (month index relative to application date)  
**Hypothesis:**  
- The length of the balance history (`min` to `max` months) may indicate how long the customer has been tracked.  
- Recent negative trends (e.g., statuses getting worse in the last few months) could be more predictive than old history.

**What to analyze:**  
- For each customer, compute:  
  - `history_length = max(monthsBalance) - min(monthsBalance)`  
  - `recent_status_avg` (average status over the last 3 months)  
- Compare these time-series derived metrics between target groups.

Analisis Temuan Group 6: Bureau Balance Time Series
1. Rata-rata Metrik Time-Series (history_length, avg_status_score, recent_status_avg)
Target	avg_history_length	avg_avg_status_score	avg_recent_status_avg
0 (Lancar)	56,16 bulan	0,029	0,026
1 (Gagal)	48,81 bulan	0,051	0,045
Analisis:

Anomali Panjang Riwayat: Nasabah yang gagal bayar (target=1) justru memiliki rata-rata riwayat kredit yang lebih pendek (48,8 bulan) dibandingkan yang lancar (56,2 bulan). Ini menandakan bahwa nasabah dengan riwayat kredit yang sangat panjang (>4,5 tahun) cenderung lebih stabil dan mampu mengelola utang. Sedangkan yang gagal bayar mungkin adalah nasabah yang baru “terjun” ke dunia kredit dan belum terbiasa mengatur beban cicilan.

Status Terkini vs Keseluruhan: Pada defaulter, avg_recent_status_avg (0,045) lebih rendah daripada avg_avg_status_score (0,051). Ini secara tidak langsung menunjukkan bahwa status mereka cenderung membaik sedikit sebelum pengajuan, tapi tetap saja gagal bayar karena faktor lain.

2. Analisis Tren (Memburuk, Membaik, Stabil) -> Sinyal Paling Kuat!
Trend	total_customers	default_rate
Memburuk	7.179	12,66%
Membaik	23.103	9,01%
Stabil	61.949	7,30%
Insight Kunci:

Trend Memburuk adalah red flag terkuat di Group 6. Nasabah yang status kreditnya memburuk dalam 3 bulan terakhir (dari 0 ke 2, misalnya) memiliki risiko gagal bayar 12,66%, jauh di atas rata-rata dataset.

Tren Membaik memiliki risiko 9,01% (masih di atas rata-rata). Artinya, meskipun mereka mulai membaik, beban masa lalu masih membayangi.

Trend Stabil memiliki risiko paling rendah (7,30%), yang berarti status kredit yang konsisten adalah tanda nasabah yang aman.

Kesimpulan: Jangan hanya lihat angka statusnya, tapi arah perubahannya (trend). Memburuk dalam 3 bulan terakhir adalah indikator kegagalan yang sangat akurat.

3. Dampak Panjang Riwayat (history_length_group) -> Sinyal Valid
History Length Group	total_customers	default_rate
Pendek (≤6 bulan)	3.253	14,29%
Sedang (7-12 bulan)	4.137	11,68%
Panjang (13-24 bulan)	9.317	10,99%
Sangat Panjang (>24 bulan)	75.524	7,33%
Analisis:

Terdapat korelasi negatif yang jelas: Semakin pendek riwayat kredit, semakin tinggi default rate.

Nasabah dengan riwayat Sangat Panjang (>24 bulan) memiliki risiko paling rendah, karena mereka sudah membuktikan kemampuan mengelola kredit dalam jangka panjang.

Nasabah dengan riwayat Pendek (≤6 bulan) sangat berisiko (14,29%), kemungkinan besar karena mereka adalah first-time borrowers atau orang yang baru saja mendapatkan akses kredit dengan tiba-tiba dan belum bisa mengendalikan beban utang.

📌 Kesimpulan Teknis – Group 6 (Bureau Balance Time Series)
Metric	Insight	Rekomendasi untuk Fitur
trend (Memburuk)	Red flag terkuat (12,66% default rate).	Wajib digunakan sebagai fitur biner: is_worsening_trend = 1 jika recent_status_avg > avg_status_score_overall, else 0.
history_length	Riwayat pendek sangat berisiko.	Wajib digunakan. Bisa sebagai numerik (history_length) atau kategorikal (Pendek, Sedang, Panjang).
avg_status_score_overall	Redundan dengan delinquent_months dari Group 5.	Abaikan (tidak perlu dimasukkan).
recent_status_avg	Angka mentahnya sudah diwakili oleh trend.	Abaikan (cukup pakai is_worsening_trend).
🛠️ Feature Engineering Recommendations for Gold Layer
Berdasarkan Group 6, fitur-fitur yang paling direkomendasikan:

is_worsening_trend (Binary) – 1 jika recent_status_avg > avg_status_score_overall, 0 jika sebaliknya.
Ini adalah fitur wajib! Menangkap nasabah yang sedang dalam tekanan keuangan saat ini.

history_length (Numerik) – Jumlah bulan riwayat tercatat.
Jika ingin disederhanakan, gunakan kategori history_length_group.
(Catatan: Karena jumlah sampel yang panjang sangat dominan, pastikan untuk melakukan capping pada nilai ekstrem).

Fitur yang TIDAK perlu dibuat:

avg_status_score_overall (redundan dengan Group 5).

recent_status_avg (karena sinyalnya lebih kuat saat diubah menjadi trend).

💡 Ringkasan Akhir untuk Anda
Dari Group 6, kita belajar bahwa perilaku time-series (waktu) memberikan wawasan yang tidak bisa didapat dari snapshot statis:

Tren yang memburuk adalah peringatan dini paling kuat untuk gagal bayar.

Riwayat kredit yang panjang (>2 tahun) adalah penanda stabilitas dan kepercayaan.

Riwayat yang sangat pendek (<6 bulan) menandakan nasabah baru yang belum teruji, sehingga risikonya sangat tinggi.

---

## Group 7: Combined Metrics (Per Customer)

**Hypothesis:**  
- A single summary per customer that combines multiple bureau signals might be the strongest predictor.  
- For example, a customer with high `debtSum`, high `overdueDays`, and frequent delinquent statuses is likely very risky.

**What to analyze:**  
- Create a composite score (e.g., sum of normalized `overdueDays`, `debtSum`, and `delinquent_months`) and see how it correlates with `target`.  
- Alternatively, use simple averages and totals to build a profile per customer.

Kesimpulan Teknis – Group 7 (Combined Metrics)
Pendekatan	Hasil	Rekomendasi
Skor Komposit	Tidak informatif (sebagian besar skor < 0.25) karena outlier.	Jangan gunakan dalam bentuk ini. Perbaiki dengan winsorization atau log-transform sebelum normalisasi.
Rasio Utang/Pendapatan	Data mentah menghasilkan banyak grup kecil.	Gunakan bucket (misal <1, 1-3, 3-5, >5) untuk analisis yang valid.
🛠️ Feature Engineering Recommendations untuk Gold Layer
Meskipun skor komposit belum optimal, fitur rasio utang terhadap pendapatan (setelah dibucket) sangat potensial. Saya rekomendasikan:

debt_ratio_bucket – Kategorikal dengan 4 level risiko:

Ringan (<1x)

Sedang (1-3x)

Berat (3-5x)

Sangat Berat (>5x)

Untuk skor komposit, setelah diperbaiki dengan persentil, fitur ini bisa digunakan sebagai pelengkap, bukan fitur utama.

Fitur yang TIDAK perlu dibuat:

composite_score mentah (sebelum diperbaiki).

debt_to_income_ratio langsung (tanpa bucket).

💡 Ringkasan Akhir untuk Anda
Group 7 mengajarkan bahwa model sederhana (skor komposit) tidak selalu lebih baik, dan normalisasi harus memperhatikan outlier.
Namun, rasio utang/pendapatan adalah metrik yang sangat kuat secara bisnis—selama kita mengelompokkannya dengan benar.

---

## Group 8: Number of Bureau Loans (`count` of `bureauId` per `loanId`)

**Hypothesis:**  
- Customers with many credit bureau loans (especially active ones) are over-leveraged and more likely to default.

**What to analyze:**  
- Count the number of distinct `bureauId` per `loanId`.  
- Compare average count between defaulters and non-defaulters.  
- Also analyze the distribution of credit counts across target groups.


Kesimpulan Teknis – Group 8 (Number of Bureau Loans)
Metrik	Insight	Rekomendasi untuk Fitur
total_bureau_loans	Tidak berkorelasi (defaulters justru lebih sedikit).	Tidak digunakan (tidak informatif).
active_bureau_loans	Defaulters memiliki lebih banyak pinjaman aktif.	Wajib digunakan sebagai numerik.
closed_bureau_loans	Defaulters memiliki lebih sedikit pinjaman lunas.	Wajib digunakan sebagai numerik.
sold_bureau_loans	Defaulters memiliki lebih banyak pinjaman macet.	Wajib digunakan sebagai numerik.
active_ratio	Analisis langsung tidak valid (jebakan bucket 1 sampel).	Jangan pakai mentah. Bucketkan menjadi 4 rentang jika ingin dipakai.
loan_count_bucket	Selisih risiko sangat kecil (<1%).	Tidak digunakan (tidak informatif).
🛠️ Feature Engineering Recommendations for Gold Layer
Berdasarkan Group 8, fitur-fitur yang paling direkomendasikan:

active_bureau_loans (Numerik) – Jumlah pinjaman aktif.
Ini adalah sinyal valid: semakin banyak, semakin berisiko.

closed_bureau_loans (Numerik) – Jumlah pinjaman yang sudah lunas.
Sinyal valid: semakin banyak, semakin aman.

sold_bureau_loans (Numerik) – Jumlah pinjaman yang macet dan dijual.
Sinyal valid, meskipun angkanya kecil.

Fitur yang TIDAK perlu dibuat:

total_bureau_loans (tidak informatif).

loan_count_bucket (tidak informatif).

Fitur Opsional (jika ingin dibuat):

active_ratio_bucket – Rasio pinjaman aktif yang sudah di-bucket (misal: 0-25%, 25-50%, 50-75%, >75%).


---

## Important Considerations

- Because the relationship is **one-to-many** (one `loanId` can have many bureau records), we must **aggregate** per `loanId` before comparing with `target`.  
- All analyses should be done at the **customer (`loanId`) level**, not at the individual bureau record level.  
- For each group, we will generate aggregated tables (e.g., `AVG`, `SUM`, `COUNT`, `MAX`) and then join with `application` to get `target`.  
- The final output of this project will be a set of insights that will directly inform which bureau-derived features to include in the Gold Layer.

---

**Next Steps:**  
1. Write aggregation queries for each group.  
2. Join the aggregated results with `application`.  
3. Run EDA on the combined dataset and record conclusions.  
4. Prioritize features based on observed impact and business logic.