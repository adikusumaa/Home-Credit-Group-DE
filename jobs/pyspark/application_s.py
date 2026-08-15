import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_application_data():
    spark = SparkSession.builder.appName("ApplicationProcessing").getOrCreate()
    
    try:
        logger.info("Executing SQL query to fetch data from DBDUELIST")
        df = spark.sql("SELECT * FROM DBDUELIST")
        df.show()
    except Exception as e:
        logger.error(f"Error executing SQL query: {str(e)}")
        raise

if __name__ == "__main__":
    process_application_data()