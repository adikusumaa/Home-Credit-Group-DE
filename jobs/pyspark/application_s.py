import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, DoubleType

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_application_data():
    spark = SparkSession.builder.appName("ApplicationSilverProcessing").getOrCreate()
    
    try:
        logger.info("Reading source data...")
        df = spark.read.parquet("/data/raw/application/")
        
        # Schema Enforcement: Daftar kolom wajib dan tipe datanya
        required_columns = {
            "SK_ID_CURR": "long",
            "TARGET": "integer",
            "NAME_CONTRACT_TYPE": "string"
        }
        
        # Handling missing columns (Schema Drift)
        for col_name, col_type in required_columns.items():
            if col_name not in df.columns:
                logger.warning(f"Column {col_name} missing. Adding as null.")
                df = df.withColumn(col_name, F.lit(None).cast(col_type))
        
        # Business Logic (Contoh)
        df_processed = df.select(*required_columns.keys())
        
        # Write to temp path before overwrite to avoid data loss
        temp_path = "/data/silver/application_temp/"
        final_path = "/data/silver/application/"
        
        logger.info("Writing to temp path...")
        df_processed.write.mode("overwrite").parquet(temp_path)
        
        # Logic untuk memindahkan dari temp ke final bisa ditambahkan di sini
        # atau menggunakan overwrite pada path final jika sudah aman
        df_processed.write.mode("overwrite").parquet(final_path)
        
        logger.info("Processing completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        raise e
    finally:
        spark.stop()

if __name__ == "__main__":
    process_application_data()