from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, abs as spark_abs, round as spark_round, lit

spark = SparkSession.builder \
    .appName("ApplicationProfile") \
    .getOrCreate()

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

def clean_application(df, is_train=True):
    df = df.withColumn("AGE_YEARS", spark_round(spark_abs(col("DAYS_BIRTH")) / 365.25, 2))
    df = df.drop("DAYS_BIRTH")
    df = df.withColumn("FLAG_UNEMPLOYED", when(col("DAYS_EMPLOYED") == 365243, 1).otherwise(0))
    df = df.withColumn("YEARS_EMPLOYED",
                       when(col("DAYS_EMPLOYED") == 365243, 0.0)
                       .otherwise(spark_round(spark_abs(col("DAYS_EMPLOYED")) / 365.25, 2)))
    df = df.drop("DAYS_EMPLOYED")
    for flag_col in ["FLAG_OWN_CAR", "FLAG_OWN_REALTY"]:
        if flag_col in df.columns:
            df = df.withColumn(flag_col, when(col(flag_col) == "Y", 1).otherwise(0).cast("int"))
    numeric_cols = [c for c, t in df.dtypes if t in ["double", "int", "float"] and c not in ("TARGET", "SK_ID_CURR")]
    for nc in numeric_cols:
        if df.filter(col(nc).isNull()).count() > 0:
            df = fill_missing_with_median_fast(df, nc)
    cat_cols = [c for c, t in df.dtypes if t == "string"]
    for cc in cat_cols:
        if df.filter(col(cc).isNull()).count() > 0:
            df = fill_missing_with_mode(df, cc)
    df = df.dropDuplicates(["SK_ID_CURR"])
    return df

df_train = spark.read.csv("hdfs://namenode:8020/data/bronze/home_credit/raw/application_train.csv", header=True, inferSchema=True)
df_train_clean = clean_application(df_train)
df_train_clean.coalesce(4).write.mode("overwrite").parquet("hdfs://namenode:8020/data/silver/staging/application_train_clean")

# Proses Test
df_test = spark.read.csv("hdfs://namenode:8020/data/bronze/home_credit/raw/application_test.csv", header=True, inferSchema=True)
df_test_clean = clean_application(df_test)
df_test_clean.coalesce(4).write.mode("overwrite").parquet("hdfs://namenode:8020/data/silver/staging/application_test_clean")

spark.stop()
print("✅ Application Profile selesai.")