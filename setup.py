from setuptools import setup, find_packages

setup(
    name="scrapli_ipython",
    version="0.0.6",
    install_requires=[
        "scrapli[ssh2]",
        "ntc_templates",
        "jinja2",
        "ipython",
    ],
    author="haccht",
    url="https://github.com/haccht/scrapli_ipython",
    description="scrapli extention for ipython",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires='>=3.8',
)
