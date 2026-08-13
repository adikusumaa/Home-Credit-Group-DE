# previous_s.py
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Silver_Previous").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

ENV = "dev"
BRONZE_BASE = f"hdfs://namenode:8020/data/{ENV}/bronze/home_credit/raw"
SILVER_BASE = f"hdfs://namenode:8020/data/{ENV}/silver/staging"


prev_raw = spark.read.csv(f"{BRONZE_BASE}/previous_application.csv", header=True, inferSchema=True)
prev_raw.createOrReplaceTempView("prev_raw")

prev_features = spark.sql("""
WITH prev_agg AS (
    SELECT
        SK_ID_CURR AS loanId,
        COUNT(SK_ID_PREV) AS prev_count,
        SUM(CASE WHEN NAME_CONTRACT_STATUS = 'Refused' THEN 1 ELSE 0 END) AS refused_count,
        MAX(CASE WHEN NAME_CONTRACT_STATUS = 'Refused' THEN 1 ELSE 0 END) AS has_refused_prev,
        MAX(CASE WHEN CODE_REJECT_REASON IN ('SCOFR', 'LIMIT') THEN 1 ELSE 0 END) AS is_high_risk_reason,
        MAX(CASE WHEN DAYS_DECISION >= -30 THEN 1 ELSE 0 END) AS is_recent_decision
    FROM prev_raw
    GROUP BY SK_ID_CURR
)
SELECT
    loanId,
    has_refused_prev,
    refused_count,
    is_high_risk_reason,
    is_recent_decision
FROM prev_agg
""")
prev_features.createOrReplaceTempView("prev_features")


pos_raw = spark.read.csv(f"{BRONZE_BASE}/POS_CASH_balance.csv", header=True, inferSchema=True)
pos_raw.createOrReplaceTempView("pos_raw")

pos_features = spark.sql("""
WITH pos_agg_base AS (
    SELECT
        SK_ID_CURR AS loanId,
        MAX(CASE WHEN SK_DPD > 0 THEN 1 ELSE 0 END) AS has_pos_dpd,
        MAX(CASE WHEN CNT_INSTALMENT_FUTURE > 12 AND SK_DPD > 0 THEN 1 ELSE 0 END) AS is_pos_high_risk,
        MAX(MONTHS_BALANCE) AS max_month,
        MIN(MONTHS_BALANCE) AS min_month
    FROM pos_raw
    GROUP BY SK_ID_CURR
),
pos_agg AS (
    SELECT
        loanId,
        has_pos_dpd,
        is_pos_high_risk,
        max_month - min_month AS pos_history_length,
        CASE WHEN max_month - min_month > 24 THEN 1 ELSE 0 END AS is_pos_long_history
    FROM pos_agg_base
)
SELECT
    loanId,
    has_pos_dpd,
    is_pos_high_risk,
    pos_history_length,
    is_pos_long_history
FROM pos_agg
""")
pos_features.createOrReplaceTempView("pos_features")


inst_raw = spark.read.csv(f"{BRONZE_BASE}/installments_payments.csv", header=True, inferSchema=True)
inst_raw.createOrReplaceTempView("inst_raw")

inst_features = spark.sql("""
WITH inst_agg AS (
    SELECT
        SK_ID_CURR AS loanId,
        COUNT(*) AS total_c,
        SUM(CASE WHEN DAYS_ENTRY_PAYMENT > DAYS_INSTALMENT THEN 1 ELSE 0 END) AS late_count,
        AVG(DAYS_ENTRY_PAYMENT - DAYS_INSTALMENT) AS avg_late_days,
        AVG(AMT_PAYMENT - AMT_INSTALMENT) AS avg_payment_diff,
        MAX(CASE WHEN NUM_INSTALMENT_VERSION = 0 THEN 1 ELSE 0 END) AS is_inst_version_0,
        SUM(CASE WHEN AMT_PAYMENT < AMT_INSTALMENT THEN 1 ELSE 0 END) AS underpaid_count
    FROM inst_raw
    GROUP BY SK_ID_CURR
)
SELECT
    loanId,
    CASE WHEN total_c > 0 THEN late_count / total_c ELSE 0 END AS inst_late_ratio,
    CASE WHEN avg_late_days BETWEEN 6 AND 15 THEN 1 ELSE 0 END AS is_inst_medium_late,
    avg_payment_diff AS inst_avg_payment_diff,
    CASE 
        WHEN total_c > 0 AND underpaid_count / total_c > 0.3 THEN 'Sering'
        WHEN total_c > 0 AND underpaid_count / total_c > 0.1 THEN 'Sedang'
        WHEN total_c > 0 AND underpaid_count > 0 THEN 'Jarang'
        ELSE 'Tidak Pernah'
    END AS inst_underpaid_freq,
    is_inst_version_0
FROM inst_agg
""")
inst_features.createOrReplaceTempView("inst_features")

# ==================== 4. credit_card_balance ====================
cc_raw = spark.read.csv(f"{BRONZE_BASE}/credit_card_balance.csv", header=True, inferSchema=True)
cc_raw.createOrReplaceTempView("cc_raw")

cc_features = spark.sql("""
WITH cc_agg_base AS (
    SELECT
        SK_ID_CURR AS loanId,
        AVG(AMT_BALANCE / AMT_CREDIT_LIMIT_ACTUAL) AS cc_avg_utilization,
        MAX(CASE WHEN AMT_CREDIT_LIMIT_ACTUAL > 0 AND AMT_BALANCE / AMT_CREDIT_LIMIT_ACTUAL > 0.7 THEN 1 ELSE 0 END) AS is_cc_high_utilization,
        AVG(CASE WHEN MONTHS_BALANCE = -1 THEN AMT_BALANCE / AMT_CREDIT_LIMIT_ACTUAL ELSE NULL END) AS cc_recent_utilization,
        AVG(AMT_DRAWINGS_CURRENT) AS avg_draw,
        AVG(AMT_PAYMENT_CURRENT) AS avg_pay,
        MAX(CASE WHEN AMT_DRAWINGS_CURRENT > 0 THEN 1 ELSE 0 END) AS has_cc_activity,
        MAX(CASE WHEN AMT_DRAWINGS_CURRENT - AMT_PAYMENT_CURRENT > 0 
                  AND (AMT_DRAWINGS_CURRENT - AMT_PAYMENT_CURRENT) < 100000 THEN 1 ELSE 0 END) AS is_cc_accruing_debt
    FROM cc_raw
    GROUP BY SK_ID_CURR
),
cc_agg AS (
    SELECT
        loanId,
        cc_avg_utilization,
        is_cc_high_utilization,
        cc_recent_utilization,
        avg_draw,
        avg_pay,
        CASE WHEN avg_draw > 0 THEN avg_pay / avg_draw ELSE 0 END AS cc_pay_draw_ratio,
        CASE WHEN avg_draw > 0 AND avg_pay / avg_draw < 0.4 THEN 1 ELSE 0 END AS is_cc_low_pay_ratio,
        has_cc_activity,
        is_cc_accruing_debt
    FROM cc_agg_base
)
SELECT
    loanId,
    cc_avg_utilization,
    is_cc_high_utilization,
    cc_recent_utilization,
    is_cc_low_pay_ratio,
    has_cc_activity,
    is_cc_accruing_debt
FROM cc_agg
""")
cc_features.createOrReplaceTempView("cc_features")

# ==================== Combine all features per loanId ====================
full_previous = spark.sql("""
SELECT
    COALESCE(p.loanId, pos.loanId, i.loanId, c.loanId) AS loanId,
    p.has_refused_prev,
    p.refused_count,
    p.is_high_risk_reason,
    p.is_recent_decision,
    pos.has_pos_dpd,
    pos.is_pos_high_risk,
    pos.pos_history_length,
    pos.is_pos_long_history,
    i.inst_late_ratio,
    i.is_inst_medium_late,
    i.inst_avg_payment_diff,
    i.inst_underpaid_freq,
    i.is_inst_version_0,
    c.cc_avg_utilization,
    c.is_cc_high_utilization,
    c.cc_recent_utilization,
    c.is_cc_low_pay_ratio,
    c.has_cc_activity,
    c.is_cc_accruing_debt
FROM prev_features p
FULL OUTER JOIN pos_features pos ON p.loanId = pos.loanId
FULL OUTER JOIN inst_features i ON COALESCE(p.loanId, pos.loanId) = i.loanId
FULL OUTER JOIN cc_features c ON COALESCE(p.loanId, pos.loanId, i.loanId) = c.loanId
""")

# Write to Silver
full_previous.coalesce(4).write.mode("overwrite").parquet(f"{SILVER_BASE}/previous_features")

spark.stop()
print("Previous (POS, Installments, Credit Card) Silver Layer completed.")