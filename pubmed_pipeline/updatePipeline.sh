#!/bin/bash

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

echo 1

mkdir logs
touch /logs/downloadPapersJobLog.txt
chmod 777 /logs/downloadPapersJobLog.txt

apiKey=$3
db="pubmed"
base="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
offset=10000
export resultsDir=$1
retmode="xml"
retstart=0
query_key=3
retmax=100000

mDate="mdat"
eDate="edat"
reldate=$4 			# fourth argument passed to script from command line

echo 2

# search 1: modified papers
query=$2
esearchUrl="${base}esearch.fcgi?db=$db&term=$query&reldate=$reldate&datetype=$mDate&usehistory=y"
data=$(curl -k --silent "$esearchUrl" | xmlstarlet fo -D)
webEnv=$(echo $data | xmlstarlet sel -t -v "//WebEnv")

echo 3

# search 2: new papers
esearchUrl="${base}esearch.fcgi?db=$db&term=$query&reldate=$reldate&datetype=$eDate&webenv=$webEnv&usehistory=y"
data=$(curl -k --silent "$esearchUrl" | xmlstarlet fo -D)

echo 4

# search 3: union of search 1 and 2
query="%231+OR+%232"
esearchUrl="${base}esearch.fcgi?db=$db&term=$query&webenv=$webEnv&retmax=$retmax&usehistory=y"
data=$(curl -k --silent "$esearchUrl" | xmlstarlet fo -D)

echo 5

printf "%s" "$data" > "newUID.xml"

count=$(echo $data | xmlstarlet sel -t -v "/eSearchResult/Count")

numberOfResults=$(($count / 10000))

echo "Key: $key"
echo "WebEnv: $webEnv"
echo "Count: $count"
echo "resultsdir: $resultsDir"

efetchUrl="${base}efetch.fcgi?db=$db&query_key=$query_key&webenv=$webEnv&api_key=$apiKey&retmode=$retmode"

startPaperDownload () {
    echo "starting paper download"
	jobNumber=$2
	efetchUrl=$1
	wget -O "${resultsDir}/results${jobNumber}.xml" "${efetchUrl}&retstart=$(($jobNumber * 10000))"
}

export -f startPaperDownload

echo "starting all paper downloads"

parallel --retries 3 --delay 0.2 --joblog logs/downloadPapersJobLog.txt -j10 startPaperDownload ::: $efetchUrl ::: $(seq 0 ${numberOfResults})

echo "starting failed jobs"
# check for download failures in joblog file and keep retrying failed downloads until there are none
while [[ $? -ne 0 ]]
do
echo "in loop"
parallel -j8 --delay 0.2 --retry-failed --joblog logs/downloadPapersJobLog.txt
done


echo "script done"
