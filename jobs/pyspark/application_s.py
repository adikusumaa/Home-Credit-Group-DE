import logging
from pyspark.sql import SparkSession
import pyspark.sql.functions as F

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_application_data(spark):
    try:
        logger.info("Starting application_s processing")
        df = spark.read.parquet("/data/raw/application")
        
        df = df.withColumn("processed_at", F.current_timestamp())
        
        df.createOrReplaceTempView("application_temp")
        
        result_df = spark.sql("SELECT * FROM application_temp WHERE application_id IS NOT NULL")
        
        result_df.write.mode("overwrite").parquet("/data/silver/application")
        logger.info("Processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        raise

if __name__ == "__main__":
    spark = SparkSession.builder.appName("ApplicationProcessing").getOrCreate()
    process_application_data(spark)
