import pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

with open(HERE / "requirements.txt") as f:
    required = f.read().splitlines()

# This call to setup() does all the work
setup(
    name="coderius-play",
    version="3.2.0",
    description="The easiest way to make games and media projects in Python.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/Coderius-Education/play",
    author="koen1711",
    author_email="koen@coderius.nl",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    python_requires=">=3.10",
    packages=find_packages(),
    include_package_data=True,
    install_requires=required,
)
