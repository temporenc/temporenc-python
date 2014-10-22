#
# Project settings
#

project = 'Temporenc'
copyright = '2014, Wouter Bolsterlee'
version = '0.1'  # TODO: get from project
release = version

#
# Extensions
#

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
]

autodoc_member_order = 'bysource'


#
# Files and paths
#

master_doc = 'index'
templates_path = ['_templates']
source_suffix = '.rst'
exclude_patterns = ['build']


#
# Output
#

pygments_style = 'sphinx'
html_theme = 'default'
html_static_path = ['_static']
html_domain_indices = False
html_use_index = False
html_show_sphinx = False
html_show_copyright = False
