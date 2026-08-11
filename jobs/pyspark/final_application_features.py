from pyspark.sql import SparkSession
from pyspark.sql.functions import col

spark = SparkSession.builder \
    .appName("FinalApplicationFeatures") \
    .getOrCreate()

BASE = "hdfs://namenode:8020/data/silver/staging"

def get_columns_without_key(table_name, key_col="SK_ID_CURR"):
    """Ambil daftar kolom dari suatu tabel view, kecuali kolom key"""
    df = spark.table(table_name)
    return [c for c in df.columns if c != key_col]

def build_final_dataset():
    # Baca semua tabel fitur ke view sementara
    spark.read.parquet(f"{BASE}/application_train_clean").createOrReplaceTempView("t")
    spark.read.parquet(f"{BASE}/bureau_credit_features").createOrReplaceTempView("a")
    spark.read.parquet(f"{BASE}/bureau_delinquency_features").createOrReplaceTempView("b")
    spark.read.parquet(f"{BASE}/previous_application_features").createOrReplaceTempView("c")
    spark.read.parquet(f"{BASE}/pos_loan_features").createOrReplaceTempView("d")
    spark.read.parquet(f"{BASE}/installment_payment_features").createOrReplaceTempView("e")
    spark.read.parquet(f"{BASE}/credit_card_features").createOrReplaceTempView("f")

    a_cols = get_columns_without_key("a")
    b_cols = get_columns_without_key("b")
    c_cols = get_columns_without_key("c")
    d_cols = get_columns_without_key("d")
    e_cols = get_columns_without_key("e")
    f_cols = get_columns_without_key("f")

    select_cols = ["t.*"] + [f"a.`{col}`" for col in a_cols] + \
                           [f"b.`{col}`" for col in b_cols] + \
                           [f"c.`{col}`" for col in c_cols] + \
                           [f"d.`{col}`" for col in d_cols] + \
                           [f"e.`{col}`" for col in e_cols] + \
                           [f"f.`{col}`" for col in f_cols]
    select_clause = ",\n    ".join(select_cols)

    train_sql = f"""
        CREATE OR REPLACE TEMP VIEW train_integrated AS
        SELECT
            {select_clause}
        FROM t
        LEFT JOIN a ON t.SK_ID_CURR = a.SK_ID_CURR
        LEFT JOIN b ON t.SK_ID_CURR = b.SK_ID_CURR
        LEFT JOIN c ON t.SK_ID_CURR = c.SK_ID_CURR
        LEFT JOIN d ON t.SK_ID_CURR = d.SK_ID_CURR
        LEFT JOIN e ON t.SK_ID_CURR = e.SK_ID_CURR
        LEFT JOIN f ON t.SK_ID_CURR = f.SK_ID_CURR
    """
    spark.sql(train_sql)

    # Build SQL untuk test (sama, tapi sumber dari t_test)
    # Baca test table
    spark.read.parquet(f"{BASE}/application_test_clean").createOrReplaceTempView("t_test")
    # Gunakan daftar kolom yang sama (tabel fitur sudah ada)
    test_sql = f"""
        CREATE OR REPLACE TEMP VIEW test_integrated AS
        SELECT
            t_test.*,
            {", ".join([f"a.`{col}`" for col in a_cols] + [f"b.`{col}`" for col in b_cols] + [f"c.`{col}`" for col in c_cols] + [f"d.`{col}`" for col in d_cols] + [f"e.`{col}`" for col in e_cols] + [f"f.`{col}`" for col in f_cols])}
        FROM t_test
        LEFT JOIN a ON t_test.SK_ID_CURR = a.SK_ID_CURR
        LEFT JOIN b ON t_test.SK_ID_CURR = b.SK_ID_CURR
        LEFT JOIN c ON t_test.SK_ID_CURR = c.SK_ID_CURR
        LEFT JOIN d ON t_test.SK_ID_CURR = d.SK_ID_CURR
        LEFT JOIN e ON t_test.SK_ID_CURR = e.SK_ID_CURR
        LEFT JOIN f ON t_test.SK_ID_CURR = f.SK_ID_CURR
    """
    spark.sql(test_sql)

def validate_and_save():
    train = spark.table("train_integrated")
    total = train.count()
    unique = train.select("SK_ID_CURR").distinct().count()
    null_sk = train.filter(col("SK_ID_CURR").isNull()).count()
    invalid_target = train.filter(~col("TARGET").isin([0, 1])).count()
    outlier_age = train.filter((col("AGE_YEARS") < 18) | (col("AGE_YEARS") > 100)).count()

    print(f"Total: {total}, Unique SK_ID_CURR: {unique}, Null SK_ID_CURR: {null_sk}")
    print(f"Invalid TARGET: {invalid_target}, Outlier AGE: {outlier_age}")

    if null_sk == 0 and total == unique and invalid_target == 0 and outlier_age == 0:
        print("✅ Validasi PASS")
        train.coalesce(2).write.mode("overwrite").parquet("hdfs://namenode:8020/data/silver/home_credit/integrated/train")
        spark.table("test_integrated").coalesce(2).write.mode("overwrite").parquet("hdfs://namenode:8020/data/silver/home_credit/integrated/test")
        print("✅ Data final disimpan di /data/silver/home_credit/integrated/")
    else:
        raise Exception("❌ Validasi GAGAL, dataset tidak disimpan.")

build_final_dataset()
validate_and_save()
spark.stop()
print("✅ Final Application Features selesai.")