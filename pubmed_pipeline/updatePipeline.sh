#!/bin/bash

# create directories and files for logging 
mkdir ./logs
touch ./logs/downloadPapersJobLog.txt
chmod 777 ./logs/downloadPapersJobLog.txt

apiKey=$3	# need an api key for increased rate of requests
db="pubmed"
base="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
offset=10000			# to allow 10000 downloads at a time
export resultsDir=$1	# path to store the results, export this path to be accessible in all sub-processes
retmode="xml"	# download pubmed data as xml
retstart=0		# start index of papers on PubMed, gets increased by $offset in each efetch request (see Eutils efetch documentation for download limitation)	
retmax=100000	# can only store up to 100000 papers (see Eutils documentation)
query_key=3		# third query since we are running mdat and edat queries before the union of both queries

mDate="mdat"	# modification date
eDate="edat"	# entrez date (data of addition on pubmed)
reldate=$4 			# fourth argument passed to script from command line


# search 1: find modified papers
query=$2	# second argument passed to the script, search query terms
esearchUrl="${base}esearch.fcgi?db=$db&term=$query&reldate=$reldate&datetype=$mDate&usehistory=y"
data=$(curl -k --silent "$esearchUrl" | xmlstarlet fo -D)
webEnv=$(echo $data | xmlstarlet sel -t -v "//WebEnv")

# search 2: find new papers
esearchUrl="${base}esearch.fcgi?db=$db&term=$query&reldate=$reldate&datetype=$eDate&webenv=$webEnv&usehistory=y"
curl -k --silent -o "/dev/null" "$esearchUrl"

# search 3: union of search 1 and 2
query="%231+OR+%232"		# syntax to get the results of search 1 and 2 (see eutil documentatation)
esearchUrl="${base}esearch.fcgi?db=$db&term=$query&webenv=$webEnv&retmax=$retmax&usehistory=y"		# form the url to download papers from pubmed
data=$(curl -k --silent "$esearchUrl" | xmlstarlet fo -D)		# parse the result to XML


count=$(echo $data | xmlstarlet sel -t -v "/eSearchResult/Count")		# get the number of papers in the search

echo "Number of papers found: " $count		# display to user

numberOfResults=$(($count / 10000))			# split the results into batches of 10000


efetchUrl="${base}efetch.fcgi?db=$db&query_key=$query_key&webenv=$webEnv&api_key=$apiKey&retmode=$retmode"		# get result of both searches as a seperate search (query key = 3)

# paper download function
startPaperDownload () {
    echo "starting paper download"
	jobNumber=$2
	efetchUrl=$1
	wget -O "${resultsDir}/results${jobNumber}.xml" "${efetchUrl}&retstart=$(($jobNumber * 10000))"		# download and save each batch in a separate xml
}

export -f startPaperDownload

echo "starting all paper downloads"

# spawn download jobs, a max of 10 at a time, retried 3 times on failure, each spawn delayed by 0.2 seconds to avoid 429 HTTP error
parallel --retries 3 --delay 0.2 --joblog logs/downloadPapersJobLog.txt -j10 startPaperDownload ::: $efetchUrl ::: $(seq 0 ${numberOfResults})

# check for download failures in joblog file and keep retrying failed downloads until there are none
while [[ $? -ne 0 ]]
do
echo "re-trying failed jobs"
parallel -j8 --delay 0.2 --retry-failed --joblog logs/downloadPapersJobLog.txt
done

echo "XML paper metadata download done"

echo "script done"