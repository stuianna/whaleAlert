import setuptools
exec(open('whalealert/_version.py').read())

with open("README.md","r") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "whale-alert",
    scripts = ['bin/whaleAlertLogger'],
    version = '0.0.1',
    author ="stuianna",
    author_email = "stuian@protonmail.com",
    description = "Cryptocurrency Whale Alert API Logger",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url = "https://github.com/stuianna/whaleAlert",
    packages = setuptools.find_packages(),
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
        ],
    python_requires = '>=3.6',
    install_requires=[
        'requests',
        'colorama',
        'config-checker',
        'db-ops',
        'requests',
        'pandas',
        'numpy',
        'appdirs',
        'python-dateutil',
        'urllib3'
    ],
    )
