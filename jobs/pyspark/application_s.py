import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_columns(df, expected_schema):
    """Menangani schema drift dengan menambahkan kolom yang hilang sebagai null."""
    for col_name, col_type in expected_schema.items():
        if col_name not in df.columns:
            logger.warning(f"Kolom {col_name} hilang. Menambahkan dengan tipe {col_type}.")
            df = df.withColumn(col_name, F.lit(None).cast(col_type))
    return df

def run_application_processing():
    spark = SparkSession.builder.appName("ApplicationProcessing").getOrCreate()
    
    # Contoh skema yang diharapkan
    expected_schema = {
        "SK_ID_CURR": "long",
        "TARGET": "integer",
        "NAME_CONTRACT_TYPE": "string"
    }

    try:
        df = spark.read.parquet("/data/raw/application")
        
        # Handle schema drift
        df = ensure_columns(df, expected_schema)
        
        # Logic bisnis inti
        df_processed = df.select(*expected_schema.keys())
        
        # Gunakan temp path untuk overwrite aman
        temp_path = "/data/silver/application_temp"
        df_processed.write.mode("overwrite").parquet(temp_path)
        
        logger.info("Proses application_s selesai dengan sukses.")
        
    except Exception as e:
        logger.error(f"Error saat memproses application_s: {str(e)}")
        raise

if __name__ == "__main__":
    run_application_processing()
