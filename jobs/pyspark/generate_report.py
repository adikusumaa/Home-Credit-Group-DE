import great_expectations as ge
from great_expectations.dataset import SparkDFDataset
from pyspark.sql import SparkSession
from great_expectations.data_context import DataContext

def main():
    spark = SparkSession.builder \
        .appName("GenerateGEDocs") \
        .getOrCreate()

    print("📂 Membaca data train final dari HDFS...")
    df = spark.read.parquet("hdfs://namenode:8020/data/silver/home_credit/integrated/train")
    ge_df = SparkDFDataset(df)

    print("🔍 Menjalankan validasi...")
    ge_df.expect_column_values_to_not_be_null("SK_ID_CURR")
    ge_df.expect_column_values_to_be_unique("SK_ID_CURR")
    ge_df.expect_column_values_to_be_in_set("TARGET", [0, 1])
    ge_df.expect_column_values_to_be_between("AGE_YEARS", min_value=18, max_value=100)

    results = ge_df.validate()   # <-- INI YANG KURANG

    context_root_dir = "/opt/jobs/pyspark/great_expectations"
    context = DataContext(context_root_dir=context_root_dir)

    suite = ge_df.get_expectation_suite()
    context.save_expectation_suite(suite, "silver_validation_suite")

    context.build_data_docs()

    if not results['success']:
        raise Exception("❌ Validasi GAGAL! Ada data yang tidak sesuai aturan.")

    print("\n✅ LAPORAN BERHASIL DIBUAT!")
    print(f"📁 Lokasi: {context_root_dir}/uncommitted/data_docs/local_site/index.html")

if __name__ == "__main__":
    main()