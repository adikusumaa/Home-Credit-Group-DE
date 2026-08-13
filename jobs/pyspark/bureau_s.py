# clean_bureau.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum, when, count, avg, max, min, abs

spark = SparkSession.builder.appName("Silver_Bureau").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

ENV = "dev"
BRONZE_BASE = f"hdfs://namenode:8020/data/{ENV}/bronze/home_credit/raw"
SILVER_BASE = f"hdfs://namenode:8020/data/{ENV}/silver/staging"

# Read raw
bureau = spark.read.csv(f"{BRONZE_BASE}/bureau.csv", header=True, inferSchema=True)
bureau_balance = spark.read.csv(f"{BRONZE_BASE}/bureau_balance.csv", header=True, inferSchema=True)

# Register views
bureau.createOrReplaceTempView("bureau")
bureau_balance.createOrReplaceTempView("bureau_balance")

# Rename columns for clarity
bureau_renamed = spark.sql("""
SELECT
    SK_ID_CURR AS loanId,
    SK_ID_BUREAU AS bureauId,
    CREDIT_ACTIVE AS creditActive,
    CREDIT_CURRENCY AS creditCurrency,
    DAYS_CREDIT AS daysCredit,
    CREDIT_DAY_OVERDUE AS overdueDays,
    DAYS_CREDIT_ENDDATE AS creditEndDays,
    DAYS_ENDDATE_FACT AS enddateFact,
    AMT_CREDIT_MAX_OVERDUE AS maxOverdue,
    CNT_CREDIT_PROLONG AS prolongCount,
    AMT_CREDIT_SUM AS creditSum,
    AMT_CREDIT_SUM_DEBT AS debtSum,
    AMT_CREDIT_SUM_LIMIT AS creditLimit,
    AMT_CREDIT_SUM_OVERDUE AS overdueSum,
    CREDIT_TYPE AS creditType,
    DAYS_CREDIT_UPDATE AS daysCreditUpdate,
    AMT_ANNUITY AS annuityAmt
FROM bureau
""")
bureau_renamed.createOrReplaceTempView("bureau_renamed")

bureau_balance_renamed = spark.sql("""
SELECT
    SK_ID_BUREAU AS bureauId,
    MONTHS_BALANCE AS monthsBalance,
    STATUS AS status
FROM bureau_balance
""")
bureau_balance_renamed.createOrReplaceTempView("bureau_balance_renamed")

# Join bureau and bureau_balance per bureauId
main_bureau = spark.sql("""
SELECT
    a.loanId,
    a.bureauId AS bureau_id,
    a.creditActive,
    a.daysCredit,
    a.overdueDays,
    a.maxOverdue,
    a.creditSum,
    a.debtSum,
    a.creditLimit,
    a.overdueSum,
    a.creditType,
    a.daysCreditUpdate,
    b.monthsBalance,
    b.status
FROM bureau_renamed a
LEFT JOIN bureau_balance_renamed b ON a.bureauId = b.bureauId
""")
main_bureau.createOrReplaceTempView("main_bureau")

# Aggregate per loanId and generate all features from groups 1-8
bureau_features = spark.sql("""
WITH bureau_agg AS (
    SELECT
        loanId,
        COUNT(bureau_id) AS total_bureau_loans,
        SUM(CASE WHEN creditActive = 'Active' THEN 1 ELSE 0 END) AS active_bureau_loans,
        SUM(CASE WHEN creditActive = 'Closed' THEN 1 ELSE 0 END) AS closed_bureau_loans,
        SUM(CASE WHEN creditActive = 'Sold' THEN 1 ELSE 0 END) AS sold_bureau_loans,
        SUM(CASE WHEN creditActive = 'Active' THEN 1 ELSE 0 END) AS active_loan_count,  -- same as active_bureau_loans
        MAX(CASE WHEN creditActive = 'Sold' THEN 1 ELSE 0 END) AS has_sold,
        MAX(CASE WHEN creditActive = 'Active' THEN 1 ELSE 0 END) AS has_active,
        MIN(CASE WHEN creditActive = 'Closed' THEN 1 ELSE 0 END) AS all_closed, -- not exactly; we need to check if all are closed.
        SUM(overdueSum) AS overdueSum,
        AVG(CASE WHEN creditLimit > 0 THEN debtSum/creditLimit ELSE 0 END) AS utilization_ratio,
        MAX(CASE WHEN creditLimit > 0 THEN 1 ELSE 0 END) AS has_credit_limit,
        MAX(CASE WHEN maxOverdue > 0 THEN 1 ELSE 0 END) AS ever_overdue,
        MAX(CASE WHEN daysCreditUpdate >= -30 THEN 1 ELSE 0 END) AS is_recent_update,
        MAX(CASE WHEN creditType = 'Microloan' THEN 1 ELSE 0 END) AS is_microloan,
        MAX(CASE WHEN creditType = 'Credit card' THEN 1 ELSE 0 END) AS has_credit_card,
        MAX(CASE WHEN creditType IN ('Car loan', 'Mortgage') THEN 1 ELSE 0 END) AS has_collateral_loan,
        SUM(CASE WHEN status IN ('1','2','3','4','5') THEN 1 ELSE 0 END) AS delinquent_months,
        MAX(CASE WHEN status IN ('1','2','3','4','5') THEN CAST(status AS INT) ELSE 0 END) AS max_status,
        MAX(CASE WHEN status = '5' THEN 1 ELSE 0 END) AS ever_status_5,
        MAX(monthsBalance) - MIN(monthsBalance) AS history_length,
        AVG(CASE WHEN monthsBalance >= -3 AND status IN ('1','2','3','4','5') THEN CAST(status AS INT) ELSE 0 END) AS recent_status_avg,
        AVG(CASE WHEN status IN ('1','2','3','4','5') THEN CAST(status AS INT) ELSE 0 END) AS avg_status_score_overall,
        MAX(CASE WHEN debtSum > 0 THEN 1 ELSE 0 END) AS ever_delinquent -- proxy
    FROM main_bureau
    GROUP BY loanId
)
SELECT
    loanId,
    -- Group 1
    has_sold,
    has_active,
    CASE WHEN sold_bureau_loans = 0 AND active_bureau_loans = 0 THEN 1 ELSE 0 END AS all_closed,
    active_loan_count,
    -- Group 2
    overdueSum,
    CASE WHEN utilization_ratio > 0.7 THEN 1 ELSE 0 END AS is_high_utilization,
    has_credit_limit,
    -- Group 3
    ever_overdue,
    is_recent_update,
    -- Group 4
    is_microloan,
    has_credit_card,
    has_collateral_loan,
    -- Group 5
    delinquent_months,
    CASE WHEN max_status > 0 THEN 1 ELSE 0 END AS ever_delinquent,
    ever_status_5,
    -- Group 6
    CASE WHEN recent_status_avg > avg_status_score_overall THEN 1 ELSE 0 END AS is_worsening_trend,
    history_length,
    -- Group 8
    active_bureau_loans,
    closed_bureau_loans,
    sold_bureau_loans
FROM bureau_agg
""")

# Write to Silver
bureau_features.coalesce(4).write.mode("overwrite").parquet(f"{SILVER_BASE}/bureau_features")

spark.stop()
print("Bureau Silver Layer completed.")