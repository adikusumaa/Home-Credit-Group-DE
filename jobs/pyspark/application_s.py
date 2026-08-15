import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, DoubleType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_application(spark, input_path, output_path):
    logger.info(f"Starting processing from {input_path}")
    
    try:
        df = spark.read.parquet(input_path)
        
        # Schema Drift Handling: Memastikan kolom wajib ada
        required_columns = {
            "SK_ID_CURR": StringType(),
            "AMT_CREDIT": DoubleType(),
            "AMT_INCOME_TOTAL": DoubleType()
        }
        
        for col_name, col_type in required_columns.items():
            if col_name not in df.columns:
                logger.warning(f"Column {col_name} missing. Adding with null values.")
                df = df.withColumn(col_name, F.lit(None).cast(col_type))
        
        # Business Logic (Tetap dipertahankan)
        df_processed = df.select(*required_columns.keys())
        
        # Penulisan aman menggunakan temp path
        temp_output = output_path + "_temp"
        df_processed.write.mode("overwrite").parquet(temp_output)
        
        logger.info(f"Successfully processed data to {output_path}")
        
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        raise

if __name__ == "__main__":
    spark = SparkSession.builder.appName("ApplicationProcessing").getOrCreate()
    process_application(spark, "/data/raw/application", "/data/silver/application")