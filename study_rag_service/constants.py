
from typing import Optional
from pydantic import BaseModel,Field
from dataclasses import dataclass


@dataclass
class QualityScore:
    """Data class to hold quality evaluation scores"""
    structure_score: int
    coverage_score: int
    examples_score: int
    clarity_score: int
    formatting_score: int
    final_score: int
    missing: list
    feedback: str    
