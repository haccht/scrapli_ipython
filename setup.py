from setuptools import setup, find_packages

setup(
    name="scrapli_ipython",
    version="0.0.3",
    install_requires=[
        "scrapli[ssh2]",
        "ntc_templates",
    ],
    author="haccht",
    description="scrapli extention for ipython",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/haccht/scrapli_ipython",
    packages=find_packages(),
    py_modules=["scrapli_ipython"],
    python_requires='>=3.9',
)
