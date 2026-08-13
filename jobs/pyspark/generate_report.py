from pyspark.sql import SparkSession
from pyspark.sql.functions import col, countDistinct
import json

spark = SparkSession.builder.appName("SilverValidation").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")
spark.conf.set("spark.sql.shuffle.partitions", "4")   # optimasi partisi

ENV = "dev"
INTEGRATED_BASE = f"hdfs://namenode:8020/data/{ENV}/silver/home_credit/integrated"

print("📂 Membaca data train final dari HDFS...")
df = spark.read.parquet(f"{INTEGRATED_BASE}/train")

# Hanya ambil kolom yang benar-benar divalidasi
df_val = df.select("SK_ID_CURR", "TARGET", "AGE_YEARS")

total = df_val.count()
null_sk = df_val.filter(col("SK_ID_CURR").isNull()).count()
distinct_sk = df_val.select(countDistinct("SK_ID_CURR")).collect()[0][0]
invalid_target = df_val.filter(~col("TARGET").isin(0, 1)).count()
age_out = df_val.filter((col("AGE_YEARS") < 18) | (col("AGE_YEARS") > 100)).count()

results = {
    "total_rows": total,
    "sk_id_curr_null": null_sk,
    "sk_id_curr_unique": distinct_sk,
    "invalid_target": invalid_target,
    "age_out_of_range": age_out,
    "success": null_sk == 0 and distinct_sk == total and invalid_target == 0 and age_out == 0
}

print(json.dumps(results, indent=2))

if not results["success"]:
    raise Exception("❌ Validasi GAGAL!")
else:
    print("✅ Validasi SUKSES!")