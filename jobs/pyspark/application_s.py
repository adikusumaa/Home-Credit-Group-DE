import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, DoubleType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_application():
    spark = SparkSession.builder.appName("ApplicationSilverProcessing").getOrCreate()
    
    try:
        logger.info("Reading source data...")
        df = spark.read.parquet("/data/bronze/application/")
        
        # Schema Drift Handling: Memastikan kolom wajib ada
        required_columns = {
            "SK_ID_CURR": "long",
            "AMT_CREDIT": "double",
            "NAME_CONTRACT_TYPE": "string"
        }
        
        for col_name, col_type in required_columns.items():
            if col_name not in df.columns:
                logger.warning(f"Column {col_name} missing. Adding with null values.")
                df = df.withColumn(col_name, F.lit(None).cast(col_type))
        
        # Business Logic
        df_silver = df.select(*required_columns.keys())
        
        # Penulisan aman
        temp_path = "/data/silver/application_temp/"
        
        df_silver.write.mode("overwrite").parquet(temp_path)
        
        logger.info("Processing completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        raise

if __name__ == "__main__":
    process_application()