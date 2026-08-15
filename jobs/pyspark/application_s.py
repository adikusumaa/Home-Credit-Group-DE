import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, DoubleType, IntegerType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_application():
    spark = SparkSession.builder.appName("SilverApplicationProcessing").getOrCreate()
    
    try:
        df = spark.read.parquet("/data/bronze/application")
        
        # Define expected schema and types to prevent schema drift
        expected_schema = {
            "SK_ID_CURR": IntegerType(),
            "TARGET": IntegerType(),
            "NAME_CONTRACT_TYPE": StringType(),
            "AMT_INCOME_TOTAL": DoubleType()
        }
        
        # Schema Drift Handling
        for col_name, col_type in expected_schema.items():
            if col_name not in df.columns:
                logger.warning(f"Column {col_name} missing. Adding with null values.")
                df = df.withColumn(col_name, F.lit(None).cast(col_type))
        
        # Business Logic (Keep Intact)
        df_silver = df.select(*expected_schema.keys())
        
        # Write to temp path before moving to final destination
        temp_path = "/data/silver/application_temp"
        df_silver.write.mode("overwrite").parquet(temp_path)
        
        logger.info("Processing completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        raise e

if __name__ == "__main__":
    process_application()