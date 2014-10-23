from setuptools import setup, find_packages

# No third party dependencies, so importing the package should be safe.
import temporenc

setup(
    name='temporenc',
    version=temporenc.__version__,
    author="Wouter Bolsterlee",
    author_email="uws@xs4all.nl",
    url='https://github.com/wbolster/temporenc-python',
    packages=find_packages(),
)
