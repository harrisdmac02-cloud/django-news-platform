# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys
import django

from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath('../..'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'news_project.settings'

django.setup()

MOCK_MODULES = [
    'django.db.models.manager',
    'django.db.models.query',
    'django.db.models.fields.related_descriptors',
    'django.contrib.auth.models',
]

for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = MagicMock()

project = 'Django News Platform'
copyright = '2026, harrisdmac02-cloud'
author = 'harrisdmac02-cloud'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'migrations/*']

# Prevent autodoc from crashing on Django models with complex properties
autodoc_mock_imports = [
    'core.models',           # mock entire core.models module
    'core.views',
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
