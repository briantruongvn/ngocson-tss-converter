#!/usr/bin/env python3
"""
Step 2: Data Extraction from Excel Files
Extracts Article Name and Article Number from input Excel files and populates Step1 template.
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
import logging
from pathlib import Path
from typing import Union, Optional, List, Tuple, Dict
import argparse
import sys
import re

from common.validation import validate_step2_input, FileValidator
from common.exceptions import TSConverterError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataExtractor:
    """
    Data Extractor for Step 2
    
    Extracts Article Name and Article Number from Excel files:
    - Searches all sheets for "Product name"/"Article name" and "Product number"/"Article number"
    - Extracts vertical data until empty cell
    - Populates Step1 template with extracted data
    - Removes duplicate pairs
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.output_dir = self.base_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Headers to search for
        self.name_headers = ["Product name", "Article name", "product name", "article name"]
        self.number_headers = ["Product number", "Article number", "product number", "article number"]
    
    def find_header_cells(self, worksheet, headers: List[str]) -> List[Tuple[int, int]]:
        """
        Find cells containing specified headers in a worksheet
        
        Args:
            worksheet: openpyxl worksheet object
            headers: List of header strings to search for
            
        Returns:
            List of (row, col) tuples where headers are found
        """
        found_cells = []
        
        # Search through all cells in the worksheet
        for row in worksheet.iter_rows():
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    cell_value = cell.value.strip()
                    for header in headers:
                        if header.lower() in cell_value.lower():
                            found_cells.append((cell.row, cell.column))
                            logger.info(f"Found '{header}' at {worksheet.title}!{cell.coordinate}: {cell.value}")
                            break
        
        return found_cells
    
    def clean_value(self, value: str) -> str:
        """
        Clean individual value by removing trailing punctuation and whitespace
        
        Args:
            value: Raw value string
            
        Returns:
            Cleaned value string
        """
        if not value or not isinstance(value, str):
            return ""
        
        # Remove whitespace
        cleaned = value.strip()
        
        # Remove trailing punctuation (semicolon, comma, etc.)
        while cleaned and cleaned[-1] in ';,':
            cleaned = cleaned[:-1].strip()
        
        return cleaned
    
    def parse_multi_value_cell(self, value: str) -> List[str]:
        """
        Parse cell value that may contain multiple items separated by delimiters
        
        Args:
            value: Cell value string
            
        Returns:
            List of individual cleaned values
        """
        if not value or not isinstance(value, str):
            return []
        
        # Common delimiters: newline, semicolon, comma
        delimiters = ['\n', ';', ',']
        
        # Try each delimiter
        for delimiter in delimiters:
            if delimiter in value:
                # Split by delimiter and clean each part
                parts = [self.clean_value(part) for part in value.split(delimiter)]
                # Filter out empty strings
                parts = [part for part in parts if part]
                if len(parts) > 1:
                    logger.debug(f"Split '{value}' by '{delimiter}' into {len(parts)} parts")
                    return parts
        
        # No delimiter found, return as single cleaned item
        cleaned = self.clean_value(value)
        return [cleaned] if cleaned else []
    
    def extract_data_vertical(self, worksheet, start_row: int, start_col: int) -> List[str]:
        """
        Extract data vertically from worksheet starting from specified position
        Parse multi-value cells into individual items
        
        Args:
            worksheet: openpyxl worksheet object
            start_row: Starting row (1-based)
            start_col: Starting column (1-based)
            
        Returns:
            List of extracted individual data values
        """
        data = []
        current_row = start_row + 1  # Start from next row after header
        
        while True:
            cell = worksheet.cell(row=current_row, column=start_col)
            if cell.value is None or (isinstance(cell.value, str) and cell.value.strip() == ""):
                break
            
            # Convert value to string and clean it
            value = str(cell.value).strip()
            if value:
                # Parse multi-value cells
                parsed_values = self.parse_multi_value_cell(value)
                data.extend(parsed_values)
                logger.debug(f"Extracted from {worksheet.title}!{cell.coordinate}: {len(parsed_values)} items")
            
            current_row += 1
        
        return data
    
    def remove_duplicates(self, name_data: List[str], number_data: List[str]) -> Tuple[List[str], List[str]]:
        """
        Remove duplicate pairs from name and number data
        
        Args:
            name_data: List of article names
            number_data: List of article numbers
            
        Returns:
            Tuple of (unique_names, unique_numbers)
        """
        if len(name_data) != len(number_data):
            # Pad shorter list with empty strings
            max_len = max(len(name_data), len(number_data))
            name_data.extend([""] * (max_len - len(name_data)))
            number_data.extend([""] * (max_len - len(number_data)))
        
        seen_pairs = set()
        unique_names = []
        unique_numbers = []
        
        for name, number in zip(name_data, number_data):
            pair = (name, number)
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                unique_names.append(name)
                unique_numbers.append(number)
            else:
                logger.info(f"Removed duplicate pair: ('{name}', '{number}')")
        
        return unique_names, unique_numbers
    
    def process_file(self, step1_file: Union[str, Path], 
                    source_file: Union[str, Path],
                    output_file: Optional[Union[str, Path]] = None) -> str:
        """
        Process Step1 file and extract data from source file
        
        Args:
            step1_file: Step1 template file path
            source_file: Source Excel file to extract data from
            output_file: Optional output file path (if None, auto-generate)
            
        Returns:
            Path to output file
        """
        logger.info("📋 Step 2: Data Extraction")
        
        # Validate input files
        try:
            validate_step2_input(step1_file, source_file)
            step1_path = Path(step1_file)
            source_path = Path(source_file)
        except TSConverterError as e:
            logger.error(f"Input validation failed: {e}")
            raise
        
        # Auto-generate output file if not provided
        if output_file is None:
            base_name = step1_path.stem.replace(" - Step1", "")
            output_file = self.output_dir / f"{base_name} - Step2.xlsx"
        else:
            output_file = Path(output_file)
        
        # Validate output path is writable
        try:
            output_file = FileValidator.validate_output_writable(output_file)
        except TSConverterError as e:
            logger.error(f"Output validation failed: {e}")
            raise
        
        logger.info(f"Step1 Template: {step1_path}")
        logger.info(f"Source Data: {source_path}")
        logger.info(f"Output: {output_file}")
        
        # Load Step1 template (preserve formatting)
        step1_wb = openpyxl.load_workbook(str(step1_path))
        step1_ws = step1_wb.active
        
        # Load source file for data extraction
        source_wb = openpyxl.load_workbook(str(source_path))
        
        all_names = []
        all_numbers = []
        
        # Process each worksheet in source file
        for sheet_name in source_wb.sheetnames:
            logger.info(f"Processing sheet: {sheet_name}")
            worksheet = source_wb[sheet_name]
            
            # Find article name headers
            name_cells = self.find_header_cells(worksheet, self.name_headers)
            for row, col in name_cells:
                names = self.extract_data_vertical(worksheet, row, col)
                all_names.extend(names)
                logger.info(f"Extracted {len(names)} names from {sheet_name}!{worksheet.cell(row, col).coordinate}")
            
            # Find article number headers  
            number_cells = self.find_header_cells(worksheet, self.number_headers)
            for row, col in number_cells:
                numbers = self.extract_data_vertical(worksheet, row, col)
                all_numbers.extend(numbers)
                logger.info(f"Extracted {len(numbers)} numbers from {sheet_name}!{worksheet.cell(row, col).coordinate}")
        
        # Remove duplicates
        unique_names, unique_numbers = self.remove_duplicates(all_names, all_numbers)
        
        logger.info(f"Found {len(all_names)} total names, {len(unique_names)} unique")
        logger.info(f"Found {len(all_numbers)} total numbers, {len(unique_numbers)} unique")
        logger.info(f"Creating {max(len(unique_names), len(unique_numbers))} article pairs")
        
        # Populate Step1 template
        # Each pair (name, number) goes in one column starting from B
        max_pairs = max(len(unique_names), len(unique_numbers))
        
        for i in range(max_pairs):
            col = i + 2  # Column B = 2, C = 3, etc.
            
            # Row 1: Article name
            if i < len(unique_names):
                name = unique_names[i]
                cell = step1_ws.cell(row=1, column=col, value=name)
                logger.debug(f"Set {cell.coordinate} = '{name}'")
            
            # Row 2: Article number  
            if i < len(unique_numbers):
                number = unique_numbers[i]
                cell = step1_ws.cell(row=2, column=col, value=number)
                logger.debug(f"Set {cell.coordinate} = '{number}'")
        
        # Save output file
        try:
            step1_wb.save(str(output_file))
            logger.info(f"✅ Step 2 completed: {output_file}")
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise
        
        source_wb.close()
        step1_wb.close()
        
        return str(output_file)
    
    def extract_from_step1_source(self, step1_file: Union[str, Path],
                                 output_file: Optional[Union[str, Path]] = None) -> str:
        """
        Extract data from the original source file that was used to create Step1
        
        Args:
            step1_file: Step1 template file path  
            output_file: Optional output file path (if None, auto-generate)
            
        Returns:
            Path to output file
        """
        step1_path = Path(step1_file)
        
        # Try to find the original source file
        # Assume it's in input folder with same base name
        base_name = step1_path.stem.replace(" - Step1", "")
        source_candidates = [
            self.base_dir / "input" / f"{base_name}.xlsx",
            step1_path.parent.parent / "input" / f"{base_name}.xlsx",
            self.base_dir / f"{base_name}.xlsx"
        ]
        
        source_file = None
        for candidate in source_candidates:
            if candidate.exists():
                source_file = candidate
                break
        
        if source_file is None:
            raise FileNotFoundError(f"Could not find source file for {step1_path}")
        
        return self.process_file(step1_file, source_file, output_file)

def main():
    """Command line interface for data extraction"""
    parser = argparse.ArgumentParser(description='Data Extractor Step 2 - Extract Article Data')
    parser.add_argument('step1_file', help='Step1 template file (*.xlsx)')
    parser.add_argument('-s', '--source', help='Source file to extract data from (if not auto-detected)')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-d', '--base-dir', help='Base directory', default='.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize extractor
    extractor = DataExtractor(args.base_dir)
    
    try:
        if args.source:
            # Extract from specified source file
            result = extractor.process_file(args.step1_file, args.source, args.output)
        else:
            # Auto-detect source file
            result = extractor.extract_from_step1_source(args.step1_file, args.output)
        
        print(f"\n✅ Success!")
        print(f"📁 Output: {result}")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()