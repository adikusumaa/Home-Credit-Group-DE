import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, DoubleType, IntegerType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_application():
    spark = SparkSession.builder \
        .appName("ApplicationSilverProcessing") \
        .getOrCreate()

    try:
        logger.info("Reading source data...")
        df = spark.read.parquet("/data/bronze/application/")

        # Schema Drift Handling: Ensure required columns exist
        required_columns = {
            "SK_ID_CURR": IntegerType(),
            "TARGET": IntegerType(),
            "AMT_INCOME_TOTAL": DoubleType(),
            "NAME_CONTRACT_TYPE": StringType()
        }

        for col_name, col_type in required_columns.items():
            if col_name not in df.columns:
                logger.warning(f"Column {col_name} missing. Adding as null.")
                df = df.withColumn(col_name, F.lit(None).cast(col_type))

        # Business Logic
        df_silver = df.select(*required_columns.keys())

        # Save to temp path before overwriting
        temp_path = "/data/silver/application_temp/"
        final_path = "/data/silver/application/"
        
        df_silver.write.mode("overwrite").parquet(temp_path)
        
        # In a real scenario, use a file system move command here
        logger.info("Data processed successfully.")

    except Exception as e:
        logger.error(f"Error processing application data: {str(e)}")
        raise e
    finally:
        spark.stop()

if __name__ == "__main__":
    process_application()
