import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_application_data(spark):
    try:
        logger.info("Starting application data processing")
        df = spark.read.parquet("/data/raw/application")
        
        # Example fix for schema drift
        if "target_column" not in df.columns:
            df = df.withColumn("target_column", F.lit(None).cast("string"))
            
        df.createOrReplaceTempView("application_view")
        
        # Corrected SQL execution
        result_df = spark.sql("SELECT * FROM application_view WHERE status = 'ACTIVE'")
        
        result_df.write.mode("overwrite").parquet("/data/silver/application_temp")
        logger.info("Application data processing completed successfully")
    except Exception as e:
        logger.error(f"Error processing application data: {str(e)}")
        raise

if __name__ == "__main__":
    spark = SparkSession.builder.appName("ApplicationProcessing").getOrCreate()
    process_application_data(spark)
