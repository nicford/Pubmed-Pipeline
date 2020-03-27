#!/bin/bash

# install required libraries

#install parallel
apt-get update
apt-get install parallel -y

#install curl
apt-get update
apt-get install curl -y

#install wget
apt-get update
apt-get install wget -y

#install xmlstarlet
apt-get update
apt-get install xmlstarlet -y


mkdir logs
touch /logs/downloadPapersJobLog.txt
chmod 777 /logs/downloadPapersJobLog.txt


db="pubmed"
query=$2
base="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
offset=10000
export resultsDir=$1
retmode="xml"

esearchUrl="${base}esearch.fcgi?db=$db&term=$query&usehistory=y"
apiKey=$3
retstart=0
data=$(curl -k --silent "$esearchUrl" | xmlstarlet fo -D)

key=$(echo $data | xmlstarlet sel -t -v "//QueryKey")
webEnv=$(echo $data | xmlstarlet sel -t -v "//WebEnv")
count=$(echo $data | xmlstarlet sel -t -v "/eSearchResult/Count")

numberOfResults=$(($count / 10000))



efetchUrl="${base}efetch.fcgi?db=$db&query_key=$key&WebEnv=$webEnv&api_key=$apiKey&retmode=$retmode"

startPaperDownload () {
	pwd
	jobNumber=$2
	efetchUrl=$1
	wget -O "${resultsDir}/results${jobNumber}.xml" "${efetchUrl}&retstart=$(($jobNumber * 10000))"
}

export -f startPaperDownload

parallel --retries 3 --delay 0.2 --joblog logs/downloadPapersJobLog.txt -j10 startPaperDownload ::: $efetchUrl ::: $(seq 0 ${numberOfResults})
echo 11111111111
# check for download failures in joblog file and keep retrying failed downloads until there are none
while [[ $? -ne 0 ]]
do
echo "setup: in while loop"
parallel -j8 --delay 0.2 --retry-failed --joblog logs/downloadPapersJobLog.txt
done

echo "XML download done"

echo "script done"