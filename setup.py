import setuptools
from glob import glob

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='PubMed_Pipeline',
    version='0.1',
    author=['Nicolas Ford', 'Yalman Ahadi', 'Pao Lorthongpaisarn'],
    author_email=['zcabnjf@ucl.ac.uk', 'zcabyah@ucl.ac.uk', 'paul.lorthongpaisarn.18@ucl.ac.uk'],
    description='A PubMed Pipeline package',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/nicford/Pubmed-Pipeline',
    license='GPLv3',
    install_requires=['pyspark==2.4.4', 'joblib==1.2.0', 'nltk==3.4.5', 'numpy==1.18.1', 'pandas==1.0.1', 'pyarrow==0.11', 'requests==2.23.0',
    'scikit-learn==0.22.1', 'scispacy==0.2.4', 'spacy==2.2.3', 'unidecode==1.1.1', 'xgboost==0.90', 'pubmed_parser @ git+git://github.com/titipata/pubmed_parser.git@40d361a756a29cd943a54313c09b95044767eb97'],
    packages=setuptools.find_packages(),
    scripts=["pubmed_pipeline/setupPipeline.sh", "pubmed_pipeline/updatePipeline.sh"],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Intended Audience :: Developers',
        "Intended Audience :: Science/Research"
    ],
    python_requires='>=3',
)