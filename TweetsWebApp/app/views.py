"""
Definition of views.
"""

from datetime import datetime,timedelta, date
from django.template import RequestContext
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim
from django.shortcuts import render
from django.http import HttpRequest
from folium import plugins
import json,re,branca,numpy
import folium
import tweepy
import sqlite3

def readConfigFile():
    with open('config.json') as data_file:
            config = json.load(data_file)
    pass
    api_key = config['api']
    consumer_key = config['consumer_key']
    consumer_secret = config['consumer_secret']
    access_token = config['access_token']
    access_token_secret = config['access_token_secret']
    tweets_to_download = config['tweets_to_download']
    result_type = config['result_type']
    language = config['language']
    return api_key,consumer_key,consumer_secret,access_token,access_token_secret,tweets_to_download,result_type,language
    pass

def getCountryList():
    countrylist=[]
    with open('CountriesList.txt') as data_file:
        for d in data_file:
            countrylist.append(d.replace('\n',''))
        pass
    pass
    return countrylist
    pass

def put_marker(cur_maps, data):
    geo_locator = Nominatim(user_agent="LearnPython")
    for (name, location) in data:
        if location:
            try:
                location = geo_locator.geocode(location)
            except GeocoderTimedOut:
                continue
            if location:
                html = ReturnPopup(name.split("::")[1], name.split("::")[2], name.split("::")[3], name.split("::")[4])
                iframe = branca.element.IFrame(html=html, width=300, height=200)
                popup = folium.Popup(iframe, parse_html=True)
                folium.Marker(
                    [location.latitude, location.longitude],
                    popup=popup,
                    icon=folium.Icon(color="red", icon="info-sign"),
                ).add_to(cur_maps)
                data = [location.latitude, location.longitude]
                col = 2
                stationArr = numpy.array([data[i:i + col] for i in range(0, len(data), col)])
                cur_maps.add_child(plugins.HeatMap(stationArr, radius=15))
            pass
        pass
    pass
    pass

def ReturnPopup(name, image, screen_name, description):
    html = """
    <!DOCTYPE html>
    <html>
    <div style="max-width:100%;margin-left:auto;margin-right:auto;">
    <img style="float:left;border-radius:10px;" src="{}">""".format(image)+"""
    <ul style="list-style-type:none;margin-left:1em;">
    <li><a href=https://twitter.com/{} target="_blank">{}</a></li>""".format(screen_name,name)+"""
    <li>@{}</li>""".format(screen_name)+"""
    </ul>
    <p style="text-align:center;">{}</p>""".format(description)+"""
    <br style="clear: both;">
    </div>
    </html>
    """
    return html
    pass

def gatherTweets(api,queries,place_id,language,result_type,tweets_to_download,timestamp):
    cur_maps = folium.Map(location=[0, 0], zoom_start=3)
    Query=[]
    Handlename=[]
    Hashtag=[]
    Usermention=[]
    Placename=[]
    TweetsDate=[]
    for query in queries: 
        all_tweets = tweepy.Cursor(api.search, q='{} place:{}'.format(query, place_id) + " -filter:retweets", lang=language, tweet_mode='extended', result_type=result_type).items(tweets_to_download)
        for tweet in all_tweets:
            location_data = []
            tweet_text = ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet.full_text).split())
            place = tweet.place.name if tweet.place else "Undefined place"
            tweet_hashtags = ''
            tweet_user_mentions = ''
            for tags in tweet.entities.get('hashtags'):
                tweet_hashtags = tweet_hashtags + tags['text'] + "#"
            for tags in tweet.entities.get('user_mentions'):
                tweet_user_mentions = tweet_user_mentions + tags['name'] + "#"
            twitter_handlename = tweet.user.name
            twitter_image = tweet.user.profile_image_url
            twitter_screen_image = tweet.user.screen_name
            date = tweet.created_at.strftime('%Y-%m-%d %H:%M')
            tuple_tweet_data = (timestamp.strftime('%Y-%m-%d %H:%M'),query, twitter_handlename, tweet_hashtags, tweet_user_mentions, tweet_text, place, date)
            map_tooltip = query + "::" + twitter_handlename + "::" + twitter_image + "::" + twitter_screen_image + "::" + tweet.full_text
            location_data.append((map_tooltip, place))
            Query.append(query)
            Handlename.append(twitter_handlename)
            Hashtag.append(tweet_hashtags)
            Usermention.append(tweet_user_mentions)
            Placename.append(place)
            TweetsDate.append(date)
            put_marker(cur_maps, location_data)
        pass
    pass
    cur_maps.save("app/static/app/content/maps.html")
    print('Save Successfully')
    return  list(zip(Query,Handlename,Hashtag,Usermention,Placename,TweetsDate)),cur_maps
    pass

def home(request):
    QueryList=[]
    if request.method == "POST":
        Country=request.POST['country'].lower()
        query=request.POST['query']
        queryOne=request.POST['queryone']
        queryTwo=request.POST['querytwo']
        if len(query)>0:
            QueryList.append(query)
        if len(queryOne)>0:
            QueryList.append(queryOne)
        if len(queryTwo)>0:
            QueryList.append(queryTwo)
        api_key,consumer_key,consumer_secret,access_token,access_token_secret,tweets_to_download,result_type,language=readConfigFile()
        timestamp = datetime.now()
        end_date = datetime(2021, 5, 8, 0, 0, 0)
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
        places = api.geo_search(query=Country, granularity="country")
        place_id = places[0].id
        TweetsData,MapPage=gatherTweets(api,QueryList,place_id,language,result_type,tweets_to_download,timestamp)
        return render(request,
                      'app/index.html',
                      {
                          'title':'Search Tweets',
                          'TweetsData':TweetsData,
                          'MapPage':MapPage
                          })
    else:
        return render(request,
                      'app/index.html',
                      {
                          'title':'Search Tweets',
                          'countrylist':getCountryList(),
                          })
    pass