# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.15] - 2024-08-11

### Changed
- Updated version number for PyPI release
- Improved JSON processing in utilisys.py:
  - Enhanced `fix_json`, `iterative_llm_fix_json`, and `safe_json_loads` functions
  - Improved error handling and logging for JSON-related operations
- Updated `get_requirements` function to use DatabaseManager's use_table method
- Updated documentation and version numbers in setup.py, __init__.py, README.md, and PKG-INFO

## [0.1.14] - 2024-08-05

### Changed
- Updated version number for PyPI release
- Several changes in utilisys.py:
  - Updated `get_requirements` function to use `use_table` method instead of `table` method
  - Modified `fix_json` function to use Groq's llama-3.1-8b-instant model
  - Updated `iterative_llm_fix_json` and `safe_json_loads` functions to use OpenAI's gpt-4o-mini model
  - Added `json_mode=True` parameter to Intelisys calls for better JSON handling
  - Improved error handling and logging in various functions

## [0.1.13] - 2024-08-04

### Changed
- Updated version number for PyPI release
- Several changes in utilisys.py (details added in 0.1.13)

## [0.1.11] - 2024-08-03

### Changed
- Updated version number for PyPI release

## [0.1.10] - [Release date of previous version]

[Add changes from the previous version here]
