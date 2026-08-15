import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_application_processing():
    spark = SparkSession.builder \
        .appName("ApplicationProcessing") \
        .enableHiveSupport() \
        .getOrCreate()

    try:
        logger.info("Executing SQL query for application processing")
        df = spark.sql("SELECT * FROM DBDUELIST")
        df.show()
    except Exception as e:
        logger.error(f"Error during application processing: {str(e)}")
        raise

if __name__ == "__main__":
    run_application_processing()
