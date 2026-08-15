import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, StringType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_silver_data():
    spark = SparkSession.builder \
        .appName("SilverProcessing") \
        .config("spark.executor.memory", "4g") \
        .config("spark.sql.shuffle.partitions", "200") \
        .getOrCreate()

    try:
        logger.info("Reading source data...")
        df = spark.read.parquet("/data/bronze/raw_data")

        # Handling Schema Drift for critical columns
        required_columns = {
            "AMT_CREDIT": DoubleType(),
            "NAME_CONTRACT_TYPE": StringType()
        }

        for col_name, col_type in required_columns.items():
            if col_name not in df.columns:
                logger.warning(f"Column {col_name} missing. Adding as null.")
                df = df.withColumn(col_name, F.lit(None).cast(col_type))

        # Business Logic
        df_silver = df.select("AMT_CREDIT", "NAME_CONTRACT_TYPE") \
                      .filter(F.col("AMT_CREDIT").isNotNull())

        # Write to temp path to avoid overwrite issues
        temp_path = "/data/silver/temp_silver_data"
        df_silver.write.mode("overwrite").parquet(temp_path)
        
        logger.info("Processing completed successfully.")

    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        raise e
    finally:
        spark.stop()

if __name__ == "__main__":
    process_silver_data()
