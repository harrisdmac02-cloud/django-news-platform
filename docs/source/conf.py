# docs/source/conf.py

import os
import sys
import django

# Add project root to sys.path
sys.path.insert(0, os.path.abspath('../..'))

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'news_project.settings'

# 3. Initialize Django (required for models to be importable)
django.setup()

# ────────────────────────────────────────────────
# Sphinx configuration starts here
# ────────────────────────────────────────────────

project = 'Django News Platform'
author = 'mphor / harrisdmac02-cloud'
release = '0.1.0'
version = '0.1'

# General
extensions = [
    'sphinx.ext.autodoc',       # Pull docstrings from code
    'sphinx.ext.napoleon',      # Parse Google-style docstrings
    'sphinx.ext.viewcode',      # Add "view source" links
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# HTML output
html_theme = 'sphinx_rtd_theme'          # nice default theme
html_static_path = ['_static']

# Autodoc settings – make it more forgiving
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'private-members': False,           # skip _private things
    'special-members': False,
    'show-inheritance': True,
}

# Mock Django internals that often crash autodoc
autodoc_mock_imports = ['django.db.models.manager', 'django.db.models.query']