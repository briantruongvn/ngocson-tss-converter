"""
Quality Reporter for TSS Converter
Tracks processing warnings, errors, and provides quality metrics for user feedback
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class ProcessingIssue:
    """Represents a processing issue (warning or error)"""
    level: str  # 'warning', 'error', 'info'
    step: str   # 'step1', 'step2', etc.
    category: str  # 'missing_headers', 'formula_errors', 'data_validation', etc.
    message: str
    details: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'level': self.level,
            'step': self.step,
            'category': self.category,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }

class QualityReporter:
    """
    Tracks processing quality and provides user-friendly feedback
    """
    
    def __init__(self):
        self.issues: List[ProcessingIssue] = []
        self.processing_stats = {
            'start_time': None,
            'end_time': None,
            'steps_completed': 0,
            'total_warnings': 0,
            'total_errors': 0,
            'files_processed': 0,
            'data_rows_extracted': 0,
            'data_rows_final': 0
        }
        
    def start_processing(self):
        """Mark start of processing"""
        self.processing_stats['start_time'] = datetime.now()
        
    def end_processing(self):
        """Mark end of processing"""
        self.processing_stats['end_time'] = datetime.now()
        
    def add_issue(self, level: str, step: str, category: str, message: str, details: Optional[str] = None):
        """Add a processing issue"""
        issue = ProcessingIssue(
            level=level,
            step=step,
            category=category,
            message=message,
            details=details
        )
        
        self.issues.append(issue)
        
        if level == 'warning':
            self.processing_stats['total_warnings'] += 1
        elif level == 'error':
            self.processing_stats['total_errors'] += 1
            
        logger.log(
            logging.WARNING if level == 'warning' else logging.ERROR,
            f"{step.upper()}: {message}"
        )
        
    def add_warning(self, step: str, category: str, message: str, details: Optional[str] = None):
        """Add a warning"""
        self.add_issue('warning', step, category, message, details)
        
    def add_error(self, step: str, category: str, message: str, details: Optional[str] = None):
        """Add an error"""
        self.add_issue('error', step, category, message, details)
        
    def add_info(self, step: str, category: str, message: str, details: Optional[str] = None):
        """Add an info message"""
        self.add_issue('info', step, category, message, details)
        
    def step_completed(self, step_name: str):
        """Mark a step as completed"""
        self.processing_stats['steps_completed'] += 1
        self.add_info(step_name, 'completion', f'{step_name} completed successfully')
        
    def update_stats(self, **kwargs):
        """Update processing statistics"""
        self.processing_stats.update(kwargs)
        
    def get_issues_by_level(self, level: str) -> List[ProcessingIssue]:
        """Get all issues of a specific level"""
        return [issue for issue in self.issues if issue.level == level]
        
    def get_issues_by_step(self, step: str) -> List[ProcessingIssue]:
        """Get all issues for a specific step"""
        return [issue for issue in self.issues if issue.step == step]
        
    def get_issues_by_category(self, category: str) -> List[ProcessingIssue]:
        """Get all issues of a specific category"""
        return [issue for issue in self.issues if issue.category == category]
        
    def has_critical_errors(self) -> bool:
        """Check if there are any critical errors that would prevent processing"""
        critical_categories = ['file_validation_failed', 'processing_failed']
        return any(
            issue.level == 'error' and issue.category in critical_categories
            for issue in self.issues
        )
        
    def get_quality_score(self) -> float:
        """Calculate a quality score from 0-100 based on issues"""
        if not self.issues:
            return 100.0
            
        # Deduct points for different types of issues
        score = 100.0
        
        for issue in self.issues:
            if issue.level == 'error':
                if issue.category in ['file_validation_failed', 'processing_failed']:
                    score -= 30  # Critical errors
                else:
                    score -= 15  # Regular errors
            elif issue.level == 'warning':
                if issue.category in ['missing_headers', 'formula_errors']:
                    score -= 10   # Data quality warnings (increased penalty)
                elif issue.category in ['validation_warning', 'validation_failed']:
                    score -= 15   # Validation issues are more serious
                else:
                    score -= 5   # Minor warnings
                    
        # Additional penalty for multiple missing headers (indicates poor input quality)
        missing_headers_count = len([i for i in self.issues if i.category == 'missing_headers'])
        if missing_headers_count >= 2:
            score -= 20  # Severe penalty for multiple missing header warnings
                    
        return max(0.0, score)
        
    def get_user_summary(self) -> Dict[str, Any]:
        """Get a user-friendly summary of processing quality"""
        warnings = self.get_issues_by_level('warning')
        errors = self.get_issues_by_level('error')
        
        # Categorize issues for user display
        data_issues = []
        processing_issues = []
        
        for issue in warnings + errors:
            if issue.category in ['missing_headers', 'formula_errors', 'data_validation']:
                data_issues.append(issue)
            else:
                processing_issues.append(issue)
        
        # Generate user-friendly messages
        summary = {
            'quality_score': self.get_quality_score(),
            'total_issues': len(self.issues),
            'warnings_count': len(warnings),
            'errors_count': len(errors),
            'data_quality_issues': len(data_issues),
            'processing_issues': len(processing_issues),
            'processing_time': None,
            'recommendations': []
        }
        
        # Calculate processing time
        if self.processing_stats['start_time'] and self.processing_stats['end_time']:
            delta = self.processing_stats['end_time'] - self.processing_stats['start_time']
            summary['processing_time'] = delta.total_seconds()
            
        # Generate recommendations
        if data_issues:
            summary['recommendations'].append(
                "Consider reviewing your input file for missing headers or formula errors to improve data quality."
            )
            
        if summary['quality_score'] < 80:
            summary['recommendations'].append(
                "The processing quality score is below 80%. Please check the detailed issues below."
            )
            
        if not errors and not warnings:
            summary['recommendations'].append(
                "Excellent! Your file was processed without any issues."
            )
            
        return summary
        
    def get_detailed_report(self) -> Dict[str, Any]:
        """Get a detailed report for debugging"""
        return {
            'issues': [issue.to_dict() for issue in self.issues],
            'statistics': self.processing_stats.copy(),
            'summary': self.get_user_summary()
        }
        
    def export_report(self, file_path: str):
        """Export detailed report to JSON file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.get_detailed_report(), f, indent=2, ensure_ascii=False)
            
    def clear(self):
        """Clear all issues and reset statistics"""
        self.issues.clear()
        self.processing_stats = {
            'start_time': None,
            'end_time': None,
            'steps_completed': 0,
            'total_warnings': 0,
            'total_errors': 0,
            'files_processed': 0,
            'data_rows_extracted': 0,
            'data_rows_final': 0
        }

# Global instance for easy access
_global_reporter = QualityReporter()

def get_global_reporter() -> QualityReporter:
    """Get the global quality reporter instance"""
    return _global_reporter

def reset_global_reporter():
    """Reset the global quality reporter"""
    global _global_reporter
    _global_reporter.clear()

# Convenience functions for the global reporter
def add_warning(step: str, category: str, message: str, details: Optional[str] = None):
    """Add warning to global reporter"""
    _global_reporter.add_warning(step, category, message, details)

def add_error(step: str, category: str, message: str, details: Optional[str] = None):
    """Add error to global reporter"""
    _global_reporter.add_error(step, category, message, details)

def add_info(step: str, category: str, message: str, details: Optional[str] = None):
    """Add info to global reporter"""
    _global_reporter.add_info(step, category, message, details)

def step_completed(step_name: str):
    """Mark step completed in global reporter"""
    _global_reporter.step_completed(step_name)

def get_user_summary() -> Dict[str, Any]:
    """Get user summary from global reporter"""
    return _global_reporter.get_user_summary()