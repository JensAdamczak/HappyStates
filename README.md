###README for the HappyStates Twitter sentiment anlysis

This repository contains a Twitter sentiment analysis. The main program that
does the analysis is *happyStates.py*. It requires and input file
*twitter_output_small.txt* with data from the Twitter API. The program reads the
file and determines the language and location of each tweet, and finds the name
of the US state it was sent from. It then reads in a file with sentiment scores
for words (see input_file directory) and determines sentiments for new words
found in the tweets. Based on the list of words a happiness score for each tweet
is determined.

To run the program an input file with twitter data is needed. The program takes
a flag that specifies if locations for tweets for which only a city name is
available should be derived (flag set to 1). This takes longer and the derived
locations are less accurate. To start it from the command line type:

```
python happyStates.py inputfile outputfile
echo "or with city_flag set to 1"
python happyStates.py inputfile outputfile 1
```

It was tested with Python 2.7.5 on Mac OS X 10.6.8.
