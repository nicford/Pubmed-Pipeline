#!/bin/bash

# E-utilities documentation: https://www.ncbi.nlm.nih.gov/books/NBK25501/

# make logs directory and file
mkdir ./logs
touch ./logs/downloadPapersJobLog.txt
chmod 777 ./logs/downloadPapersJobLog.txt


base="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
db="pubmed"
query=$2 				# pass the query terms as argument to the script
offset=10000 			# to allow 10000 downloads at a time  
export resultsDir=$1 	# path to store the results, export this path to be accessible in all sub-processes
retmode="xml" 			# download pubmed data as xml

esearchUrl="${base}esearch.fcgi?db=$db&term=$query&usehistory=y" 	# create the E-Eutils API url
apiKey=$3 		# need an api key for increased rate of requests
retstart=0		# start index of papers on PubMed, gets increased by $offset in each efetch request (see Eutils efetch documentation for download limitation)
data=$(curl -k --silent "$esearchUrl" | xmlstarlet fo -D)			# parse result as xml

key=$(echo $data | xmlstarlet sel -t -v "//QueryKey")				# store query key
webEnv=$(echo $data | xmlstarlet sel -t -v "//WebEnv")				# store web env
count=$(echo $data | xmlstarlet sel -t -v "/eSearchResult/Count")	# store search count

numberOfResults=$(($count / 10000))		# calculate how many download jobs are needed


# create the url to download the papers
efetchUrl="${base}efetch.fcgi?db=$db&query_key=$key&WebEnv=$webEnv&api_key=$apiKey&retmode=$retmode"

# paper download function to execute multiple times to download batches of 10000
startPaperDownload () {
	jobNumber=$2
	efetchUrl=$1	
	wget -O "${resultsDir}/results${jobNumber}.xml" "${efetchUrl}&retstart=$(($jobNumber * 10000))"		# download and save each batch in a separate xml
}

export -f startPaperDownload	# make function available to all sub-processes

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