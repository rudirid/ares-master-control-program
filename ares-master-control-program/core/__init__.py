"""
ARES Core Protocol Library v2.5
Codified from Ares v2.1 Internal Skeptic protocols
"""

from .validation import AresValidation, ValidationResult
from .output import AresOutput, AresResponse
from .patterns import AresPatternMatcher, Pattern

__all__ = [
    'AresValidation',
    'ValidationResult',
    'AresOutput',
    'AresResponse',
    'AresPatternMatcher',
    'Pattern'
]

__version__ = '2.5.0'
