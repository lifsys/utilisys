# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.13] - 2024-08-04

### Changed
- Updated version number for PyPI release
- Several changes in utilisys.py:
  - Added `get_api` function for retrieving API keys from 1Password vault
  - Added `get_completion_api` function for handling API completions with various models
  - Updated `get_requirements` function to use DatabaseManager
  - Added `fix_json` function using LLM for JSON formatting
  - Added `iterative_llm_fix_json` function for iterative JSON fixing
  - Updated `safe_json_loads` function with improved error handling and LLM-based fixing
  - Added logging configuration and error handling improvements throughout the file

## [0.1.12] - 2024-08-04

### Changed
- Updated version number for PyPI release
- Several changes in utilisys.py (details added in 0.1.13)

## [0.1.11] - 2024-08-03

### Changed
- Updated version number for PyPI release

## [0.1.10] - [Release date of previous version]

[Add changes from the previous version here]
