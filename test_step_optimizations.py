#!/usr/bin/env python3
"""
Simple performance test for optimized TSS Converter steps
"""

import time
import tracemalloc
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Reduce log noise
logger = logging.getLogger(__name__)

def test_step_performance(step_name: str, step_func, *args):
    """
    Test performance of a single step
    
    Args:
        step_name: Name of the step for display
        step_func: Function to execute
        *args: Arguments to pass to the function
    """
    print(f"\n🚀 Testing {step_name}")
    print("-" * 50)
    
    # Start performance monitoring
    tracemalloc.start()
    start_time = time.time()
    
    try:
        # Run the step
        result = step_func(*args)
        
        # Calculate performance
        end_time = time.time()
        execution_time = end_time - start_time
        current_memory, peak_memory = tracemalloc.get_traced_memory()
        
        print(f"✅ {step_name} completed successfully!")
        print(f"⏱️  Execution time: {execution_time:.2f}s")
        print(f"💾 Peak memory: {peak_memory / 1024 / 1024:.1f} MB")
        print(f"📤 Output: {result}")
        
        return {
            'success': True,
            'time': execution_time,
            'peak_memory': peak_memory,
            'output': result
        }
        
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"❌ {step_name} failed!")
        print(f"⏱️  Execution time: {execution_time:.2f}s")
        print(f"❌ Error: {e}")
        
        return {
            'success': False,
            'time': execution_time,
            'error': str(e)
        }
        
    finally:
        tracemalloc.stop()

def main():
    """Run performance tests on optimized steps"""
    
    print("=" * 60)
    print("🎯 TSS Converter Step Optimization Performance Test")
    print("=" * 60)
    
    # Test files
    input_file = Path("input/test.xlsx")
    if not input_file.exists():
        print("❌ Test file not found: input/test.xlsx")
        print("Please ensure a test file exists to run performance tests.")
        return
    
    # Import optimized step modules
    from step1_template_creation import TemplateCreator
    from step2_data_extraction import DataExtractor
    from step3_data_mapping import DataMapper
    from step4_data_fill import DataFiller
    from step5_filter_deduplicate import DataFilter
    
    results = {}
    
    # Test Step 1 - Template Creation
    try:
        creator = TemplateCreator()
        results['step1'] = test_step_performance(
            "Step 1: Template Creation",
            creator.create_template,
            input_file
        )
    except Exception as e:
        print(f"❌ Step 1 setup failed: {e}")
        results['step1'] = {'success': False, 'error': str(e)}
    
    # Test Step 2 - Data Extraction (if Step 1 succeeded)
    if results.get('step1', {}).get('success'):
        try:
            extractor = DataExtractor()
            step1_output = Path(results['step1']['output'])
            results['step2'] = test_step_performance(
                "Step 2: Data Extraction", 
                extractor.process_file,
                step1_output,
                input_file
            )
        except Exception as e:
            print(f"❌ Step 2 setup failed: {e}")
            results['step2'] = {'success': False, 'error': str(e)}
    
    # Test Step 3 - Data Mapping (if Step 2 succeeded)
    if results.get('step2', {}).get('success'):
        try:
            mapper = DataMapper()
            step2_output = Path(results['step2']['output'])
            results['step3'] = test_step_performance(
                "Step 3: Data Mapping",
                mapper.process_file,
                input_file,
                step2_output
            )
        except Exception as e:
            print(f"❌ Step 3 setup failed: {e}")
            results['step3'] = {'success': False, 'error': str(e)}
    
    # Test Step 4 - Data Fill (if Step 3 succeeded)
    if results.get('step3', {}).get('success'):
        try:
            filler = DataFiller()
            step3_output = Path(results['step3']['output'])
            results['step4'] = test_step_performance(
                "Step 4: Data Fill",
                filler.process_file,
                step3_output
            )
        except Exception as e:
            print(f"❌ Step 4 setup failed: {e}")
            results['step4'] = {'success': False, 'error': str(e)}
    
    # Test Step 5 - Filter & Deduplicate (if Step 4 succeeded)
    if results.get('step4', {}).get('success'):
        try:
            filter_processor = DataFilter()
            step4_output = Path(results['step4']['output'])
            results['step5'] = test_step_performance(
                "Step 5: Filter & Deduplicate",
                filter_processor.process_file,
                step4_output
            )
        except Exception as e:
            print(f"❌ Step 5 setup failed: {e}")
            results['step5'] = {'success': False, 'error': str(e)}
    
    # Performance Summary
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 60)
    
    total_time = 0
    total_memory = 0
    successful_steps = 0
    
    for step, result in results.items():
        if result.get('success'):
            step_time = result.get('time', 0)
            step_memory = result.get('peak_memory', 0)
            total_time += step_time
            total_memory = max(total_memory, step_memory)
            successful_steps += 1
            
            print(f"✅ {step.upper()}: {step_time:.2f}s, {step_memory / 1024 / 1024:.1f} MB")
        else:
            print(f"❌ {step.upper()}: FAILED - {result.get('error', 'Unknown error')}")
    
    print(f"\n🎯 OVERALL PERFORMANCE:")
    print(f"   ⏱️  Total time: {total_time:.2f}s")
    print(f"   💾 Peak memory: {total_memory / 1024 / 1024:.1f} MB")
    print(f"   ✅ Success rate: {successful_steps}/5 steps")
    
    # Performance benchmarks
    if total_time < 30:
        print("🎯 EXCELLENT: Sub-30 second processing ✅")
    elif total_time < 60:
        print("🎯 GOOD: Sub-60 second processing")
    else:
        print("🎯 SLOW: Consider further optimizations")
    
    if total_memory < 200 * 1024 * 1024:  # 200MB
        print("🎯 MEMORY EFFICIENT: < 200MB peak usage ✅")
    elif total_memory < 500 * 1024 * 1024:  # 500MB
        print("🎯 MODERATE: Memory usage acceptable")
    else:
        print("🎯 HIGH MEMORY: Consider memory optimizations")

if __name__ == "__main__":
    main()