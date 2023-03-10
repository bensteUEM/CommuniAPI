from setuptools import setup, find_packages

with open("README.md", "r") as file:
    description = file.read()

setup(
    name='CommuniAPI',
    version='0.9',
    author='bensteUEM',
    author_email='benedict.stein@gmail.com',
    description='A python package to make use of Communi API',
    long_description=description,
    long_description_content_type="text/markdown",
    url='https://github.com/bensteUEM/CommuniAPI',
    license='CC-BY-SA',
    python_requires='>=3.8',
    packages=find_packages(),
    install_requires=[
        'ChurchToolsApi @ git+https://github.com/bensteUEM/ChurchToolsAPI.git@v1.1.1#egg=ChurchToolsAPI'
    ],
)