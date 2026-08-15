import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_application_data():
    spark = SparkSession.builder.appName("ApplicationProcessing").getOrCreate()
    
    try:
        logger.info("Starting application data processing")
        
        df = spark.table("application_raw")
        
        db_due_list = spark.sql("SELECT * FROM DBDUELIST")
        
        df_joined = df.join(db_due_list, on="application_id", how="left")
        
        df_joined.write.mode("overwrite").parquet("/tmp/application_silver")
        
        logger.info("Application data processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing application data: {str(e)}")
        raise

if __name__ == "__main__":
    process_application_data()