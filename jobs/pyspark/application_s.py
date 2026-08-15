import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_application(spark):
    try:
        df = spark.read.parquet("/data/raw/application")
        
        df.createOrReplaceTempView("application_view")
        
        result_df = spark.sql("SELECT * FROM application_view WHERE status = 'ACTIVE'")
        
        result_df.write.mode("overwrite").parquet("/data/silver/application")
        logger.info("Processing application completed successfully.")
        
    except Exception as e:
        logger.error(f"Error processing application: {str(e)}")
        raise

if __name__ == "__main__":
    spark = SparkSession.builder.appName("ApplicationProcessing").getOrCreate()
    process_application(spark)
