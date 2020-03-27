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

If you do not have git installed, follow [these](https://git-scm.com/downloads) instruction to download it.

1. Clone this repository (or alternatively download it directly from the github page):
```bash
git clone https://github.com/nicford/Pubmed-Pipline.git
```

2. In your terminal, navigated into the cloned/downloaded folder.
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
### Setup Pipeline

The setup pipeline class allows you to setup a pipeline.
With this import statement, you will get access to the methods in the class
```python
from pubmed_pipeline import PubmedPipelineSetup
```

#### Example

An example to setup a pipeline and run it:

```python
from pubmed_pipeline import PubmedPipelineSetup

XMLFilesDirectory = ""     # path to save downloaded xml content from pubmed
numSlices = ""             # The numSlices denote the number of partitions the data would be parallelized to
searchQueries = [""]       # list of strings for queries to search pubmed for
apiKey = ""                # API key from pubmed to allow increased rate of requests, to avoid HTTP 429 error(see E-utilites website for how to get a key) 
lastRunDatePath = ""       # path to store a pickle object of the date when the setup is run (this is the same path to provide to the update job)
classifierPath = ""        # path to the classifier used to classify papers
dataframeOutputPath = ""   # path to store the final dataframe to in parquet form
sparkSession = ""          # your Spark session configuration

# The call below sets the pipeline up 
setupJob = PubmedPipelineSetup(sparkSession, XMLFilesDirectory, classifierPath, dataframeOutputPath, numSlices, lastRunDatePath)

# This downloads all the required papers from pubmed under the searchQueries
setupJob.downloadXmlFromPubmed(searchQueries, apiKey)

# This runs the pipeline and saves the classified 
setupJob.runPipeline()




```

### Update Pipeline