from setuptools import setup, find_packages

with open('README.rst', encoding='UTF-8') as f:
    readme = f.read()

__version__ = "0.1.3"

setup(
    name='mqtt2measurinator',
    version=__version__,
    description='MTR receiver readings from MQTT server to measurinator api',
    author='topo',
    author_email='tvallas@iki.fi',
    url='https://github.com/tvallas/mqtt2measurinator',
    install_requires=['paho-mqtt'],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'mqtt2measurinator=mqtt2measurinator.cli:main',
        ]
    }
)