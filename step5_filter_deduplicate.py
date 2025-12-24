#!/usr/bin/env python3
"""
Step 5: Filter and Deduplicate Data
Removes NA rows and deduplicates SD rows with data cleaning.
"""

import os
import openpyxl
from openpyxl.utils import get_column_letter
import logging
from pathlib import Path
from typing import Union, Optional, List, Dict, Tuple
import argparse
import sys
import shutil
from collections import defaultdict

from common.validation import validate_step5_input, FileValidator
from common.exceptions import TSConverterError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataFilter:
    """
    Data Filter for Step 5
    
    Two-stage filtering process:
    1. Remove rows where column H is NA/empty/"-"
    2. Deduplicate SD rows based on columns B,C,D,E,F,I similarity
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.output_dir = self.base_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Columns for comparison in SD deduplication
        self.comparison_columns = ['B', 'C', 'D', 'E', 'F', 'I', 'J']
        self.start_row = 4  # Start from row 4 (after headers)
    
    def is_na_value(self, cell_value) -> bool:
        """
        Check if cell value should be considered as NA/empty
        
        Args:
            cell_value: Cell value to check
            
        Returns:
            True if value is NA/empty/"-"
        """
        if cell_value is None:
            return True
        
        if isinstance(cell_value, str):
            cleaned = cell_value.strip().upper()
            return cleaned in ["", "NA", "-"]
        
        return False
    
    def get_row_values(self, worksheet, row: int, columns: List[str]) -> tuple:
        """
        Get values from specified columns in a row
        
        Args:
            worksheet: openpyxl worksheet object
            row: Row number (1-based)
            columns: List of column letters
            
        Returns:
            Tuple of values from specified columns
        """
        values = []
        for col_letter in columns:
            col_num = openpyxl.utils.column_index_from_string(col_letter)
            cell_value = worksheet.cell(row, col_num).value
            # Normalize value for comparison
            if cell_value is None:
                values.append("")
            elif isinstance(cell_value, str):
                values.append(cell_value.strip())
            else:
                values.append(str(cell_value))
        
        return tuple(values)
    
    def remove_na_rows(self, worksheet) -> int:
        """
        Remove rows where column H is NA/empty/"-"
        
        Args:
            worksheet: openpyxl worksheet object
            
        Returns:
            Number of rows removed
        """
        logger.info("Step 5.1: Removing NA rows from column H")
        
        h_col_num = openpyxl.utils.column_index_from_string('H')
        rows_to_delete = []
        
        # Find all rows to delete (process from bottom to top to avoid index issues)
        for row in range(worksheet.max_row, self.start_row - 1, -1):
            h_value = worksheet.cell(row, h_col_num).value
            
            if self.is_na_value(h_value):
                rows_to_delete.append(row)
                logger.debug(f"Marking row {row} for deletion (H = '{h_value}')")
        
        # Delete rows
        for row in rows_to_delete:
            worksheet.delete_rows(row, 1)
            logger.debug(f"Deleted row {row}")
        
        removed_count = len(rows_to_delete)
        logger.info(f"Removed {removed_count} NA rows")
        return removed_count
    
    def find_sd_duplicates(self, worksheet) -> Dict[tuple, List[int]]:
        """
        Find SD duplicate groups based on columns B,C,D,E,F,I,J similarity
        
        Args:
            worksheet: openpyxl worksheet object
            
        Returns:
            Dictionary mapping value tuples to list of row numbers
        """
        logger.info("Step 5.2: Finding SD duplicate groups")
        
        h_col_num = openpyxl.utils.column_index_from_string('H')
        duplicate_groups = defaultdict(list)
        
        # Find all SD rows and group by comparison columns
        for row in range(self.start_row, worksheet.max_row + 1):
            h_value = worksheet.cell(row, h_col_num).value
            
            if h_value and isinstance(h_value, str) and h_value.strip().upper() == "SD":
                # Get comparison values
                comparison_values = self.get_row_values(worksheet, row, self.comparison_columns)
                duplicate_groups[comparison_values].append(row)
                logger.debug(f"SD row {row}: {comparison_values}")
        
        # Filter to only actual duplicates (groups with > 1 row)
        actual_duplicates = {k: v for k, v in duplicate_groups.items() if len(v) > 1}
        
        logger.info(f"Found {len(actual_duplicates)} SD duplicate groups")
        for group_key, rows in actual_duplicates.items():
            logger.debug(f"Group {group_key}: rows {rows}")
        
        return actual_duplicates
    
    def determine_common_value(self, worksheet, rows: List[int], column: str) -> str:
        """
        Determine common value from a group of rows for specified column
        
        Args:
            worksheet: openpyxl worksheet object
            rows: List of row numbers
            column: Column letter
            
        Returns:
            Common value or "Yearly" as default
        """
        col_num = openpyxl.utils.column_index_from_string(column)
        values = []
        
        for row in rows:
            cell_value = worksheet.cell(row, col_num).value
            if cell_value and isinstance(cell_value, str):
                cleaned_value = cell_value.strip()
                if cleaned_value:
                    values.append(cleaned_value)
        
        # Find most common value
        if values:
            from collections import Counter
            counter = Counter(values)
            most_common = counter.most_common(1)[0][0]
            logger.debug(f"Common value for column {column}: '{most_common}' from {values}")
            return most_common
        
        logger.debug(f"No common value found for column {column}, using default 'Yearly'")
        return "Yearly"
    
    def deduplicate_sd_rows(self, worksheet) -> int:
        """
        Deduplicate SD rows and clean data
        
        Args:
            worksheet: openpyxl worksheet object
            
        Returns:
            Number of rows removed
        """
        duplicate_groups = self.find_sd_duplicates(worksheet)
        
        if not duplicate_groups:
            logger.info("No SD duplicates found")
            return 0
        
        rows_to_delete = []
        rows_processed = 0
        
        # Process each duplicate group
        for group_key, group_rows in duplicate_groups.items():
            logger.info(f"Processing duplicate group with {len(group_rows)} rows: {group_rows}")
            
            # Keep the first row, mark others for deletion
            keep_row = group_rows[0]
            delete_rows = group_rows[1:]
            rows_to_delete.extend(delete_rows)
            
            # Clean data in the kept row
            logger.debug(f"Keeping row {keep_row}, cleaning columns K,L,M")
            
            # Clear columns K, L, M (keep J)
            for col_letter in ['K', 'L', 'M']:
                col_num = openpyxl.utils.column_index_from_string(col_letter)
                worksheet.cell(keep_row, col_num).value = None
                logger.debug(f"Cleared {col_letter}{keep_row}")
            
            # Set column N to common value or "Yearly"
            n_col_num = openpyxl.utils.column_index_from_string('N')
            common_n_value = self.determine_common_value(worksheet, group_rows, 'N')
            worksheet.cell(keep_row, n_col_num).value = common_n_value
            logger.debug(f"Set N{keep_row} = '{common_n_value}'")
            
            rows_processed += 1
        
        # Delete duplicate rows (from bottom to top to avoid index issues)
        rows_to_delete.sort(reverse=True)
        for row in rows_to_delete:
            worksheet.delete_rows(row, 1)
            logger.debug(f"Deleted duplicate row {row}")
        
        removed_count = len(rows_to_delete)
        logger.info(f"Deduplicated {rows_processed} groups, removed {removed_count} duplicate rows")
        return removed_count
    
    def process_file(self, step4_file: Union[str, Path],
                    output_file: Optional[Union[str, Path]] = None) -> str:
        """
        Process Step4 file with filtering and deduplication
        
        Args:
            step4_file: Step4 input file path
            output_file: Optional output file path (if None, auto-generate)
            
        Returns:
            Path to output file
        """
        logger.info("📋 Step 5: Filter and Deduplicate")
        
        # Validate input file
        try:
            validate_step5_input(step4_file)
            step4_path = Path(step4_file)
        except TSConverterError as e:
            logger.error(f"Input validation failed: {e}")
            raise
        
        # Enhanced output file handling with directory management
        if output_file is None:
            base_name = step4_path.stem.replace(" - Step4", "")
            output_file = self.output_dir / f"{base_name} - Step5.xlsx"
            logger.info(f"Auto-generated output path: {output_file}")
        else:
            output_file = Path(output_file)
            logger.info(f"Using provided output path: {output_file}")
            
            # Ensure parent directory exists for provided output path
            if not output_file.parent.exists():
                logger.info(f"Creating output directory: {output_file.parent}")
                output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # CRITICAL FIX: Always ensure output_file path is writable, no fallback for explicit paths
        try:
            # For explicitly provided paths, create the directory structure if needed
            if output_file.parent != self.output_dir:
                logger.info(f"Ensuring directory structure exists: {output_file.parent}")
                output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Simple writability check without FileValidator.validate_output_writable which may change path
            if output_file.exists() and not os.access(output_file, os.W_OK):
                raise TSConverterError(f"Output file is not writable: {output_file}")
            if not os.access(output_file.parent, os.W_OK):
                raise TSConverterError(f"Output directory is not writable: {output_file.parent}")
                
            logger.info(f"Output path validation successful: {output_file}")
        except TSConverterError as e:
            logger.error(f"Output validation failed: {e}")
            raise
        
        logger.info(f"Input: {step4_path}")
        logger.info(f"Final output: {output_file}")
        
        # Copy Step4 file as starting point with enhanced error handling
        try:
            shutil.copy2(str(step4_path), str(output_file))
            logger.info("Copied Step4 file as base")
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to copy input file to output location: {e}")
            raise TSConverterError(f"Could not create output file: {str(e)}")
        
        # Load workbook with enhanced error handling
        try:
            wb = openpyxl.load_workbook(str(output_file))
            ws = wb.active
        except Exception as e:
            logger.error(f"Failed to load workbook from {output_file}: {e}")
            raise TSConverterError(f"Could not open output file for processing: {str(e)}")
        
        # Get initial stats
        initial_rows = ws.max_row
        logger.info(f"Initial rows: {initial_rows}")
        
        try:
            # Step 5.1: Remove NA rows
            na_removed = self.remove_na_rows(ws)
            
            # Step 5.2: Deduplicate SD rows
            sd_removed = self.deduplicate_sd_rows(ws)
            
            # Get final stats
            final_rows = ws.max_row
            total_removed = na_removed + sd_removed
            
            logger.info("Processing Summary:")
            logger.info(f"  Initial rows: {initial_rows}")
            logger.info(f"  NA rows removed: {na_removed}")
            logger.info(f"  SD duplicates removed: {sd_removed}")
            logger.info(f"  Total rows removed: {total_removed}")
            logger.info(f"  Final rows: {final_rows}")
            
            # Save output file with enhanced error handling
            try:
                wb.save(str(output_file))
                logger.info(f"✅ Step 5 completed: {output_file}")
                
                # Verify file was actually saved and is accessible
                if not output_file.exists():
                    raise TSConverterError(f"Output file was not created successfully: {output_file}")
                    
                file_size = output_file.stat().st_size
                logger.info(f"Output file size: {file_size} bytes")
                
            except Exception as save_error:
                logger.error(f"Failed to save file: {save_error}")
                raise TSConverterError(f"Could not save output file: {str(save_error)}")
                
        except Exception as process_error:
            logger.error(f"Processing error during Step 5: {process_error}")
            raise TSConverterError(f"Data processing failed: {str(process_error)}")
        finally:
            # Always close workbook to free resources
            try:
                wb.close()
            except Exception as close_error:
                logger.warning(f"Could not close workbook properly: {close_error}")
        
        return str(output_file)

def main():
    """Command line interface for data filtering and deduplication"""
    parser = argparse.ArgumentParser(description='Data Filter Step 5 - Filter and Deduplicate')
    parser.add_argument('step4_file', help='Step4 input file (*.xlsx)')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-d', '--base-dir', help='Base directory', default='.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize filter
    filter_processor = DataFilter(args.base_dir)
    
    try:
        result = filter_processor.process_file(args.step4_file, args.output)
        
        print(f"\n✅ Success!")
        print(f"📁 Output: {result}")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()