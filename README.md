# Pubmed Pipeline Python Library

## Requirements

[python3+](https://www.python.org/downloads/)

[pip](https://pypi.org/project/pip/)



[git](https://git-scm.com)

[parallel](https://www.gnu.org/software/parallel/)

[xmlstarlet](http://xmlstar.sourceforge.net)

[wget](https://www.gnu.org/software/wget/)

[curl](https://curl.haxx.se)


## Installation

Make sure you have python and pip installed.

If you do not have git installed, follow [these](https://git-scm.com/downloads) instruction to install it.

1. Clone this repository (or alternatively download it directly from the github page):
```bash
git clone https://github.com/nicford/Pubmed-Pipline.git
```

2. In your terminal, navigate into the cloned/downloaded folder.
   Run the following command to install the Pubmed Pipeline library:

```bash
pip install pubmed_pipeline
```


3. Install other required dependencies:

    Follow [these](https://www.gnu.org/software/parallel/) instructions to install parallel.

    Follow [these](http://xmlstar.sourceforge.net/download.php) instructions to install xmlstarlet.

    Follow [these](https://www.gnu.org/software/wget/) instructions to install wget.

    Follow [these](https://curl.haxx.se/download.html) instructions to install curl.



## Usage

## Requirements

### 1. Spark Session

To create a pipeline object, you need to pass a spark session. Thus, you must configure your spark session beforehand. If you are unfamiliar with spark sessions, you can get started [here](https://spark.apache.org/docs/2.1.0/api/python/pyspark.sql.html?highlight=sparksession). Note: if you are using Databricks, a spark session is automatically created called "spark".

### 2. API KEY (optional, for XML downloads)

If you do not have your own PubMed XML data and you wish to download XML paper data from PubMed, you need a PubMed API key. This API key be obtained by doing the following:

"Users can obtain an API key now from the Settings page of their NCBI account. To create an account, visit http://www.ncbi.nlm.nih.gov/account/." 


### Setup Pipeline

The setup pipeline class allows you to setup a pipeline.

See below how to use this setup pipeline.

```python
from pubmed_pipeline import PubmedPipelineSetup

XMLFilesDirectory = ""     # path to save downloaded XML content from pubmed or path to XML data if you already have some
numSlices = ""             # The numSlices denote the number of partitions the data would be parallelized to
searchQueries = [""]       # list of strings for queries to search pubmed for
apiKey = ""                # API key from pubmed to allow increased rate of requests, to avoid HTTP 429 error(see E-utilites website for how to get a key) 
lastRunDatePath = ""       # path to store a pickle object of the date when the setup is run (this is the same path to provide to the update job)
classifierPath = ""        # path to the classifier used to classify papers
dataframeOutputPath = ""   # path to store the final dataframe to in parquet form

# your Spark session configuration
sparkSession = SparkSession.builder \    
                       .master("local") \
                       .appName("") \
                       .config("spark.some.config.option", "some-value") \
                       .getOrCreate()

# create the setup pipeline 
setupJob = PubmedPipelineSetup(sparkSession, XMLFilesDirectory, classifierPath, dataframeOutputPath, numSlices, lastRunDatePath)

# This downloads all the required papers from PubMed under the searchQueries
setupJob.downloadXmlFromPubmed(searchQueries, apiKey)

# This runs the pipeline and saves the classified papers in dataframeOutputPath
setupJob.runPipeline()
```

### Update Pipeline

The update pipeline class allows you to update your database of papers since the setup pipeline was run, or since the last update was run.

See below how to use this update pipeline.

```python
from pubmed_pipeline import PubmedPipelineUpdate

XMLFilesDirectory = ""          # path to save downloaded xml content from pubmed
numSlices = ""                  # The numSlices denote the number of partitions the data would be parallelized to
searchQueries = [""]            # list of strings for queries to search pubmed for
apiKey = ""                     # API key from pubmed to allow increased rate of requests, to avoid HTTP 429 error(see E-utilites website for how to get a key) 
lastRunDatePath = ""            # path containing a pickle object of the last run date (running setup job creates one)
classifierPath = ""             # path to the classifier used to classify papers
dataframeOutputPath = ""        # path to store the final dataframe to in parquet form
newAndUpdatedPapersPath = ""    # path to store the dataframe containing the new and updated papers

# your Spark session configuration
sparkSession = SparkSession.builder \
                       .master("local") \
                       .appName("") \
                       .config("spark.some.config.option", "some-value") \
                       .getOrCreate()

# create the update pipeline 
updateJob = PubmedPipelineUpdate(sparkSession, XMLFilesDirectory, classifierPath, dataframeOutputPath, numSlices, lastRunDatePath, newAndUpdatedPapersPath)

# This downloads all the required papers from pubmed under the searchQueries
updateJob.downloadXmlFromPubmed(searchQueries, apiKey)

# This runs the pipeline and saves the new and updated classified papers in newAndUpdatedPapersPath
# The pipeline also handles the logic to add new papers and remove any papers from the main dataframe which are no longer relevant
updateJob.runPipeline()
```


## Customisation of library

If you wish to customise the library to meet your own needs, please fork the repository and do the following:

To customise the pipeline processes, change/add the functions in pubmedPipeline.py
To customise the downloading of XML metadata, change setupPipeline.sh and updatePipeline.sh


## Core Developers

[Nicolas Ford](https://github.com/nicford)

[Yalman Ahadi](https://github.com/yalmanahadi)

[Paul Lorthongpaisarn](https://github.com/pongpol21)


## Dependencies

We would like to acknowledge the following projects:

[parallel](https://www.gnu.org/software/parallel/)

[xmlstarlet](http://xmlstar.sourceforge.net/download.php)

[wget](https://www.gnu.org/software/wget/)

[curl](https://curl.haxx.se/download.html)



and the following libraries:

[pyspark](https://spark.apache.org/docs/latest/api/python/index.html)

[joblib](https://joblib.readthedocs.io/en/latest/)

[nltk](https://www.nltk.org)

[numpy](https://numpy.org)

[pandas](https://pandas.pydata.org)

[pyarrow](https://pypi.org/project/pyarrow/)

[requests](https://requests.readthedocs.io/en/master/)

[scikit-learn](https://scikit-learn.org/stable/)

[scispacy](https://allenai.github.io/scispacy/)

[spacy](https://spacy.io)

[unidecode](https://pypi.org/project/Unidecode/)

[xgboost](https://xgboost.readthedocs.io/en/latest/#)

[pubmed_parser](https://github.com/titipata/pubmed_parser)