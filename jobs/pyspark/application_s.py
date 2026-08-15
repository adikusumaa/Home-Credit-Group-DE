import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_application_data(spark):
    try:
        logger.info("Starting application_s processing")
        
        query = "SELECT * FROM DBDUELIST"
        df = spark.sql(query)
        
        df.write.mode("overwrite").parquet("/tmp/application_s_output")
        logger.info("Processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        raise

if __name__ == "__main__":
    spark = SparkSession.builder.appName("ApplicationProcessing").getOrCreate()
    process_application_data(spark)
