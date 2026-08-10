from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, when

spark = SparkSession.builder \
    .appName("Explore") \
    .getOrCreate()

df = spark.read.csv("hdfs://namenode:8020/data/bronze/home_credit/raw/application_train.csv", header=True, inferSchema=True)

print("=== Missing Values ===")
df.select([count(when(col(c).isNull(), c)).alias(c) for c in ["DAYS_BIRTH", "DAYS_EMPLOYED", "EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3", "AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY"]]).show()

print("=== Target Distribution ===")
df.groupBy("TARGET").count().show()

print("=== Duplicate SK_ID_CURR ===")
df.groupBy("SK_ID_CURR").count().filter("count > 1").show()

print("=== FLAG_OWN_CAR unique ===")
df.select("FLAG_OWN_CAR").distinct().show()
print("=== FLAG_OWN_REALTY unique ===")
df.select("FLAG_OWN_REALTY").distinct().show()

print("=== DAYS_EMPLOYED == 365243 ===")
print(df.filter(col("DAYS_EMPLOYED") == 365243).count())

spark.stop()