from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("LoanAndPaymentBehavior") \
    .getOrCreate()

BASE = "hdfs://namenode:8020/data/silver/staging"

def clean_pos_cash():
    df = spark.read.csv("hdfs://namenode:8020/data/bronze/home_credit/raw/POS_CASH_balance.csv", header=True, inferSchema=True)
    df.createOrReplaceTempView("pos_raw")
    spark.sql("""
        CREATE OR REPLACE TEMP VIEW pos_clean AS
        SELECT DISTINCT
            SK_ID_PREV, SK_ID_CURR, MONTHS_BALANCE,
            COALESCE(CNT_INSTALMENT, 0) AS CNT_INSTALMENT,
            COALESCE(CNT_INSTALMENT_FUTURE, 0) AS CNT_INSTALMENT_FUTURE,
            COALESCE(NAME_CONTRACT_STATUS, 'Unknown') AS NAME_CONTRACT_STATUS,
            COALESCE(SK_DPD, 0) AS SK_DPD, COALESCE(SK_DPD_DEF, 0) AS SK_DPD_DEF
        FROM pos_raw
    """)
    spark.table("pos_clean").write.mode("overwrite").parquet(f"{BASE}/POS_CASH_balance_clean")

def clean_installments():
    df = spark.read.csv("hdfs://namenode:8020/data/bronze/home_credit/raw/installments_payments.csv", header=True, inferSchema=True)
    df.createOrReplaceTempView("inst_raw")
    spark.sql("""
        CREATE OR REPLACE TEMP VIEW inst_clean AS
        SELECT DISTINCT
            SK_ID_PREV, SK_ID_CURR,
            COALESCE(NUM_INSTALMENT_VERSION, 0) AS NUM_INSTALMENT_VERSION,
            NUM_INSTALMENT_NUMBER,
            COALESCE(DAYS_INSTALMENT, 0) AS DAYS_INSTALMENT,
            COALESCE(DAYS_ENTRY_PAYMENT, 0) AS DAYS_ENTRY_PAYMENT,
            COALESCE(AMT_INSTALMENT, 0) AS AMT_INSTALMENT,
            COALESCE(AMT_PAYMENT, 0) AS AMT_PAYMENT
        FROM inst_raw
    """)
    spark.table("inst_clean").write.mode("overwrite").parquet(f"{BASE}/installments_payments_clean")

def clean_credit_card():
    df = spark.read.csv("hdfs://namenode:8020/data/bronze/home_credit/raw/credit_card_balance.csv", header=True, inferSchema=True)
    df.createOrReplaceTempView("cc_raw")
    spark.sql("""
        CREATE OR REPLACE TEMP VIEW cc_clean AS
        SELECT DISTINCT
            SK_ID_PREV, SK_ID_CURR, MONTHS_BALANCE,
            COALESCE(AMT_BALANCE, 0) AS AMT_BALANCE,
            COALESCE(AMT_CREDIT_LIMIT_ACTUAL, 0) AS AMT_CREDIT_LIMIT_ACTUAL,
            COALESCE(AMT_DRAWINGS_ATM_CURRENT, 0) AS AMT_DRAWINGS_ATM_CURRENT,
            COALESCE(AMT_DRAWINGS_CURRENT, 0) AS AMT_DRAWINGS_CURRENT,
            COALESCE(AMT_DRAWINGS_OTHER_CURRENT, 0) AS AMT_DRAWINGS_OTHER_CURRENT,
            COALESCE(AMT_DRAWINGS_POS_CURRENT, 0) AS AMT_DRAWINGS_POS_CURRENT,
            COALESCE(AMT_INST_MIN_REGULARITY, 0) AS AMT_INST_MIN_REGULARITY,
            COALESCE(AMT_PAYMENT_CURRENT, 0) AS AMT_PAYMENT_CURRENT,
            COALESCE(AMT_PAYMENT_TOTAL_CURRENT, 0) AS AMT_PAYMENT_TOTAL_CURRENT,
            COALESCE(AMT_RECEIVABLE_PRINCIPAL, 0) AS AMT_RECEIVABLE_PRINCIPAL,
            COALESCE(AMT_RECIVABLE, 0) AS AMT_RECIVABLE,
            COALESCE(AMT_TOTAL_RECEIVABLE, 0) AS AMT_TOTAL_RECEIVABLE,
            COALESCE(CNT_DRAWINGS_ATM_CURRENT, 0) AS CNT_DRAWINGS_ATM_CURRENT,
            COALESCE(CNT_DRAWINGS_CURRENT, 0) AS CNT_DRAWINGS_CURRENT,
            COALESCE(CNT_DRAWINGS_OTHER_CURRENT, 0) AS CNT_DRAWINGS_OTHER_CURRENT,
            COALESCE(CNT_DRAWINGS_POS_CURRENT, 0) AS CNT_DRAWINGS_POS_CURRENT,
            COALESCE(CNT_INSTALMENT_MATURE_CUM, 0) AS CNT_INSTALMENT_MATURE_CUM,
            COALESCE(NAME_CONTRACT_STATUS, 'Unknown') AS NAME_CONTRACT_STATUS,
            COALESCE(SK_DPD, 0) AS SK_DPD, COALESCE(SK_DPD_DEF, 0) AS SK_DPD_DEF
        FROM cc_raw
    """)
    spark.table("cc_clean").write.mode("overwrite").parquet(f"{BASE}/credit_card_balance_clean")

def aggregate_payment_features():
    # POS
    spark.read.parquet(f"{BASE}/POS_CASH_balance_clean").createOrReplaceTempView("pos_clean")
    spark.sql("""
        CREATE OR REPLACE TEMP VIEW pos_loan_features AS
        SELECT SK_ID_CURR,
            COUNT(DISTINCT SK_ID_PREV) AS POS_CNT,
            AVG(CNT_INSTALMENT_FUTURE) AS POS_AVG_REMAINING_INST,
            AVG(SK_DPD) AS POS_AVG_DPD, MAX(SK_DPD) AS POS_MAX_DPD,
            SUM(CASE WHEN NAME_CONTRACT_STATUS='Active' THEN 1 ELSE 0 END) AS POS_ACTIVE_CNT,
            SUM(CASE WHEN NAME_CONTRACT_STATUS='Completed' THEN 1 ELSE 0 END) AS POS_COMPLETED_CNT,
            CASE WHEN COUNT(*)>0 THEN SUM(CASE WHEN SK_DPD>0 THEN 1 ELSE 0 END)*1.0/COUNT(*) ELSE 0 END AS POS_OVERDUE_RATIO
        FROM pos_clean
        GROUP BY SK_ID_CURR
    """)
    spark.table("pos_loan_features").write.mode("overwrite").parquet(f"{BASE}/pos_loan_features")

    # Installments
    spark.read.parquet(f"{BASE}/installments_payments_clean").createOrReplaceTempView("inst_clean")
    spark.sql("""
        CREATE OR REPLACE TEMP VIEW installment_payment_features AS
        SELECT SK_ID_CURR,
            COUNT(*) AS INSTAL_CNT,
            AVG(AMT_PAYMENT/NULLIF(AMT_INSTALMENT,0)) AS INSTAL_AVG_PAYMENT_RATIO,
            STDDEV(AMT_PAYMENT/NULLIF(AMT_INSTALMENT,0)) AS INSTAL_STD_PAYMENT_RATIO,
            SUM(CASE WHEN DAYS_ENTRY_PAYMENT>DAYS_INSTALMENT THEN 1 ELSE 0 END) AS INSTAL_LATE_CNT,
            CASE WHEN COUNT(*)>0 THEN SUM(CASE WHEN DAYS_ENTRY_PAYMENT>DAYS_INSTALMENT THEN 1 ELSE 0 END)*1.0/COUNT(*) ELSE 0 END AS INSTAL_LATE_RATIO,
            AVG(CASE WHEN DAYS_ENTRY_PAYMENT>DAYS_INSTALMENT THEN DAYS_ENTRY_PAYMENT-DAYS_INSTALMENT ELSE 0 END) AS INSTAL_AVG_DAYS_LATE,
            SUM(AMT_PAYMENT) AS INSTAL_TOTAL_PAYMENT
        FROM inst_clean
        GROUP BY SK_ID_CURR
    """)
    spark.table("installment_payment_features").write.mode("overwrite").parquet(f"{BASE}/installment_payment_features")

    # Credit Card
    spark.read.parquet(f"{BASE}/credit_card_balance_clean").createOrReplaceTempView("cc_clean")
    spark.sql("""
        CREATE OR REPLACE TEMP VIEW credit_card_features AS
        SELECT SK_ID_CURR,
            COUNT(DISTINCT SK_ID_PREV) AS CC_CNT,
            AVG(AMT_BALANCE) AS CC_AVG_BALANCE,
            SUM(AMT_CREDIT_LIMIT_ACTUAL) AS CC_TOTAL_LIMIT,
            AVG(AMT_BALANCE/NULLIF(AMT_CREDIT_LIMIT_ACTUAL,0)) AS CC_AVG_UTILIZATION,
            MAX(AMT_BALANCE/NULLIF(AMT_CREDIT_LIMIT_ACTUAL,0)) AS CC_MAX_UTILIZATION,
            AVG(AMT_PAYMENT_TOTAL_CURRENT) AS CC_AVG_PAYMENT,
            AVG(AMT_DRAWINGS_ATM_CURRENT) AS CC_AVG_ATM_DRAWINGS,
            CASE WHEN COUNT(*)>0 THEN SUM(CASE WHEN AMT_BALANCE>AMT_CREDIT_LIMIT_ACTUAL THEN 1 ELSE 0 END)*1.0/COUNT(*) ELSE 0 END AS CC_OVERLIMIT_RATIO,
            AVG(SK_DPD) AS CC_AVG_DPD, MAX(SK_DPD) AS CC_MAX_DPD
        FROM cc_clean
        GROUP BY SK_ID_CURR
    """)
    spark.table("credit_card_features").write.mode("overwrite").parquet(f"{BASE}/credit_card_features")

clean_pos_cash()
clean_installments()
clean_credit_card()
aggregate_payment_features()

spark.stop()
print("✅ Loan and Payment Behavior selesai.")