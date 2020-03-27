from pyspark.sql.functions import col
from pyspark.sql.functions import pandas_udf
from pyspark.sql.types import StringType, IntegerType
import pandas as pd
import os
import joblib
import time
import numpy as np
from glob import glob
import pubmed_parser as pp
from pyspark.sql import Row
from pyspark.sql import Window
from pyspark.sql.functions import rank, max, sum, desc, lit
from sklearn import *
import pickle
import datetime
import subprocess
from subprocess import Popen, PIPE
from typing import List


class PubmedPipeline:
    """ Parent class of pipeline job types """
    
    def __init__(self, SPARK_SESSION, xmlPath, classifierPath, numSlices, lastRunPath):
        self.xmlPath = os.path.dirname(xmlPath) if os.path.isfile(xmlPath) else xmlPath
        self.classifierPath = classifierPath
        self.numSlices = numSlices
        self.lastRunPath = lastRunPath

        self.SPARK_SESSION = SPARK_SESSION

        self.classifier = joblib.load(self.classifierPath)

    

    def parseXMLToDF(self):
        """
        Read XML files and parse them into a dataframe.

        Returns:
            Dataframe containing parsed papers
        
        """
        medline_files_rdd = self.SPARK_SESSION.sparkContext.parallelize(glob(self.xmlPath + "/*.xml"), self.numSlices)

        parse_results_rdd = medline_files_rdd.\
        flatMap(lambda x: [Row(file_name=os.path.basename(x), **publication_dict) 
                        for publication_dict in pp.parse_medline_xml(x)])
        
        medline_df = parse_results_rdd.toDF()
        return medline_df
  
 

    def preProcessDataframe(self, dataframe):
        """
        Pre-process the dataframe to match classifier's expected input.
        This function can be customised as needed.
        
        Args:
            dataframe: dataframe to be pre-process
        
        Return:
            pre-processed dataframe
        
        """
        dataframe = dataframe.select("pmid", "pmc", "title", "medline_ta", "pubdate", "authors", "affiliations",
                                    "publication_types", "mesh_terms", "keywords", "chemical_list", "abstract", "country",
                                    "other_id", "doi", "nlm_unique_id", )

        dataframe = dataframe.withColumnRenamed("authors", "author").withColumnRenamed("affiliations", "affiliation")
        dataframe = dataframe.withColumn('pmid', dataframe['pmid'].cast(IntegerType()))
        return dataframe
  
  

    def propagate_udf(self, *args):
        """
        Apply udf propagate to predict_pandas_udf
        
        Args:
            *args: columns used for pandas udf prediction
        
        Return:
            dataframe with udf predictions applied
        """
        classifier = self.classifier
      
        @pandas_udf(returnType=StringType())
        def predict_pandas_udf(*features):
            X = pd.concat(features, axis=1)
            X.columns = ['abstract', 'title', 'medline_ta', 'keywords', 'publication_types', 'chemical_list', 'country',
                         'author', 'mesh_terms']
            y = classifier.predict(X)
            return pd.Series(y)
        
        return predict_pandas_udf(*args)
    
    
    def applyClassifier(self, dataframe):
        """
        Apply the classifier to the dataframe of papers

        Args:
            dataframe: dataframe to filter using classifier
            
        Return:
            dataframe only containing entries classified as relevant
        """
        dataframe = dataframe.withColumn( "prediction", self.propagate_udf(col("abstract"), col("title"), col("medline_ta"), col("keywords"), col("publication_types"),
                            col("chemical_list"), col("country"), col("author"), col("mesh_terms")))

        dataframe = dataframe.filter(dataframe.prediction == "Relevant")    # remove non-relevant rows i.e. non-relevant papers
        return dataframe
    

    def intersectPmidDataframes(self, currentDataframe, newAndUpdatedPapersDataframe):
        """
        Acquire papers which have been modified on pubmed

        Args:
            currentDataframe: main dataframe with all papers
            newAndUpdatedPapersDataframe: dataframe of new papers retrieved by the update job
        
        Return:
            intersection of current dataframe and new records dataframe on 'pmid' field
        """
        return currentDataframe.select('pmid').intersect(newAndUpdatedPapersDataframe.select('pmid'))


    def removeCommonPmidsFromDataframe(self, currentDF, commonPmids):
        """
        Remove modified papers from the current dataframe 

        Args:
            currentDF: current dataframe with all papers
            commonPmids: dataframe of common pmids 
        
        Return:
            dataframe with modified papers removed
        """
        left_join = currentDF.join(commonPmids, on=["pmid"], how='left_anti')
        return left_join


    def saveLastRunDate(self):
        """
        Saves the date on which the last job was run. Used for update job
        """
        today = datetime.date.today()
        pickle.dump(today, open(self.lastRunPath, "wb"))



class PubmedPipelineSetup(PubmedPipeline):
    """ Setup Pipeline class. Used for initial pipeline run to parse all xml paper metadata.
        XML data can be provided or can be downloaded using a PubMed search query. """
    def __init__(self, SPARK, XMLFilesOutputPath, pipelinePath, mainDataframeOutputPath, numslices, lastRunPicklePath):
        super().__init__(SPARK, XMLFilesOutputPath, pipelinePath, numslices, lastRunPicklePath)
        self.mainDataframeOutputPath = mainDataframeOutputPath

    
    def downloadXmlFromPubmed(self, searchQueries: List[str], apiKey, xmlOutputPath=None):
        """
        Download papers in XML format from pubmed

        Args:
            searchQueries: the term(s) to search for the papers on pubmed
            apiKey: API key from pubmed to allow increased rate of requests, to avoid HTTP 429 error
                    (see E-utilites website for how to get a key)
            xmlOutputPath: optional parameter, sets path to store downloaded xml papers
        """
        
        "+OR+".join(searchQueries)    # join the queries in suitable format for E-utilites url (see documentation for more info)

        # if no output path provided use object's xml path
        if xmlOutputPath is None:
            xmlOutputPath = self.xmlPath

        subprocess.call(["setupPipeline.sh", xmlOutputPath, searchQueries, str(apiKey)])



    def runPipeline(self):
        """
        Run the pipeline.
        Note: only run if you have xml data in the xmlPath. If you do not, you can use downloadXmlFromPubmed() to download xml data (see function)
        """
        dataframe = self.parseXMLToDF(self.xmlPath, self.numSlices)
        dataframe = self.preProcessDataframe(dataframe)                    
        dataframe = self.applyClassifier(dataframe)                    

        dataframe.write.parquet(self.mainDataframeOutputPath, mode="overwrite")     # write dataframe to specified directory in parquet format

        self.saveLastRunDate()      # store today as the last run date



class PubmedPipelineUpdate(PubmedPipeline):
    """ 
    Update Pipeline class. Parse new and updated papers. Add these to the main dataframe obtained from the setup job. 
    XML data can be provided or can be downloaded using a PubMed search query.
    """ 

    def __init__(self, SPARK, XMLFilesPath, pipelinePath, mainDataframePath, numslices, lastRunPicklePath, newAndUpdatedPapersDataframeOutputPath):
        super().__init__(SPARK, XMLFilesPath, pipelinePath, numslices, lastRunPicklePath)
        self.mainDataframe = self.SPARK_SESSION.read.parquet(mainDataframePath)
        self.mainDataframePath = mainDataframePath
        self.newAndUpdatedPapersDataframeOutputPath = newAndUpdatedPapersDataframeOutputPath

    
    def downloadXmlFromPubmed(self, searchQueries: List[str], apiKey, lastRunDatePath, xmlOutputPath=None):
        """
        Download papers in XML format from pubmed

        Args:
            searchQueries: the term(s) to search for the papers on pubmed
            apiKey: API key from pubmed to allow increased rate of requests, to avoid HTTP 429 error
                    (see E-utilites website for how to get a key)
            lastRunDatePath: path to the pickle file containing the last run date of a job
            xmlOutputPath: optional parameter, sets path to store downloaded xml papers
        """

        "+OR+".join(searchQueries)   # join the queries in suitable format for E-utilites url (see documentation for more info)

        # if no output path provided use object's xml path
        if xmlOutputPath is None:
            xmlOutputPath = self.xmlPath

        # get last time pipeline was run
        lastRunDate = pickle.load( open(lastRunDatePath, "rb") )

        today = datetime.date.today()

        # days since last run
        reldate = (today - lastRunDate).days + 1    # increment by 1 to avoid timezone issues. Note: papers already in the main dataframe will not be duplicated

        # PubMed only gets updated once daily, thus pipeline cannot be run more than once daily since there will be no new/changed papers.
        if reldate < 1:
            raise Exception("Days since last pipeline run is less than 1. Pipeline runs must occur at least one day apart")

        subprocess.call(["updatePipeline.sh", xmlOutputPath, searchQuery, str(apiKey), str(reldate)])

    
    def runPipeline(self):
        """
        Run the pipeline.
        Note: only run if you have xml data in the xmlPath. If you do not, you can use downloadXmlFromPubmed() to download xml data (see function)

        """
        # parse xml files into dataframe
        newPapersDataframe = self.parseXMLToDF(self.xmlPath, self.numSlices)

        # pre-process dataframe
        newPapersDataframe = self.preProcessDataframe(newPapersDataframe)

        # find and remove common papers from current dataframe
        commonPmids = self.intersectPmidDataframes(self.mainDataframe, newPapersDataframe)
        self.mainDataframe = self.removeCommonPmidsFromDataframe(self.mainDataframe, commonPmids)

        # filter papers
        newPapersDataframe = self.applyClassifier(newPapersDataframe)

        # adding new papers to main dataframe
        self.mainDataframe = self.mainDataframe.union(newPapersDataframe)
        
        # write updated main dataframe in parquet format
        self.mainDataframe.write.parquet(self.mainDataframePath, mode='overwrite')
        
        # write new and updated papers dataframe in parquet format
        newPapersDataframe.write.parquet(self.newAndUpdatedPapersDataframeOutputPath, mode='overwrite')

        # save today as last run date
        self.saveLastRunDate()








