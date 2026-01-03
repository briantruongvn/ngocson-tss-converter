#!/usr/bin/env python3
"""
Verification script to test all imports work correctly
"""

import sys
import traceback

def test_import(module_name, description):
    """Test importing a module and report results"""
    try:
        __import__(module_name)
        print(f"✅ {description}: {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {description}: {module_name} - {e}")
        traceback.print_exc()
        return False

def main():
    """Test all critical imports"""
    print("🔍 TSS Converter Import Verification")
    print("="*50)
    
    all_passed = True
    
    # Test individual pipeline modules
    modules_to_test = [
        ("step1_template_creation", "Step 1 Template Creation"),
        ("step2_data_extraction", "Step 2 Data Extraction"),
        ("step3_pre_mapping_fill", "Step 3 Pre Mapping Fill"),
        ("step4_data_mapping", "Step 4 Data Mapping"), 
        ("step5_filter_deduplicate", "Step 5 Filter Deduplicate"),
        ("step6_article_crossref", "Step 6 Article Crossref"),
    ]
    
    for module, desc in modules_to_test:
        if not test_import(module, desc):
            all_passed = False
    
    # Test streamlit pipeline
    print("\n🌟 Testing Streamlit Integration:")
    print("-"*30)
    
    if not test_import("streamlit_pipeline", "Streamlit Pipeline"):
        all_passed = False
    
    # Test main app
    if not test_import("app", "Main Streamlit App"):
        all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 ALL IMPORTS SUCCESSFUL! App should work perfectly.")
        return 0
    else:
        print("💥 SOME IMPORTS FAILED! Fix required before deployment.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)