# Minimal Sphinx configuration for ReadTheDocs

import os
import sys
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../src'))

# Mock imports for modules that require external dependencies
# This allows Sphinx to build documentation without installing all dependencies
autodoc_mock_imports = [
 'fastapi', 'pydantic', 'uvicorn', 'pandas', 'numpy', 
 'prophet', 'chronos', 'sklearn', 'requests', 'bs4',
 'selenium', 'torch', 'transformers', 'plotly', 'matplotlib',
 'scipy', 'statsmodels', 'holidays', 'scikit-learn'
]

project = 'Project Energy Tariffs'
copyright = '2025, Julius Becker'
author = 'Julius Becker'

extensions = [
 'sphinx.ext.autodoc',
 'sphinx.ext.napoleon',
 'sphinx.ext.viewcode',
]

# Autodoc settings
autodoc_default_options = {
 'members': True,
 'member-order': 'bysource',
 'special-members': '__init__',
 'undoc-members': True,
 'exclude-members': '__weakref__'
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'alabaster'
html_static_path = ['_static']
