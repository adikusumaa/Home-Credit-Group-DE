import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, DoubleType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_application():
    spark = SparkSession.builder.appName("ApplicationSilverProcessing").getOrCreate()
    
    input_path = "/data/bronze/application"
    output_path = "/data/silver/application"
    temp_path = "/data/silver/application_temp"

    try:
        df = spark.read.parquet(input_path)
        
        # Schema Drift Handling: Memastikan kolom wajib ada
        required_columns = {
            "SK_ID_CURR": "long",
            "AMT_INCOME_TOTAL": "double",
            "NAME_CONTRACT_TYPE": "string"
        }
        
        for col_name, col_type in required_columns.items():
            if col_name not in df.columns:
                logger.warning(f"Kolom {col_name} hilang, menambahkan dengan nilai NULL.")
                df = df.withColumn(col_name, F.lit(None).cast(col_type))

        # Business Logic (tetap sama)
        df_silver = df.select(*required_columns.keys())

        # Save dengan pola temp untuk menghindari data corruption
        df_silver.write.mode("overwrite").parquet(temp_path)
        
        # Rename/Move logic (simulasi)
        logger.info("Data berhasil diproses ke temp path.")
        
    except Exception as e:
        logger.error(f"Error saat memproses data: {str(e)}")
        raise

if __name__ == "__main__":
    process_application()