from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("BureauCreditHistory") \
    .getOrCreate()

BASE = "hdfs://namenode:8020/data/silver/staging"

# 1. Clean bureau & bureau_balance & previous_application
def clean_bureau():
    df = spark.read.csv("hdfs://namenode:8020/data/bronze/home_credit/raw/bureau.csv", header=True, inferSchema=True)
    df.createOrReplaceTempView("bureau_raw")
    spark.sql("""
        CREATE OR REPLACE TEMP VIEW bureau_clean AS
        SELECT DISTINCT
            SK_ID_CURR, SK_ID_BUREAU, CREDIT_ACTIVE, CREDIT_CURRENCY,
            COALESCE(DAYS_CREDIT, 0) AS DAYS_CREDIT,
            COALESCE(CREDIT_DAY_OVERDUE, 0) AS CREDIT_DAY_OVERDUE,
            COALESCE(DAYS_CREDIT_ENDDATE, 0) AS DAYS_CREDIT_ENDDATE,
            COALESCE(DAYS_ENDDATE_FACT, 0) AS DAYS_ENDDATE_FACT,
            COALESCE(AMT_CREDIT_MAX_OVERDUE, 0) AS AMT_CREDIT_MAX_OVERDUE,
            COALESCE(CNT_CREDIT_PROLONG, 0) AS CNT_CREDIT_PROLONG,
            COALESCE(AMT_CREDIT_SUM, 0) AS AMT_CREDIT_SUM,
            COALESCE(AMT_CREDIT_SUM_DEBT, 0) AS AMT_CREDIT_SUM_DEBT,
            COALESCE(AMT_CREDIT_SUM_LIMIT, 0) AS AMT_CREDIT_SUM_LIMIT,
            COALESCE(AMT_CREDIT_SUM_OVERDUE, 0) AS AMT_CREDIT_SUM_OVERDUE,
            COALESCE(CREDIT_TYPE, 'Unknown') AS CREDIT_TYPE,
            COALESCE(DAYS_CREDIT_UPDATE, 0) AS DAYS_CREDIT_UPDATE,
            COALESCE(AMT_ANNUITY, 0) AS AMT_ANNUITY
        FROM bureau_raw
    """)
    spark.table("bureau_clean").coalesce(4).write.mode("overwrite").parquet(f"{BASE}/bureau_clean")

def clean_bureau_balance():
    df = spark.read.csv("hdfs://namenode:8020/data/bronze/home_credit/raw/bureau_balance.csv", header=True, inferSchema=True)
    df.createOrReplaceTempView("bb_raw")
    spark.sql("""
        CREATE OR REPLACE TEMP VIEW bb_clean AS
        SELECT DISTINCT SK_ID_BUREAU, MONTHS_BALANCE, COALESCE(STATUS, 'C') AS STATUS
        FROM bb_raw
    """)
    spark.table("bb_clean").coalesce(4).write.mode("overwrite").parquet(f"{BASE}/bureau_balance_clean")

def clean_previous_application():
    df = spark.read.csv("hdfs://namenode:8020/data/bronze/home_credit/raw/previous_application.csv", header=True, inferSchema=True)
    df.createOrReplaceTempView("prev_raw")
    spark.sql("""
        CREATE OR REPLACE TEMP VIEW prev_clean AS
        SELECT DISTINCT
            SK_ID_PREV, SK_ID_CURR,
            COALESCE(NAME_CONTRACT_TYPE, 'Unknown') AS NAME_CONTRACT_TYPE,
            COALESCE(AMT_ANNUITY, 0) AS AMT_ANNUITY,
            COALESCE(AMT_APPLICATION, 0) AS AMT_APPLICATION,
            COALESCE(AMT_CREDIT, 0) AS AMT_CREDIT,
            COALESCE(AMT_DOWN_PAYMENT, 0) AS AMT_DOWN_PAYMENT,
            COALESCE(AMT_GOODS_PRICE, 0) AS AMT_GOODS_PRICE,
            COALESCE(WEEKDAY_APPR_PROCESS_START, 'Unknown') AS WEEKDAY_APPR_PROCESS_START,
            COALESCE(HOUR_APPR_PROCESS_START, 0) AS HOUR_APPR_PROCESS_START,
            COALESCE(FLAG_LAST_APPL_PER_CONTRACT, 'N') AS FLAG_LAST_APPL_PER_CONTRACT,
            COALESCE(NFLAG_LAST_APPL_IN_DAY, 0) AS NFLAG_LAST_APPL_IN_DAY,
            COALESCE(RATE_DOWN_PAYMENT, 0) AS RATE_DOWN_PAYMENT,
            COALESCE(RATE_INTEREST_PRIMARY, 0) AS RATE_INTEREST_PRIMARY,
            COALESCE(RATE_INTEREST_PRIVILEGED, 0) AS RATE_INTEREST_PRIVILEGED,
            COALESCE(NAME_CASH_LOAN_PURPOSE, 'Unknown') AS NAME_CASH_LOAN_PURPOSE,
            COALESCE(NAME_CONTRACT_STATUS, 'Unknown') AS NAME_CONTRACT_STATUS,
            COALESCE(DAYS_DECISION, 0) AS DAYS_DECISION,
            COALESCE(NAME_PAYMENT_TYPE, 'Unknown') AS NAME_PAYMENT_TYPE,
            COALESCE(CODE_REJECT_REASON, 'Unknown') AS CODE_REJECT_REASON,
            COALESCE(NAME_TYPE_SUITE, 'Unknown') AS NAME_TYPE_SUITE,
            COALESCE(NAME_CLIENT_TYPE, 'Unknown') AS NAME_CLIENT_TYPE,
            COALESCE(NAME_GOODS_CATEGORY, 'Unknown') AS NAME_GOODS_CATEGORY,
            COALESCE(NAME_PORTFOLIO, 'Unknown') AS NAME_PORTFOLIO,
            COALESCE(NAME_PRODUCT_TYPE, 'Unknown') AS NAME_PRODUCT_TYPE,
            COALESCE(CHANNEL_TYPE, 'Unknown') AS CHANNEL_TYPE,
            COALESCE(SELLERPLACE_AREA, 0) AS SELLERPLACE_AREA,
            COALESCE(NAME_SELLER_INDUSTRY, 'Unknown') AS NAME_SELLER_INDUSTRY,
            COALESCE(CNT_PAYMENT, 0) AS CNT_PAYMENT,
            COALESCE(NAME_YIELD_GROUP, 'Unknown') AS NAME_YIELD_GROUP,
            COALESCE(PRODUCT_COMBINATION, 'Unknown') AS PRODUCT_COMBINATION,
            COALESCE(DAYS_FIRST_DRAWING, 0) AS DAYS_FIRST_DRAWING,
            COALESCE(DAYS_FIRST_DUE, 0) AS DAYS_FIRST_DUE,
            COALESCE(DAYS_LAST_DUE_1ST_VERSION, 0) AS DAYS_LAST_DUE_1ST_VERSION,
            COALESCE(DAYS_LAST_DUE, 0) AS DAYS_LAST_DUE,
            COALESCE(DAYS_TERMINATION, 0) AS DAYS_TERMINATION,
            COALESCE(NFLAG_INSURED_ON_APPROVAL, 0) AS NFLAG_INSURED_ON_APPROVAL
        FROM prev_raw
    """)
    spark.table("prev_clean").coalesce(4).write.mode("overwrite").parquet(f"{BASE}/previous_application_clean")

# 2. Feature Aggregation
def aggregate_bureau_features():
    spark.read.parquet(f"{BASE}/bureau_clean").createOrReplaceTempView("bureau_clean")
    spark.sql("""
        CREATE OR REPLACE TEMP VIEW bureau_credit_features AS
        SELECT SK_ID_CURR,
            COUNT(SK_ID_BUREAU) AS BUREAU_CNT,
            SUM(CASE WHEN CREDIT_ACTIVE='Active' THEN 1 ELSE 0 END) AS BUREAU_ACTIVE_CNT,
            SUM(CASE WHEN CREDIT_ACTIVE='Closed' THEN 1 ELSE 0 END) AS BUREAU_CLOSED_CNT,
            AVG(ABS(DAYS_CREDIT)/365.25) AS BUREAU_AVG_CREDIT_DURATION,
            MAX(AMT_CREDIT_MAX_OVERDUE) AS BUREAU_MAX_OVERDUE,
            AVG(AMT_CREDIT_MAX_OVERDUE) AS BUREAU_AVG_OVERDUE,
            SUM(AMT_CREDIT_SUM) AS BUREAU_TOTAL_CREDIT_SUM,
            SUM(AMT_CREDIT_SUM_DEBT) AS BUREAU_TOTAL_DEBT,
            CASE WHEN SUM(AMT_CREDIT_SUM)>0 THEN SUM(AMT_CREDIT_SUM_DEBT)/SUM(AMT_CREDIT_SUM) ELSE 0 END AS BUREAU_DEBT_CREDIT_RATIO,
            AVG(AMT_ANNUITY) AS BUREAU_AVG_ANNUITY,
            SUM(CNT_CREDIT_PROLONG) AS BUREAU_TOTAL_PROLONG,
            MAX(DAYS_CREDIT_UPDATE) AS BUREAU_DAYS_SINCE_LAST_UPDATE
        FROM bureau_clean
        GROUP BY SK_ID_CURR
    """)
    spark.table("bureau_credit_features").coalesce(4).write.mode("overwrite").parquet(f"{BASE}/bureau_credit_features")

def aggregate_bureau_delinquency():
    spark.read.parquet(f"{BASE}/bureau_balance_clean").createOrReplaceTempView("bb_clean")
    spark.read.parquet(f"{BASE}/bureau_clean").createOrReplaceTempView("bureau_clean")
    spark.sql("""
        CREATE OR REPLACE TEMP VIEW bureau_delinquency_features AS
        SELECT b.SK_ID_CURR,
            AVG(CASE WHEN bb.STATUS IN ('C','X') THEN 0 ELSE CAST(bb.STATUS AS INT) END) AS BB_AVG_STATUS,
            MAX(CASE WHEN bb.STATUS IN ('C','X') THEN 0 ELSE CAST(bb.STATUS AS INT) END) AS BB_MAX_STATUS,
            SUM(CASE WHEN bb.STATUS NOT IN ('C','X') AND CAST(bb.STATUS AS INT)>=1 THEN 1 ELSE 0 END) AS BB_OVERDUE_MONTHS,
            CASE WHEN COUNT(bb.MONTHS_BALANCE)>0 THEN SUM(CASE WHEN bb.STATUS NOT IN ('C','X') AND CAST(bb.STATUS AS INT)>=1 THEN 1 ELSE 0 END)*1.0/COUNT(bb.MONTHS_BALANCE) ELSE 0 END AS BB_OVERDUE_RATIO,
            MAX(bb.MONTHS_BALANCE)-MIN(bb.MONTHS_BALANCE) AS BB_HISTORY_LENGTH
        FROM bb_clean bb
        JOIN bureau_clean b ON bb.SK_ID_BUREAU=b.SK_ID_BUREAU
        GROUP BY b.SK_ID_CURR
    """)
    spark.table("bureau_delinquency_features").coalesce(4).write.mode("overwrite").parquet(f"{BASE}/bureau_delinquency_features")

def aggregate_previous_application():
    spark.read.parquet(f"{BASE}/previous_application_clean").createOrReplaceTempView("prev_clean")
    spark.sql("""
        CREATE OR REPLACE TEMP VIEW previous_application_features AS
        SELECT SK_ID_CURR,
            COUNT(SK_ID_PREV) AS PREV_CNT,
            SUM(CASE WHEN NAME_CONTRACT_STATUS='Approved' THEN 1 ELSE 0 END) AS PREV_APPROVED_CNT,
            SUM(CASE WHEN NAME_CONTRACT_STATUS='Refused' THEN 1 ELSE 0 END) AS PREV_REFUSED_CNT,
            CASE WHEN COUNT(SK_ID_PREV)>0 THEN SUM(CASE WHEN NAME_CONTRACT_STATUS='Approved' THEN 1 ELSE 0 END)*1.0/COUNT(SK_ID_PREV) ELSE 0 END AS PREV_APPROVAL_RATE,
            AVG(AMT_CREDIT) AS PREV_AVG_AMT_CREDIT,
            SUM(AMT_CREDIT) AS PREV_TOTAL_AMT_CREDIT,
            AVG(AMT_DOWN_PAYMENT) AS PREV_AVG_DOWN_PAYMENT,
            AVG(RATE_INTEREST_PRIMARY) AS PREV_AVG_INTEREST,
            SUM(CASE WHEN NAME_CONTRACT_TYPE LIKE '%Cash%' THEN 1 ELSE 0 END) AS PREV_CASH_LOAN_CNT,
            SUM(CASE WHEN NAME_CONTRACT_TYPE LIKE '%Revolving%' THEN 1 ELSE 0 END) AS PREV_REVOLVING_CNT,
            MAX(DAYS_DECISION) AS PREV_DAYS_SINCE_LAST_APP,
            SUM(NFLAG_INSURED_ON_APPROVAL) AS PREV_INSURED_CNT
        FROM prev_clean
        GROUP BY SK_ID_CURR
    """)
    spark.table("previous_application_features").coalesce(4).write.mode("overwrite").parquet(f"{BASE}/previous_application_features")

clean_bureau()
clean_bureau_balance()
clean_previous_application()
aggregate_bureau_features()
aggregate_bureau_delinquency()
aggregate_previous_application()

spark.stop()
print("✅ Bureau Credit History selesai.")