import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_application_data():
    spark = SparkSession.builder.appName("ApplicationProcessing").getOrCreate()
    
    try:
        df = spark.read.parquet("/data/raw/application")
        
        df.createOrReplaceTempView("application_data")
        
        query = """
            SELECT 
                SK_ID_CURR,
                NAME_CONTRACT_TYPE,
                CODE_GENDER,
                AMT_CREDIT
            FROM application_data
            WHERE AMT_CREDIT IS NOT NULL
        """
        
        result_df = spark.sql(query)
        
        result_df.write.mode("overwrite").parquet("/data/silver/application")
        logger.info("Data processing completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        raise

if __name__ == "__main__":
    process_application_data()
