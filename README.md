# Utilisys by Lifsys, Inc

Utilisys is a Python package developed by Lifsys, Inc that provides a collection of utility functions for various tasks including API key retrieval, phone number standardization, dictionary flattening, contract requirement handling, email parsing, file operations, and data processing and conversion.

## Installation

You can install Utilisys using pip:

```
pip install utilisys
```

## Usage

Here's a quick example of how to use Utilisys:

```python
from utilisys import standardize_phone_number, flatten_dict

# Standardize a phone number
phone = standardize_phone_number("(123) 456-7890")
print(phone)  # Output: +1 123-456-7890

# Flatten a nested dictionary
nested_dict = {"a": 1, "b": {"c": 2, "d": {"e": 3}}}
flat_dict = flatten_dict(nested_dict)
print(flat_dict)  # Output: {'a': 1, 'b_c': 2, 'b_d_e': 3}
```

For more detailed usage instructions, please refer to the documentation.

## Version History

- 0.1.3: Updated for PyPI release
  - Updated version number in setup.py
  - Updated changelog in README.md
  - Fixed import statement in utilisys.py (changed 'intellisys' to 'intelisys')
- 0.1.2: Prepared for PyPI update
- 0.1.1: Added support for Python 3.10 and 3.11
- 0.1.0: Initial release

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## About Lifsys, Inc

Lifsys, Inc is an AI company dedicated to developing solutions for the future. For more information, visit [www.lifsys.com](https://www.lifsys.com).
