"""
SIMPLE PySpark + Docling Integration
====================================
Process PDFs in parallel using PySpark

Think of it like this:
1. You have a list of PDF files
2. PySpark splits them across many workers
3. Each worker processes their PDFs using docling_process()
4. Results come back to you
"""

# ============================================================================
# Step 1: Import the tools we need
# ============================================================================
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.types import (
    StructType,      # Like a template for a form
    StructField,     # Like a field on the form
    BooleanType,     # True/False
    StringType,      # Text
    MapType          # Dictionary/Key-Value pairs
)
import sys
from pathlib import Path

# Add our code to Python's search path
sys.path.insert(0, str(Path(__file__).parent))

# ============================================================================
# Step 2: Define what the result looks like (Schema)
# ============================================================================
def get_result_schema() -> StructType:
    """
    This tells PySpark what our result looks like.
    
    Think of it like a form template:
    - Checkbox: Did it succeed? (True/False)
    - Text box: What's the content? (Text)
    - Dictionary: Extra information (Key-Value pairs)
    - Text box: Error message if failed (Text)
    - Text box: Which file was it? (Text)
    """
    return StructType([
        StructField("success", BooleanType(), nullable=False),        # Required
        StructField("content", StringType(), nullable=True),          # Optional
        StructField("metadata", MapType(StringType(), StringType()), nullable=True),  # Optional
        StructField("error_message", StringType(), nullable=True),    # Optional
        StructField("file_path", StringType(), nullable=False),       # Required
    ])

# ============================================================================
# Step 3: Wrap our function for PySpark
# ============================================================================
def process_pdf_wrapper(file_path: str) -> dict:
    """
    This is a wrapper around docling_process that:
    1. Calls docling_process(file_path)
    2. Gets the result
    3. Converts it to a dictionary
    4. Makes sure all metadata values are strings (PySpark requirement)
    5. Returns the dictionary
    
    Why convert metadata values to strings?
    Because PySpark's MapType needs all values to be the same type!
    """
    # Import inside the function (lazy import for Spark workers)
    from processor import docling_process

    # Call the docling_process function
    # This creates a NEW processor on each worker (not serialized from driver)
    result = docling_process(file_path)
    
    # Convert the result to a dictionary
    result_dict = result.to_dict()
    
    # Convert all metadata values to strings
    if result_dict.get('metadata'):
        result_dict['metadata'] = {
            key: str(value) if value is not None else ""
            for key, value in result_dict['metadata'].items()
        }
    
    return result_dict

# ============================================================================
# Step 4: Create a Spark session (The Teacher)
# ============================================================================
def create_spark():
    """
    Create the Spark "Driver" that manages everything.
    
    local[4] means: Use 4 workers on this computer
    (Like having 4 friends helping you)
    """
    print("*" * 70)
    print("Creating Spark session...")
    print("*" * 70)
    
    spark = SparkSession.builder \
        .appName("DoclingSparkJob") \
        .master("local[4]") \
        .config("spark.python.worker.reuse", "false") \
        .config("spark.sql.execution.arrow.pyspark.enabled", "false") \
        .config("spark.executor.memory", "2g") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()

    # make it less chatty
    spark.sparkContext.setLogLevel("WARN")

    # ADD THESE LINES - Distribute the docling_module to workers
    import os
    module_path = os.path.join(os.path.dirname(__file__), "docling_module")
    for py_file in ["__init__.py", "processor.py"]:
        spark.sparkContext.addPyFile(os.path.join(module_path, py_file))

    print(f"Spark session created with {spark.sparkContext.defaultParallelism} workers")
    return spark

# ============================================================================
# Step 5: Main Function - Put it all together
# ============================================================================
def main():
    """
    The main function that does everything step by step.
    """
    
    print("\n" + "="*70)
    print("📄 SIMPLE PDF PROCESSING WITH PYSPARK")
    print("="*70)
    
    # ========== STEP 1: Create Spark ==========
    spark = create_spark()
    
    # Define output_path at the top level so it's accessible in finally block
    output_path = Path(__file__).parent.parent / "output" / "results"
    
    try:
        # ========== STEP 2: Get list of PDF files ==========
        print("\n📂 Step 1: Getting list of PDF files...")
        
        assets_dir = Path(__file__).parent.parent / "assets"
        pdf_path = assets_dir / "2206.01062.pdf"
        
        # Create a list of file paths to process
        # In real life, this could be thousands of files!
        file_list = [
            (str(pdf_path),),              # Valid PDF
            ("/fake/path/missing.pdf",),   # Will fail (doesn't exist)
            (str(pdf_path),),              # Same file again (to show parallel processing)
        ]
        
        # Create a DataFrame (like an Excel table)
        df_paths = spark.createDataFrame(file_list, ["document_path"])
        
        print(f"   Found {df_paths.count()} files to process")
        print("\n   Files:")
        df_paths.show(truncate=False)
        
        # ========== STEP 3: Register the UDF ==========
        print("\n⚙️  Step 2: Registering the processing function...")
        
        # Create the UDF (User Defined Function)
        # This wraps our process_pdf_wrapper so PySpark can use it
        docling_udf = udf(
            process_pdf_wrapper,        # Our wrapper function
            get_result_schema()         # What it returns
        )
        
        print("   ✅ Function registered")
        
        # ========== STEP 4: Process the files ==========
        print("\n🔄 Step 3: Processing files (this is where the magic happens!)...")
        print("   Spark is now distributing work to workers...")
        
        # Apply the UDF to each row
        # PySpark automatically splits this across workers!
        df_with_results = df_paths.withColumn(
            "result",                      # New column name
            docling_udf(col("document_path"))  # Apply function to each path
        )
        
        # ========== STEP 5: Flatten the results ==========
        print("\n📊 Step 4: Organizing results...")
        
        # Break apart the result into separate columns
        df_final = df_with_results.select(
            col("document_path"),
            col("result.success").alias("success"),
            col("result.content").alias("content"),
            col("result.metadata").alias("metadata"),
            col("result.error_message").alias("error_message")
        )
        
        # ========== STEP 6: Show the results ==========
        print("\n✅ Step 5: Results are ready!\n")
        
        print("📋 What the data looks like:")
        df_final.printSchema()
        
        print("\n📊 The results:")
        df_final.show(truncate=50)

        # ========== STEP 7: Analyze results ==========
        print("\n📈 Analysis:")
        
        total = df_final.count()
        successful = df_final.filter(col("success") == True).count()
        failed = df_final.filter(col("success") == False).count()
        
        print(f"   Total files: {total}")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        
        # Show successful files
        if successful > 0:
            print("\n✅ Successful files:")
            df_final.filter(col("success") == True).select(
                "document_path", "success"
            ).show(truncate=False)
        
        # Show failed files
        if failed > 0:
            print("\n❌ Failed files:")
            df_final.filter(col("success") == False).select(
                "document_path", "error_message"
            ).show(truncate=False)
        
        
        # ========== STEP 8: Save results (Optional) ==========
        print("\n💾 Step 6: Saving results...")
        
        # output_path is now defined above, not here
        
        # Save as Parquet (efficient for big data)
        df_final.write.mode("overwrite").parquet(str(output_path))
        
        print(f"   ✅ Results saved to: {output_path}")
        
        print("\n🎉 ALL DONE!")
        
        # ========== STEP 9: Read and show saved results ==========
        print("\n" + "="*70)
        print("📖 READING SAVED RESULTS")
        print("="*70)

        # Read the saved parquet files (BEFORE stopping spark)
        df_loaded = spark.read.parquet(str(output_path))

        print("\n📊 Loaded results:")
        df_loaded.show(truncate=False)

        # Save as readable JSON
        json_path = Path(__file__).parent.parent / "output" / "results.json"
        df_loaded.coalesce(1).write.mode("overwrite").json(str(json_path))
        print(f"\n💾 Also saved as JSON: {json_path}")

        # Save as CSV
        csv_path = Path(__file__).parent.parent / "output" / "results.csv"
        df_loaded.coalesce(1).write.mode("overwrite").option("header", True).csv(str(csv_path))
        print(f"💾 Also saved as CSV: {csv_path}")
        print("✅ Done!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Always stop Spark when done
        print("\n🛑 Stopping Spark...")
        spark.stop()
        print("✅ Bye!")

if __name__ == "__main__":
    main()