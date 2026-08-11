import great_expectations as ge
from great_expectations.dataset import SparkDFDataset
from pyspark.sql import SparkSession
from great_expectations.data_context import BaseDataContext
import os

def main():
    spark = SparkSession.builder \
        .appName("GreatExpectationsValidation") \
        .getOrCreate()

    print("📂 Membaca data train final dari HDFS...")
    df = spark.read.parquet("hdfs://namenode:8020/data/silver/home_credit/integrated/train")
    print(f"✅ Data berhasil dimuat, total baris: {df.count()}")

    ge_df = SparkDFDataset(df)

    print("🔍 Menjalankan validasi...")
    ge_df.expect_column_values_to_not_be_null("SK_ID_CURR")
    ge_df.expect_column_values_to_be_unique("SK_ID_CURR")
    ge_df.expect_column_values_to_be_in_set("TARGET", [0, 1])
    ge_df.expect_column_values_to_be_between("AGE_YEARS", min_value=18, max_value=100)

    results = ge_df.validate()

    print("\n📋 HASIL VALIDASI:")
    print(f"Status: {'✅ PASS' if results['success'] else '❌ FAIL'}")
    for result in results['results']:
        print(f"  - {result['expectation_config']['expectation_type']}: {result['success']}")

    # === KONFIGURASI INLINE (Tidak perlu file great_expectations.yml) ===
    context_root_dir = "/opt/jobs/pyspark/great_expectations"
    
    # Pastikan folder-folder yang diperlukan ada
    for dir_name in ["expectations", "uncommitted/validations", "uncommitted/data_docs/local_site"]:
        os.makedirs(os.path.join(context_root_dir, dir_name), exist_ok=True)

    config = {
        'config_version': 3,
        'stores': {
            'expectations_store': {
                'class_name': 'ExpectationsStore',
                'store_backend': {
                    'class_name': 'TupleFilesystemStoreBackend',
                    'base_directory': os.path.join(context_root_dir, 'expectations')
                }
            },
            'validation_results_store': {
                'class_name': 'ValidationResultsStore',
                'store_backend': {
                    'class_name': 'TupleFilesystemStoreBackend',
                    'base_directory': os.path.join(context_root_dir, 'uncommitted/validations')
                }
            }
        },
        'data_docs_sites': {
            'local_site': {
                'class_name': 'SiteBuilder',
                'store_backend': {
                    'class_name': 'TupleFilesystemStoreBackend',
                    'base_directory': os.path.join(context_root_dir, 'uncommitted/data_docs/local_site')
                },
                'site_index_builder': {
                    'class_name': 'DefaultSiteIndexBuilder'
                }
            }
        }
    }

    context = BaseDataContext(project_config=config, context_root_dir=context_root_dir)
    
    # Simpan Expectation Suite
    suite = ge_df.get_expectation_suite()
    context.save_expectation_suite(suite, "silver_validation_suite")
    
    # Build Data Docs
    context.build_data_docs()

    print("\n✅ VALIDASI SELESAI!")
    print("📌 Laporan HTML tersimpan di:")
    print(f"   {context_root_dir}/uncommitted/data_docs/local_site/index.html")
    print("📌 Copy ke host dengan:")
    print("   docker cp spark-master:/opt/jobs/pyspark/great_expectations ./ge_report")
    print("   Lalu buka ./ge_report/uncommitted/data_docs/local_site/index.html")

if __name__ == "__main__":
    main()