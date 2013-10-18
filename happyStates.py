import csv
import sys
import json
from xml.dom import minidom
import re


def point_inside_state(x, y, bounds):
    """
    Determines if a point is inside the boundaries of a given state. The state
    is a list of (x, y) pairs marking its boundaries. Based on point in polygon
    routine taken from http://www.ariel.com.au/a/python-point-int-poly.html.

    Args:
        x: the latitude of a point.
        y: the longitude of a point.
        bounds: a list of (x, y) pairs marking boundaries of state in same units
            as x and y.

    Returns:
        A boolean indicating if the point is in the given boundaries. 
    """
    n = len(bounds)
    inside = False

    p1x, p1y = bounds[0]
    for i in range(n+1):
        p2x, p2y = bounds[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y-p1y) * (p2x-p1x) / (p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def state_of_point(state_bounds, lat, lon):
    """
    Finds the US state for a given location.

    Args:
        state_bounds: a dictionary mapping state names to the (x, y) pairs of
            its boundaries.
        lat: the latitude of location.
        lon: the longitude of location.
    
    Returns:
        Name of the state as a string. If the location can't be found in any of
        the state boundaries the string 'No state found' is returned instead.
    """
    for state in state_bounds.keys():
        inside = point_inside_state(lat, lon, state_bounds[state])
        if inside:
            return state 

    return 'No state found'


def process_tweet(tweet):
    """
    Processes text of tweet to get a list of words without white spaces,
    punctuation marks, urls, and usernames.

    Args:
        tweet: the text of a tweet to be processed.
    
    Returns:
        A list of words in tweet. 
    """
    # Convert to lower case.
    tweet = tweet.lower()
    # Convert www.* or https?://* to URL.
    tweet = re.sub('((www\.[\s]+)|(https?://[^\s]+))', 'URL', tweet)
    # Convert @username to USER.
    tweet = re.sub('@[^\s]+', 'USER', tweet)
    # Remove additional white spaces.
    tweet = re.sub('[\s]+', ' ', tweet)
    # Replace #word with word.
    tweet = re.sub(r'#([^\s]+)', r'\1', tweet)
    # Trim.
    tweet = tweet.strip('\'"')

    # Get words.
    w_list = re.findall(r"[\w']+", tweet)
    # Replace two or more repetitions of characters.
    pattern = re.compile(r"(.)\1{1,}", re.DOTALL)
    w_list = [pattern.sub(r"\1\1", w) for w in w_list]
    # Strip words,
    w_list = [w.strip('\'"?,.') for w in w_list]
    #  of apostrophe.
    w_list = [w.split('\'')[0] for w in w_list]

    # Remove empty strings.
    w_list = filter(None, w_list)
    # Remove words starting with numbers.
    w_list = [w for w in w_list if not w[0].isdigit()]

    return w_list 

    
def get_sentiment(tweet, sent_dict):
    """
    Gets sentiment of tweet.
   
    Args:
        tweet: a list of words.
        sent_dict: a dictionary mapping words with sentiment scores.

    Returns:
        The sum of the sentiment scores for each word.
    """
    return sum([sent_dict[word] for word in tweet 
                if word in sent_dict])


def create_state_bound_dict(filename):
    """
    Create a dictionary that maps the names of a US state to its boundaries.
    
    Args:
        filename: name of the file with polygon data for the US states.

    Returns:
        A dictionary that maps the names of a US state to a list of (x, y) pairs
        that describe the polygon shape of its boundaries in longitude and 
        latitude.
    """
    state_bounds = {}
    
    xmldoc = minidom.parse(filename)
    state_list = xmldoc.getElementsByTagName('state')
    
    # Fill dictionary with state names and boundaries.
    for state in state_list:
        state_name = state.attributes['name'].value
        point_list = state.getElementsByTagName("point")
        bounds = []
        for point in point_list:
            lat = point.attributes['lat'].value 
            lon = point.attributes['lng'].value 
            bounds = bounds + [(float(lat), float(lon))]
        
        state_bounds[state_name] = bounds

    return state_bounds


def create_city_dict(filename):
    """
    Create a dictionary that maps the name of a city to its location

    Args:
        filename: name of the file with the city data
    
    Returns:
        A dictionary mapping the name of a city to a pair of coordinates
        specifying the longitude and latitude of the city.
    """
    city_dict = {}
    
    fields = ["geonameid", "name", "asciiname", "alternatenames", "latitude",
              "longitude", "feature_class", "feature_code", "country_code",
              "cc2", "admin1_code", "admin2_code", "admin3_code", "admin4_code",
              "population", "elevation", "dem", "timezone", "modification_date"]
     
    cities_file = open(filename, 'rb')
    
    for line in cities_file:
       # Fill dictionary with cities and coordinates.
       # If a city already exists in dictionary take the city with the higher
       #     poulation.
       field_list = line.split('\t')
    
       city = field_list[fields.index('asciiname')]
       lat = field_list[fields.index('latitude')]
       lon = field_list[fields.index('longitude')] 
    
       city_dict[city] = (float(lon), float(lat))

    cities_file.close() 
    return city_dict


def create_sent_dict(filename):
    """
    Create a sentiment dictionary
  
    Args:
        filemame: name of the file with words and sentiment score
 
    Returns:
        A dictionary mapping a word to a sentiment score
    """
    scores = {}
    
    sent_file = open(filename)
    for line in sent_file:
        # The file is tab-delimited.
        term, score  = line.split("\t")  
        # Convert the score to an integer.
        scores[term] = int(score)  
   
    return scores
 

def main():
    """
    This program performs a sentiment analysis of twitter tweets in the US.
    There are several steps involved.
        1. Select tweets of interest. They have to be in english and from the
            US.
        2. Get coordinates for tweets. 
        3. Get sentiment of new words based on list of words with known
           sentiment. Compile a dictionary that maps word to their sentiment.
        4. Apply dictionary to words in the tweets.
    The most time consuming part is the determination of the location when only
    a city name is available. This option can be enabled by setting the
    city_flag to 1. The locations derived in this way are less accurate and
    should probably only be used when not many other locations are available. 

    Usage: 
        > python happyStates.py twitter_input_file output_file city_flag
    Example:
        > python happyStates.py twitter_output.txt output.txt 
        > python happyStates.py twitter_output.txt output.txt 1 
    """
    tweet_file = open(sys.argv[1])
    out_file = open(sys.argv[2], 'w+')
   
    city_arg = 0
    if len(sys.argv) == 4:
        if sys.argv[3] == '1':
            city_arg = 1
    
    # Get polygons for state boundaries from xml file taken from
    #     http://econym.org.uk/gmap/states.xml.
    state_bounds = create_state_bound_dict("input_files/states.xml")
   
    # Optional: Get dictionary of city names and locations
    if city_arg == 1:
        city_dict = create_city_dict("input_files/US_cities.txt") 
    
    # Get tweets
    tweets = tweet_file.readlines()
    
    # Get list of stopwords.
    # Taken from https://github.com/ravikiranj. Added USER and RT. 
    stop_words = []
    
    stop_file = open('input_files/stopwords.txt', 'rb')
    lines = stop_file.readlines()
    stop_words = [w.strip() for w in lines]
    
    stop_file.close()
    
    # Select tweets that have english text and are sent from the US. Get their
    #     coordinates and the state they were sent from
    tweet_dict = {}
    for t in tweets:
        tweet_temp = json.loads(t)
        
        # Does the tweet have a text?
        if 'text' in tweet_temp:
            coord = False 
            city = ""
            ctry = ""
            coord_place = 0
            coord_coord = 0
    
            user = tweet_temp['user']
    
            # Is it in english? 
            if user['lang'] == 'en':
    
                # Is a place specified?
                if tweet_temp['place']:
                    place = tweet_temp['place']
    
                    # Is it in the US?
                    if place['country'] == 'United States':
                        ctry = place['country']
                        # Get coordinates of place
                        coord_place = place['bounding_box']['coordinates'][0][0]
    
                # Are the coordinates specified?
                if tweet_temp['coordinates']:
                    # Get coordinates
                    coord_coord = tweet_temp['coordinates']['coordinates']
    
                # Is there a user location specified?
                if user['location']:
                    # Get name of location/city
                    city = user['location'].split(',')[0]
    
            # Get coordinates for the tweet and determine state it was sent from
            if coord_coord:
                coord = coord_coord
                state = state_of_point(state_bounds, coord[1], coord[0])
            elif coord_place:
                coord = coord_place
                state = state_of_point(state_bounds, coord[1], coord[0])
            elif city_arg == 1: 
                if city:
                    if city == 'New York':
                        city = 'New York City'
                    if city in city_dict:
                        coord = city_dict[city]
                        state = state_of_point(state_bounds, coord[1], coord[0])
            
            if coord:
                if state != 'No state found': 
                    text_list = process_tweet(tweet_temp['text'])
                    # Remove word from stop_words
                    text_list = [w for w in text_list if w not in stop_words]
    
                    tweet_dict[tweet_temp["id"]] = [state, coord[1], coord[0],
                                                    text_list, tweet_temp["text"]]
    
    
    # Create sentiment dictionary
    # Use wordlist/affective lexicon by Finn Årup Nielsen: http://neuro.imm.dtu.dk/wiki/AFINN
    scores = create_sent_dict("input_files/AFINN-111.txt")

    # Initialize term sentiment dictionary for new words
    # The structure is: {word: [overall sentiment, number of occurence]}
    term_sents = {}
    
    for value in tweet_dict.values():
        text_list = value[3]
    
        score = 0
        word_count = 0
        # Get overall score word each tweet and 
        #   number of used words to determined score
        for word in text_list:
            if word in scores:
                score = score + scores[word]
                word_count = word_count + 1
        
        if score != 0:
            # Get the new sentiment for each word that is not in the sent_file
            if len(text_list) == word_count:
                word_sent = score
            else:
                word_sent = score / float(len(text_list) - word_count)
        
            for word in text_list:
                # Fill the dictionary with the cummulative sentiment and 
                #   number of occurence of each word
                if word not in scores:
                    if word in term_sents:
                        term_sents[word] = [a+b for a, b in 
                                            zip(term_sents[word], [word_sent, 1])]
                    else:
                        term_sents[word] = [word_sent, 1]
    
    # Make new extended dictionary with new words and sentiments
    scores_update = {}
    
    for key, value in term_sents.items():
        # Get score for each new word: overall sentiment / number of occurence
        scores_update[key] = value[0] / value[1]
    #for key, value in scores_update.items():
    #    print key, ',', value

    # Update with initial list from sent_file
    scores_update.update(scores)
    
    # Get sentiment score for each tweet and append to tweet_dictionary
    output = csv.writer(out_file, delimiter=',')
    header = ['id', 'state', 'lat', 'lon', 'words', 'text', 'score']
    output.writerow(header)

    for key, value in tweet_dict.items():
        tweet_dict[key] = value + [get_sentiment(value[3], scores_update)] 
        output.writerow([key] + 
                        tweet_dict[key][0:4] + 
                        [tweet_dict[key][4].encode("utf-8")] + 
                        [tweet_dict[key][-1]])
    out_file.close()

if __name__ == '__main__':
    main()
