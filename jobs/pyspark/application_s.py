import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_application_data():
    spark = SparkSession.builder.appName("ApplicationProcessing").getOrCreate()
    
    try:
        logger.info("Starting application data processing")
        
        df = spark.table("raw_application_data")
        
        df.createOrReplaceTempView("DBDUELIST")
        result_df = spark.sql("SELECT * FROM DBDUELIST")
        
        result_df.write.mode("overwrite").parquet("/tmp/application_s_output")
        
        logger.info("Application data processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error during application processing: {str(e)}")
        raise
    finally:
        spark.stop()

if __name__ == "__main__":
    process_application_data()