import pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

with open(HERE / "requirements.txt", "r", encoding="utf-8") as f:
    required = f.read().splitlines()

# This call to setup() does all the work
setup(
    name="coderius-play",
    version="3.5.0",
    description="The easiest way to make games and media projects in Python.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/Coderius-Education/play",
    author="koen1711",
    author_email="koen@coderius.nl",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Programming Language :: Python :: 3.15",
    ],
    python_requires=">=3.11",
    packages=find_packages(),
    include_package_data=True,
    install_requires=required,
)
