import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, DoubleType, IntegerType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_application():
    spark = SparkSession.builder.appName("ApplicationSilverProcessing").getOrCreate()
    
    try:
        logger.info("Reading source data...")
        df = spark.read.parquet("/data/raw/application/")
        
        # Schema Drift Handling: Memastikan kolom esensial ada
        # Jika kolom hilang, tambahkan dengan nilai NULL sesuai tipe data
        required_columns = {
            "SK_ID_CURR": IntegerType(),
            "AMT_CREDIT": DoubleType(),
            "NAME_CONTRACT_TYPE": StringType()
        }
        
        for col_name, col_type in required_columns.items():
            if col_name not in df.columns:
                logger.warning(f"Column {col_name} missing. Adding with null values.")
                df = df.withColumn(col_name, F.lit(None).cast(col_type))
        
        # Business Logic
        df_processed = df.select(*required_columns.keys())
        
        # Write to temp path before moving to final destination
        # Menghindari overwrite langsung pada path sumber data
        temp_path = "/data/silver/application_temp/"
        
        logger.info("Writing to temp path...")
        df_processed.write.mode("overwrite").parquet(temp_path)
        
        logger.info("Processing complete.")
        
    except Exception as e:
        logger.error(f"Error processing application data: {str(e)}")
        raise

if __name__ == "__main__":
    process_application()