from os.path import exists
from setuptools import find_packages, setup

readme = open(",/laplan/README.md").read() if exists("./laplan/README.md") else ""

setup(
    name="laplan",
    packages=find_packages(),
    version="0.1.0",
    description="Utilities for analyzing Los Angeles City Planning data",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Hunter Owens",
    license="Apache-2.0 license",
    include_package_data=True,
    package_dir={"laplan": "laplan"},
    install_requires=["pandas"],
)
