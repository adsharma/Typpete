from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()


config = {
    "description": "Typpete",
    "author": "Caterina Urban",
    "url": "https://github.com/caterinaurban/Typpete",
    "download_url": "https://github.com/caterinaurban/Typpete",
    "author_email": "caterina.urban@gmail.com",
    "version": "0.1",
    "install_requires": ["astor", "z3-solver"],
    "scripts": [],
    "name": "Typpete",
    "entry_points": {"console_scripts": ["typpete=typpete.inference_runner:main"]},
}

setup(
    **config,
    long_description=readme + "\n\n",
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["old_tests", "unittests", "unittests*"]),
)
