#!/usr/bin/env python3
"""
Performance test for TSS Converter optimizations
"""

import time
import tracemalloc
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_file_processing_performance(input_file: str):
    """
    Test performance of optimized TSS Converter pipeline
    
    Args:
        input_file: Path to test Excel file
    """
    from streamlit_pipeline import StreamlitTSSPipeline
    from pathlib import Path
    
    print("=" * 60)
    print("🚀 TSS Converter Performance Test")
    print("=" * 60)
    
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"❌ Test file not found: {input_path}")
        return
    
    # Initialize pipeline
    pipeline = StreamlitTSSPipeline()
    
    # Start performance monitoring
    tracemalloc.start()
    start_time = time.time()
    start_memory = tracemalloc.get_traced_memory()[0]
    
    try:
        # Test file upload
        print(f"📁 Testing file: {input_path.name}")
        print(f"📊 File size: {input_path.stat().st_size / 1024:.1f} KB")
        
        # Save uploaded file
        with open(input_path, 'rb') as f:
            file_data = f.read()
        
        upload_start = time.time()
        saved_file = pipeline.save_uploaded_file(file_data, input_path.name)
        upload_time = time.time() - upload_start
        
        print(f"⏱️  File upload time: {upload_time:.2f}s")
        
        # Run pipeline
        process_start = time.time()
        success, output_file, stats = pipeline.process_pipeline(saved_file)
        process_time = time.time() - process_start
        
        if success:
            print(f"✅ Pipeline completed successfully!")
            print(f"⏱️  Processing time: {process_time:.2f}s")
            print(f"📤 Output file: {output_file}")
            
            # Show processing stats
            if stats:
                print(f"📊 Steps completed: {stats.get('steps_completed', 0)}/5")
                if 'processing_time' in stats:
                    print(f"📊 Total processing time: {stats['processing_time']:.2f}s")
                if 'quality_score' in stats:
                    print(f"📊 Quality score: {stats['quality_score']:.1f}/100")
        else:
            print(f"❌ Pipeline failed!")
            if stats and 'error_message' in stats:
                print(f"❌ Error: {stats['error_message']}")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
    
    finally:
        # Calculate final performance metrics
        end_time = time.time()
        total_time = end_time - start_time
        
        current_memory, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE SUMMARY")
        print("=" * 60)
        print(f"⏱️  Total time: {total_time:.2f}s")
        print(f"💾 Peak memory: {peak_memory / 1024 / 1024:.1f} MB")
        print(f"💾 Final memory: {current_memory / 1024 / 1024:.1f} MB")
        print(f"🚀 Processing speed: {input_path.stat().st_size / 1024 / total_time:.1f} KB/s")
        
        # Performance benchmarks
        file_size_mb = input_path.stat().st_size / 1024 / 1024
        if total_time < 10:
            print("🎯 EXCELLENT: Sub-10 second processing ✅")
        elif total_time < 30:
            print("🎯 GOOD: Sub-30 second processing")
        else:
            print("🎯 SLOW: Consider further optimizations")
        
        if peak_memory < 100 * 1024 * 1024:  # 100MB
            print("🎯 MEMORY EFFICIENT: < 100MB peak usage ✅")
        elif peak_memory < 500 * 1024 * 1024:  # 500MB
            print("🎯 MODERATE: Memory usage acceptable")
        else:
            print("🎯 HIGH MEMORY: Consider memory optimizations")
        
        # Cleanup
        pipeline.cleanup_session()
        pipeline.clear_workbook_cache()

def main():
    """Run performance tests"""
    import sys
    
    if len(sys.argv) < 2:
        # Try to find a test file
        test_files = [
            "input/test.xlsx",
            "input/sample.xlsx",
            "test.xlsx",
            "sample.xlsx"
        ]
        
        input_file = None
        for test_file in test_files:
            if Path(test_file).exists():
                input_file = test_file
                break
        
        if not input_file:
            print("Usage: python test_performance.py <input_file.xlsx>")
            print("\nNo test file found. Please provide an Excel file to test.")
            return
    else:
        input_file = sys.argv[1]
    
    test_file_processing_performance(input_file)

if __name__ == "__main__":
    main()