"""
Provides utility functions for processing text, files, and data.

This module contains a collection of utility functions for various tasks including:
- API key retrieval
- Phone number standardization
- Dictionary flattening
- Contract requirement handling
- Email parsing
- File operations
- Data processing and conversion

These utilities are designed to support various operations in the utilisys system.
"""
# Standard library imports
from email import policy
from email.parser import BytesParser
from typing import Optional
import logging
import re
import os
import json

# Third-party imports
import phonenumbers
import pandas as pd
import redis.asyncio as redis
from fuzzywuzzy import fuzz
import requests
from bs4 import BeautifulSoup
import urllib3
from onepasswordconnectsdk import new_client_from_environment
from sqlalchemy import create_engine

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import all functions from utilisys.py
from .utilisys import *
