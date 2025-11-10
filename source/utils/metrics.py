# Author: HeartoLazor
# Description: Processing metrics and performance tracking

import time
from functools import wraps
from typing import Dict, Any
from dataclasses import dataclass, field

@dataclass
class ProcessingMetrics:
    files_processed: int = 0
    total_frames_generated: int = 0
    processing_time: float = 0.0
    errors_count: int = 0
    warnings_count: int = 0
    files_by_type: Dict[str, int] = field(default_factory=dict)
    
    def record_processing(self, frames_count: int, processing_time: float, file_type: str = "unknown"):
        self.files_processed += 1
        self.total_frames_generated += frames_count
        self.processing_time += processing_time
        self.files_by_type[file_type] = self.files_by_type.get(file_type, 0) + 1
    
    def record_error(self):
        self.errors_count += 1
    
    def record_warning(self):
        self.warnings_count += 1
    
    def get_summary(self) -> Dict[str, Any]:
        avg_time = self.processing_time / max(self.files_processed, 1)
        return {
            'files_processed': self.files_processed,
            'total_frames_generated': self.total_frames_generated,
            'processing_time': self.processing_time,
            'errors_count': self.errors_count,
            'warnings_count': self.warnings_count,
            'files_by_type': self.files_by_type,
            'average_time_per_file': avg_time
        }
    
    def print_summary(self):
        summary = self.get_summary()
        print(f"\n📊 Processing Summary:")
        print(f"   Files processed: {summary['files_processed']}")
        print(f"   Total frames: {summary['total_frames_generated']}")
        print(f"   Total time: {summary['processing_time']:.2f}s")
        print(f"   Average time per file: {summary['average_time_per_file']:.2f}s")
        print(f"   Errors: {summary['errors_count']}")
        print(f"   Warnings: {summary['warnings_count']}")
        if summary['files_by_type']:
            print(f"   Files by type: {summary['files_by_type']}")

def time_execution(description: str = ""):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            time_taken = end_time - start_time
            desc = description or func.__name__
            print(f"⏱️ {desc} executed in {time_taken:.2f} seconds")
            
            return result, time_taken
        return wrapper
    return decorator