# clean_application.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, abs, round, lit, coalesce
from pyspark.sql.types import IntegerType, DoubleType

spark = SparkSession.builder.appName("Silver_Application").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# Environment (dev/prod)
ENV = "dev"
BRONZE_BASE = f"hdfs://namenode:8020/data/{ENV}/bronze/home_credit/raw"
SILVER_BASE = f"hdfs://namenode:8020/data/{ENV}/silver/staging"

# Helper functions for imputation (optional, we can do in SQL)
def fill_missing_with_median_fast(df, col_name):
    q = df.select(col_name).approxQuantile(col_name, [0.5], 0.01)
    med = q[0] if q else None
    if med is not None:
        df = df.withColumn(col_name, when(col(col_name).isNull(), lit(med)).otherwise(col(col_name)))
    return df

def fill_missing_with_mode(df, col_name, default="Unknown"):
    mode_row = df.groupBy(col_name).count().orderBy("count", ascending=False).first()
    mode_val = mode_row[col_name] if mode_row and mode_row[col_name] is not None else default
    df = df.withColumn(col_name, when(col(col_name).isNull(), lit(mode_val)).otherwise(col(col_name)))
    return df

def clean_application(df):
    # Convert flags
    df = df.withColumn("FLAG_OWN_CAR", when(col("FLAG_OWN_CAR") == "Y", 1).otherwise(0).cast("int"))
    df = df.withColumn("FLAG_OWN_REALTY", when(col("FLAG_OWN_REALTY") == "Y", 1).otherwise(0).cast("int"))

    # Age & employment
    df = df.withColumn("ageYears", round(abs(col("DAYS_BIRTH")) / 365.25, 0).cast("int"))
    df = df.withColumn("yearsEmployed",
                       when(col("DAYS_EMPLOYED") == 365243, 0.0)
                       .otherwise(round(abs(col("DAYS_EMPLOYED")) / 365.25, 2)))
    df = df.withColumn("isUnemployed", when(col("DAYS_EMPLOYED") == 365243, 1).otherwise(0))
    df = df.drop("DAYS_BIRTH", "DAYS_EMPLOYED")

    # Impute missing values (use SQL later, but here we do with DataFrame)
    numeric_cols = [c for c, t in df.dtypes if t in ["double", "int", "float"] and c not in ("TARGET", "SK_ID_CURR")]
    for nc in numeric_cols:
        if df.filter(col(nc).isNull()).count() > 0:
            df = fill_missing_with_median_fast(df, nc)
    cat_cols = [c for c, t in df.dtypes if t == "string"]
    for cc in cat_cols:
        if df.filter(col(cc).isNull()).count() > 0:
            df = fill_missing_with_mode(df, cc)
    return df

# Read raw data
df_train = spark.read.csv(f"{BRONZE_BASE}/application_train.csv", header=True, inferSchema=True)
df_test = spark.read.csv(f"{BRONZE_BASE}/application_test.csv", header=True, inferSchema=True)

# Clean both
df_train_clean = clean_application(df_train)
df_test_clean = clean_application(df_test)

# Register temporary views
df_train_clean.createOrReplaceTempView("app_train_clean")
df_test_clean.createOrReplaceTempView("app_test_clean")

# Feature Engineering using SQL (all groups from Application Analysis Plan)
featured_train = spark.sql("""
SELECT
    SK_ID_CURR AS loanId,
    TARGET AS target,
    ageYears,
    CODE_GENDER AS gender,
    FLAG_OWN_CAR AS has_car,
    FLAG_OWN_REALTY AS has_house,
    CASE 
        WHEN FLAG_OWN_CAR=1 AND FLAG_OWN_REALTY=1 THEN 'Both'
        WHEN FLAG_OWN_CAR=1 AND FLAG_OWN_REALTY=0 THEN 'Only Car'
        WHEN FLAG_OWN_CAR=0 AND FLAG_OWN_REALTY=1 THEN 'Only House'
        ELSE 'None'
    END AS asset_profile,
    CNT_CHILDREN AS children_cnt,
    CNT_FAM_MEMBERS AS family_members,
    -- Perbaikan division by zero
    CASE WHEN CNT_FAM_MEMBERS = 0 THEN 0 
         ELSE AMT_INCOME_TOTAL / CNT_FAM_MEMBERS 
    END AS income_per_member,
    NAME_CONTRACT_TYPE AS contract_type,
    AMT_CREDIT AS credit_amt,
    AMT_ANNUITY AS annuity_amt,
    CASE WHEN AMT_INCOME_TOTAL = 0 THEN 0 
         ELSE AMT_CREDIT / AMT_INCOME_TOTAL 
    END AS debt_to_income,
    CASE WHEN AMT_INCOME_TOTAL = 0 THEN 0 
         ELSE AMT_ANNUITY / AMT_INCOME_TOTAL 
    END AS payment_to_income,
    CASE WHEN AMT_CREDIT < AMT_GOODS_PRICE THEN 1 ELSE 0 END AS has_down_payment,
    CASE 
        WHEN NAME_INCOME_TYPE IN ('State servant', 'Pensioner') THEN 'Stable'
        WHEN NAME_INCOME_TYPE IN ('Working', 'Commercial associate') THEN 'Private'
        ELSE 'Others/Rare'
    END AS income_type_group,
    CASE 
        WHEN OCCUPATION_TYPE IN ('Low-skill Laborers', 'Drivers', 'Waiters/barmen staff', 
                                 'Security staff', 'Laborers', 'Cooking staff', 'Cleaning staff') 
            THEN 'High Risk'
        WHEN OCCUPATION_TYPE IN ('Sales staff', 'Realty agents', 'Secretaries', 
                                 'Private service staff', 'Core staff', 'None') 
            THEN 'Medium Risk'
        ELSE 'Low Risk'
    END AS occupation_risk_group,
    CASE 
        WHEN DAYS_REGISTRATION <= -3650 AND DAYS_ID_PUBLISH <= -3650 THEN 2
        WHEN DAYS_REGISTRATION <= -3650 OR DAYS_ID_PUBLISH <= -3650 THEN 1
        ELSE 0
    END AS stability_score,
    CASE 
        WHEN REG_REGION_NOT_LIVE_REGION=0 AND REG_CITY_NOT_LIVE_CITY=0 THEN 'Stabil'
        WHEN REG_REGION_NOT_LIVE_REGION=0 AND REG_CITY_NOT_LIVE_CITY=1 THEN 'Komuter Lokal'
        WHEN REG_REGION_NOT_LIVE_REGION=1 AND REG_CITY_NOT_LIVE_CITY=1 THEN 'Komuter Jauh'
        ELSE 'Lainnya'
    END AS commute_risk_profile,
    REGION_RATING_CLIENT AS region_rate,
    CASE WHEN HOUR_APPR_PROCESS_START BETWEEN 0 AND 5 THEN 1 ELSE 0 END AS is_dini_hari,
    EXT_SOURCE_1, EXT_SOURCE_2, EXT_SOURCE_3,
    DAYS_LAST_PHONE_CHANGE AS days_phone_change
FROM app_train_clean
""")

# Same for test (without target)
featured_test = spark.sql("""
SELECT
    SK_ID_CURR AS loanId,
    ageYears,
    CODE_GENDER AS gender,
    FLAG_OWN_CAR AS has_car,
    FLAG_OWN_REALTY AS has_house,
    CASE 
        WHEN FLAG_OWN_CAR=1 AND FLAG_OWN_REALTY=1 THEN 'Both'
        WHEN FLAG_OWN_CAR=1 AND FLAG_OWN_REALTY=0 THEN 'Only Car'
        WHEN FLAG_OWN_CAR=0 AND FLAG_OWN_REALTY=1 THEN 'Only House'
        ELSE 'None'
    END AS asset_profile,
    CNT_CHILDREN AS children_cnt,
    CNT_FAM_MEMBERS AS family_members,
    CASE WHEN CNT_FAM_MEMBERS = 0 THEN 0 
         ELSE AMT_INCOME_TOTAL / CNT_FAM_MEMBERS 
    END AS income_per_member,
    NAME_CONTRACT_TYPE AS contract_type,
    AMT_CREDIT AS credit_amt,
    AMT_ANNUITY AS annuity_amt,
    CASE WHEN AMT_INCOME_TOTAL = 0 THEN 0 
         ELSE AMT_CREDIT / AMT_INCOME_TOTAL 
    END AS debt_to_income,
    CASE WHEN AMT_INCOME_TOTAL = 0 THEN 0 
         ELSE AMT_ANNUITY / AMT_INCOME_TOTAL 
    END AS payment_to_income,
    CASE WHEN AMT_CREDIT < AMT_GOODS_PRICE THEN 1 ELSE 0 END AS has_down_payment,
    CASE 
        WHEN NAME_INCOME_TYPE IN ('State servant', 'Pensioner') THEN 'Stable'
        WHEN NAME_INCOME_TYPE IN ('Working', 'Commercial associate') THEN 'Private'
        ELSE 'Others/Rare'
    END AS income_type_group,
    CASE 
        WHEN OCCUPATION_TYPE IN ('Low-skill Laborers', 'Drivers', 'Waiters/barmen staff', 
                                 'Security staff', 'Laborers', 'Cooking staff', 'Cleaning staff') 
            THEN 'High Risk'
        WHEN OCCUPATION_TYPE IN ('Sales staff', 'Realty agents', 'Secretaries', 
                                 'Private service staff', 'Core staff', 'None') 
            THEN 'Medium Risk'
        ELSE 'Low Risk'
    END AS occupation_risk_group,
    CASE 
        WHEN DAYS_REGISTRATION <= -3650 AND DAYS_ID_PUBLISH <= -3650 THEN 2
        WHEN DAYS_REGISTRATION <= -3650 OR DAYS_ID_PUBLISH <= -3650 THEN 1
        ELSE 0
    END AS stability_score,
    CASE 
        WHEN REG_REGION_NOT_LIVE_REGION=0 AND REG_CITY_NOT_LIVE_CITY=0 THEN 'Stabil'
        WHEN REG_REGION_NOT_LIVE_REGION=0 AND REG_CITY_NOT_LIVE_CITY=1 THEN 'Komuter Lokal'
        WHEN REG_REGION_NOT_LIVE_REGION=1 AND REG_CITY_NOT_LIVE_CITY=1 THEN 'Komuter Jauh'
        ELSE 'Lainnya'
    END AS commute_risk_profile,
    REGION_RATING_CLIENT AS region_rate,
    CASE WHEN HOUR_APPR_PROCESS_START BETWEEN 0 AND 5 THEN 1 ELSE 0 END AS is_dini_hari,
    EXT_SOURCE_1, EXT_SOURCE_2, EXT_SOURCE_3,
    DAYS_LAST_PHONE_CHANGE AS days_phone_change
FROM app_test_clean
""")

# Write to Silver
featured_train.coalesce(4).write.mode("overwrite").parquet(f"{SILVER_BASE}/application_train_clean")
featured_test.coalesce(4).write.mode("overwrite").parquet(f"{SILVER_BASE}/application_test_clean")

spark.stop()
print("Application Silver Layer completed.")