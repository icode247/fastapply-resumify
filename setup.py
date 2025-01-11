# setup.py
from setuptools import setup, find_packages
import subprocess
import sys

def download_spacy_model():
    print("Downloading spaCy model...")
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])

setup(
    name="resumify-api",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'flask==2.0.1',
        'scikit-learn==1.3.2',
        'spacy==3.7.2',
        'PyPDF2==3.0.1',
        'flask-limiter==3.5.0',
        'requests==2.31.0',
        'pandas==2.1.3',
        'mangum==0.17.0',
        'flask-cors==4.0.0',
        'Werkzeug==2.0.3',
        'urllib3<2.0.0',
        'gunicorn==20.1.0'
    ],
    cmdclass={
        'download_spacy': download_spacy_model,
    },
)