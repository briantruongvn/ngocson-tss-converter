#!/usr/bin/env python3
"""
Simple test script for TSS Converter pipeline
Tests the pipeline without Streamlit interface
"""

import sys
from pathlib import Path
from streamlit_pipeline import StreamlitTSSPipeline, ProgressCallback

def simple_progress_callback(progress_data):
    """Simple progress callback that prints to console"""
    step = progress_data.get("current_step", 0)
    message = progress_data.get("message", "Processing...")
    error = progress_data.get("error", False)
    
    if error:
        print(f"❌ Error in Step {step}: {message}")
    else:
        print(f"✅ Step {step}: {message}")

def test_pipeline(input_file_path):
    """Test the pipeline with a given input file"""
    if not input_file_path.exists():
        print(f"❌ File not found: {input_file_path}")
        return False
    
    print(f"🔄 Testing pipeline with file: {input_file_path.name}")
    print("-" * 50)
    
    try:
        # Initialize pipeline
        pipeline = StreamlitTSSPipeline()
        
        # Create progress callback
        progress_callback = ProgressCallback(simple_progress_callback)
        
        # Read file data
        with open(input_file_path, 'rb') as f:
            file_data = f.read()
        
        # Save uploaded file
        saved_file_path = pipeline.save_uploaded_file(file_data, input_file_path.name)
        print(f"📁 File saved to: {saved_file_path}")
        
        # Validate file
        is_valid, error_msg = pipeline.validate_input_file(saved_file_path)
        if not is_valid:
            print(f"❌ Validation failed: {error_msg}")
            return False
        
        print("✅ File validation passed")
        
        # Run pipeline
        print("\n🚀 Starting pipeline processing...")
        success, output_file, stats = pipeline.process_pipeline(
            saved_file_path, progress_callback
        )
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 Pipeline completed successfully!")
            print(f"📥 Output file: {output_file}")
            print(f"📊 Processing time: {stats.get('processing_time', 0):.2f} seconds")
            print(f"📋 Steps completed: {stats.get('steps_completed', 0)}/5")
            
            if stats.get('final_rows'):
                print(f"📈 Final rows: {stats['final_rows']}")
            
        else:
            print("❌ Pipeline failed!")
            print(f"🔍 Error: {stats.get('error_message', 'Unknown error')}")
            
            if stats.get('error_details'):
                print(f"📝 Details: {stats['error_details']}")
        
        # Cleanup
        pipeline.cleanup_session()
        print("\n🧹 Cleaned up temporary files")
        
        return success
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function to run pipeline test"""
    print("📊 TSS Converter Pipeline Test")
    print("=" * 50)
    
    # Check if input file is provided
    if len(sys.argv) < 2:
        print("Usage: python test_pipeline.py <input_file.xlsx>")
        print("\nAvailable test files:")
        
        input_dir = Path("input")
        if input_dir.exists():
            for file in input_dir.glob("*.xlsx"):
                print(f"  - {file.name}")
        
        return
    
    input_file = Path(sys.argv[1])
    
    # If relative path, try to find in input directory
    if not input_file.is_absolute() and not input_file.exists():
        input_file = Path("input") / input_file.name
    
    # Test the pipeline
    success = test_pipeline(input_file)
    
    if success:
        print("\n🎉 Test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()