# gold_s.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit

spark = SparkSession.builder \
    .appName("Gold_Aggregation") \
    .enableHiveSupport() \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

ENV = "dev"  # dapat diganti dengan argumen --env
SILVER_BASE = f"hdfs://namenode:8020/data/{ENV}/silver/staging"
HIVE_DB = "gold"
HIVE_TABLE = "home_credit_gold"

# ============================================================
# 1. Baca semua data Silver dan buat temporary views
# ============================================================

# Application (train + test)
app_train = spark.read.parquet(f"{SILVER_BASE}/application_train_clean")
app_test = spark.read.parquet(f"{SILVER_BASE}/application_test_clean")

# Tambahkan kolom target untuk test (NULL)
app_test = app_test.withColumn("target", lit(None).cast("double"))

# Union
app_all = app_train.unionByName(app_test, allowMissingColumns=True)
app_all.createOrReplaceTempView("application")

# Bureau
bureau = spark.read.parquet(f"{SILVER_BASE}/bureau_features")
bureau.createOrReplaceTempView("bureau")

# Previous (termasuk POS, installments, credit card)
previous = spark.read.parquet(f"{SILVER_BASE}/previous_features")
previous.createOrReplaceTempView("previous")

# ============================================================
# 2. Gabungkan semua fitur menggunakan SQL JOIN
# ============================================================

gold_df = spark.sql("""
SELECT
    a.loanId,
    a.target,
    -- Application features (semua dari application_s.py)
    a.ageYears,
    a.gender,
    a.has_car,
    a.has_house,
    a.asset_profile,
    a.children_cnt,
    a.family_members,
    a.income_per_member,
    a.contract_type,
    a.credit_amt,
    a.annuity_amt,
    a.debt_to_income,
    a.payment_to_income,
    a.has_down_payment,
    a.income_type_group,
    a.occupation_risk_group,
    a.stability_score,
    a.commute_risk_profile,
    a.region_rate,
    a.is_dini_hari,
    a.EXT_SOURCE_1,
    a.EXT_SOURCE_2,
    a.EXT_SOURCE_3,
    a.days_phone_change,

    -- Bureau features (semua dari bureau_s.py)
    b.has_sold,
    b.has_active,
    b.all_closed,
    b.active_loan_count,
    b.overdueSum,
    b.is_high_utilization,
    b.has_credit_limit,
    b.ever_overdue,
    b.is_recent_update,
    b.is_microloan,
    b.has_credit_card,
    b.has_collateral_loan,
    b.delinquent_months,
    b.ever_delinquent,
    b.ever_status_5,
    b.is_worsening_trend,
    b.history_length,
    b.active_bureau_loans,
    b.closed_bureau_loans,
    b.sold_bureau_loans,

    -- Previous application features (semua dari previous_s.py)
    p.has_refused_prev,
    p.refused_count,
    p.is_high_risk_reason,
    p.is_recent_decision,
    p.has_pos_dpd,
    p.is_pos_high_risk,
    p.pos_history_length,
    p.is_pos_long_history,
    p.inst_late_ratio,
    p.is_inst_medium_late,
    p.inst_avg_payment_diff,
    p.inst_underpaid_freq,
    p.is_inst_version_0,
    p.cc_avg_utilization,
    p.is_cc_high_utilization,
    p.cc_recent_utilization,
    p.is_cc_low_pay_ratio,
    p.has_cc_activity,
    p.is_cc_accruing_debt

FROM application a
LEFT JOIN bureau b ON a.loanId = b.loanId
LEFT JOIN previous p ON a.loanId = p.loanId
""")

# ============================================================
# 3. Simpan ke Hive sebagai tabel Parquet
# ============================================================

gold_df.write.mode("overwrite") \
    .format("parquet") \
    .saveAsTable(f"{HIVE_DB}.{HIVE_TABLE}")

print(f"Gold table {HIVE_DB}.{HIVE_TABLE} created successfully.")

# Validasi sederhana
count = spark.sql(f"SELECT COUNT(*) FROM {HIVE_DB}.{HIVE_TABLE}").collect()[0][0]
print(f"Total rows in gold table: {count}")

spark.stop()