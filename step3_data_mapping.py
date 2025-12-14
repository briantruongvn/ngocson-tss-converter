#!/usr/bin/env python3
"""
Step 3: Data Mapping and Transfer
Maps data from source Excel file to Step2 template with specific column mappings.
"""

import openpyxl
from openpyxl.utils import get_column_letter
import logging
from pathlib import Path
from typing import Union, Optional, List, Tuple, Dict
import argparse
import sys
import shutil

from common.validation import validate_step3_input, FileValidator
from common.exceptions import TSConverterError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataMapper:
    """
    Data Mapper for Step 3
    
    Maps data from source Excel file to Step2 template:
    - Processes sheets containing 'test plan' or 'summary'
    - Special mapping for 'finished product' sheet
    - General mapping for other sheets
    - Combines specified columns with delimiter
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.output_dir = self.base_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Column mappings for different sheet types
        self.finished_product_mapping = {
            'C': 'D',   # C -> D
            'H': 'F',   # H -> F
            'KL': 'I',  # K & L combined -> I
            'M': 'J',   # M -> J
            'N': 'K',   # N -> K
            'O': 'L',   # O -> L
            'P': 'M',   # P -> M
            'Q': 'N',   # Q -> N
            'S': 'O',   # S -> O
            'T': 'H',   # T -> H
            'W': 'P'    # W -> P
        }
        
        self.other_sheets_mapping = {
            'B': 'B',   # B -> B
            'C': 'C',   # C -> C
            'I': 'D',   # I -> D
            'J': 'F',   # J -> F
            'K': 'E',   # K -> E
            'NO': 'I',  # N & O combined -> I
            'P': 'J',   # P -> J
            'Q': 'K',   # Q -> K
            'R': 'L',   # R -> L
            'S': 'M',   # S -> M
            'T': 'N',   # T -> N
            'W': 'H',   # W -> H
            'Z': 'P'    # Z -> P
        }
    
    def is_sheet_relevant(self, sheet_name: str, worksheet) -> bool:
        """
        Check if sheet is relevant for processing
        
        Args:
            sheet_name: Name of the worksheet
            worksheet: openpyxl worksheet object
            
        Returns:
            True if sheet should be processed
        """
        # Check if sheet is empty first
        if worksheet.max_row == 1 and worksheet.max_column == 1:
            cell_value = worksheet.cell(1, 1).value
            if cell_value is None or (isinstance(cell_value, str) and cell_value.strip() == ""):
                logger.debug(f"Skipping empty sheet '{sheet_name}'")
                return False
        
        # Accept sheets with 'test plan', 'summary', or process all sheets that aren't empty
        sheet_lower = sheet_name.lower()
        if ('test plan' in sheet_lower or 'summary' in sheet_lower or 
            'finished product' in sheet_lower or 'textile' in sheet_lower):
            logger.info(f"Processing sheet: '{sheet_name}'")
            return True
        
        # For other sheets, check if they have substantial content
        # This allows processing of sheets that may contain test data but don't have specific names
        if worksheet.max_row > 10:  # Sheets with more than 10 rows might have useful data
            logger.info(f"Processing sheet: '{sheet_name}' (has content)")
            return True
        
        logger.debug(f"Skipping sheet '{sheet_name}' - no relevant content")
        return False
    
    def find_header_row(self, worksheet, header_text: str = "product combination") -> Optional[int]:
        """
        Find row containing the header text (case insensitive)
        
        Args:
            worksheet: openpyxl worksheet object
            header_text: Text to search for in headers
            
        Returns:
            Row number (1-based) or None if not found
        """
        for row in range(1, min(worksheet.max_row + 1, 50)):  # Search first 50 rows
            for col in range(1, worksheet.max_column + 1):
                cell = worksheet.cell(row, col)
                if cell.value and isinstance(cell.value, str):
                    if header_text.lower() in cell.value.lower():
                        logger.info(f"Found '{header_text}' at row {row}, column {get_column_letter(col)}")
                        return row
        
        logger.warning(f"Header '{header_text}' not found in worksheet")
        return None
    
    def combine_columns(self, worksheet, row: int, col1: str, col2: str, delimiter: str = "-") -> str:
        """
        Combine values from two columns with delimiter
        
        Args:
            worksheet: openpyxl worksheet object
            row: Row number (1-based)
            col1: First column letter
            col2: Second column letter
            delimiter: Delimiter between values
            
        Returns:
            Combined string value
        """
        col1_num = openpyxl.utils.column_index_from_string(col1)
        col2_num = openpyxl.utils.column_index_from_string(col2)
        
        val1 = worksheet.cell(row, col1_num).value
        val2 = worksheet.cell(row, col2_num).value
        
        # Convert to strings and clean
        str1 = str(val1).strip() if val1 is not None else ""
        str2 = str(val2).strip() if val2 is not None else ""
        
        # Combine with delimiter
        if str1 and str2:
            return f"{str1}{delimiter}{str2}"
        elif str1:
            return str1
        elif str2:
            return str2
        else:
            return ""
    
    def map_finished_product_data(self, source_ws, target_ws, start_row: int, target_start_row: int) -> int:
        """
        Map data from finished product sheet using special mapping
        
        Args:
            source_ws: Source worksheet
            target_ws: Target worksheet
            start_row: Starting row in source (1-based)
            target_start_row: Starting row in target (1-based)
            
        Returns:
            Next available row in target worksheet
        """
        logger.info(f"Mapping finished product data from row {start_row}")
        current_target_row = target_start_row
        
        # Process each row until empty
        for source_row in range(start_row, source_ws.max_row + 1):
            # Check if row has any data
            has_data = False
            for col in range(1, source_ws.max_column + 1):
                if source_ws.cell(source_row, col).value is not None:
                    has_data = True
                    break
            
            if not has_data:
                logger.debug(f"Stopping at empty row {source_row}")
                break
            
            logger.debug(f"Processing source row {source_row} -> target row {current_target_row}")
            
            # Apply column mappings
            for source_col, target_col in self.finished_product_mapping.items():
                if source_col == 'KL':  # Special case: combine K & L
                    combined_value = self.combine_columns(source_ws, source_row, 'K', 'L')
                    target_col_num = openpyxl.utils.column_index_from_string(target_col)
                    target_ws.cell(current_target_row, target_col_num, combined_value)
                    logger.debug(f"Combined K&L -> {target_col}: '{combined_value}'")
                else:
                    # Single column mapping
                    source_col_num = openpyxl.utils.column_index_from_string(source_col)
                    target_col_num = openpyxl.utils.column_index_from_string(target_col)
                    
                    source_value = source_ws.cell(source_row, source_col_num).value
                    if source_value is not None:
                        target_ws.cell(current_target_row, target_col_num, source_value)
                        logger.debug(f"{source_col} -> {target_col}: '{source_value}'")
            
            current_target_row += 1
        
        rows_mapped = current_target_row - target_start_row
        logger.info(f"Mapped {rows_mapped} rows from finished product sheet")
        return current_target_row
    
    def map_other_sheet_data(self, source_ws, target_ws, start_row: int, target_start_row: int) -> int:
        """
        Map data from other sheets using general mapping
        
        Args:
            source_ws: Source worksheet
            target_ws: Target worksheet
            start_row: Starting row in source (1-based)
            target_start_row: Starting row in target (1-based)
            
        Returns:
            Next available row in target worksheet
        """
        logger.info(f"Mapping other sheet data from row {start_row}")
        current_target_row = target_start_row
        
        # Process each row until empty
        for source_row in range(start_row, source_ws.max_row + 1):
            # Check if row has any data
            has_data = False
            for col in range(1, source_ws.max_column + 1):
                if source_ws.cell(source_row, col).value is not None:
                    has_data = True
                    break
            
            if not has_data:
                logger.debug(f"Stopping at empty row {source_row}")
                break
            
            logger.debug(f"Processing source row {source_row} -> target row {current_target_row}")
            
            # Apply column mappings
            for source_col, target_col in self.other_sheets_mapping.items():
                if source_col == 'NO':  # Special case: combine N & O
                    combined_value = self.combine_columns(source_ws, source_row, 'N', 'O')
                    target_col_num = openpyxl.utils.column_index_from_string(target_col)
                    target_ws.cell(current_target_row, target_col_num, combined_value)
                    logger.debug(f"Combined N&O -> {target_col}: '{combined_value}'")
                else:
                    # Single column mapping
                    source_col_num = openpyxl.utils.column_index_from_string(source_col)
                    target_col_num = openpyxl.utils.column_index_from_string(target_col)
                    
                    source_value = source_ws.cell(source_row, source_col_num).value
                    if source_value is not None:
                        target_ws.cell(current_target_row, target_col_num, source_value)
                        logger.debug(f"{source_col} -> {target_col}: '{source_value}'")
            
            current_target_row += 1
        
        rows_mapped = current_target_row - target_start_row
        logger.info(f"Mapped {rows_mapped} rows from other sheet")
        return current_target_row
    
    def process_file(self, source_file: Union[str, Path],
                    step2_file: Union[str, Path],
                    output_file: Optional[Union[str, Path]] = None) -> str:
        """
        Process source file and map data to Step2 template
        
        Args:
            source_file: Source Excel file to extract data from
            step2_file: Step2 template file
            output_file: Optional output file path (if None, auto-generate Step3)
            
        Returns:
            Path to output file
        """
        logger.info("📋 Step 3: Data Mapping")
        
        # Validate input files
        try:
            source_path = FileValidator.validate_file_format(source_file)
            # Skip Step3 validation as Step2 only has 3 template rows, no data rows
            # validate_step3_input(step2_file)
            step2_path = Path(step2_file)
        except TSConverterError as e:
            logger.error(f"Input validation failed: {e}")
            raise
        
        # Auto-generate output file if not provided
        if output_file is None:
            base_name = step2_path.stem.replace(" - Step2", "")
            output_file = self.output_dir / f"{base_name} - Step3.xlsx"
        else:
            output_file = Path(output_file)
        
        # Validate output path is writable
        try:
            output_file = FileValidator.validate_output_writable(output_file)
        except TSConverterError as e:
            logger.error(f"Output validation failed: {e}")
            raise
        
        logger.info(f"Source: {source_path}")
        logger.info(f"Step2 Template: {step2_path}")
        logger.info(f"Output: {output_file}")
        
        # Copy Step2 file as starting point
        shutil.copy2(str(step2_path), str(output_file))
        logger.info("Copied Step2 template as base")
        
        # Load workbooks
        source_wb = openpyxl.load_workbook(str(source_path))
        target_wb = openpyxl.load_workbook(str(output_file))
        target_ws = target_wb.active
        
        # Find next available row in target (after existing data)
        next_row = 4  # Start from row 4 (after headers and article data)
        while target_ws.cell(next_row, 2).value is not None:  # Check column B
            next_row += 1
        
        logger.info(f"Starting data mapping at target row {next_row}")
        
        # Process each sheet in source file
        finished_product_processed = False
        
        for sheet_name in source_wb.sheetnames:
            worksheet = source_wb[sheet_name]
            
            # Check if sheet is relevant for processing
            if not self.is_sheet_relevant(sheet_name, worksheet):
                continue
            
            # Check if this is finished product sheet
            if 'finished product' in sheet_name.lower():
                logger.info(f"Processing finished product sheet: {sheet_name}")
                
                # Find header row
                header_row = self.find_header_row(worksheet, "product combination")
                if header_row is None:
                    logger.warning(f"No 'product combination' found in {sheet_name}, skipping")
                    continue
                
                # Data starts at header_row + 2
                data_start_row = header_row + 2
                next_row = self.map_finished_product_data(worksheet, target_ws, data_start_row, next_row)
                finished_product_processed = True
                
            else:
                logger.info(f"Processing other sheet: {sheet_name}")
                
                # Find header row
                header_row = self.find_header_row(worksheet, "product combination")
                if header_row is None:
                    logger.warning(f"No 'product combination' found in {sheet_name}, skipping")
                    continue
                
                # Data starts at header_row + 2
                data_start_row = header_row + 2
                next_row = self.map_other_sheet_data(worksheet, target_ws, data_start_row, next_row)
        
        # Save output file
        try:
            target_wb.save(str(output_file))
            logger.info(f"✅ Step 3 completed: {output_file}")
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise
        
        source_wb.close()
        target_wb.close()
        
        return str(output_file)

def main():
    """Command line interface for data mapping"""
    parser = argparse.ArgumentParser(description='Data Mapper Step 3 - Map Excel Data')
    parser.add_argument('source_file', help='Source Excel file to extract data from')
    parser.add_argument('step2_file', help='Step2 template file (*.xlsx)')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-d', '--base-dir', help='Base directory', default='.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize mapper
    mapper = DataMapper(args.base_dir)
    
    try:
        result = mapper.process_file(args.source_file, args.step2_file, args.output)
        
        print(f"\n✅ Success!")
        print(f"📁 Output: {result}")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()