# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from colorama import Fore
from spotify_ripper.utils import *
import os
import time
import spotify
import requests
import csv
import re

import sys

import spotipy.util as util
import spotipy.client
import spotipy.oauth2 as oauth2

#check instructions from https://github.com/stephanlensky/spotify-ripper
redirect_uri = 'http://retropie'
client_id = '66b8ec5322ef4eab85d6f8dc91666bb9' # You need to place your client_id here before install
client_secret = '527ebda9e4a940048a22ea2846fd677f' # You need to place your client_secret here before install
scope = 'playlist-modify-public playlist-modify-private playlist-read-collaborative'

#client_id = os.environ["SPOTIPY_CLIENT_ID"]
#client_secret = os.environ["SPOTIPY_CLIENT_SECRET"]
#redirect_uri = os.environ["SPOTIPY_REDIRECT_URI"]

token = None
spotInstance = None
spotAuthUsername = None


def init_spotipy(username):
    global spotAuthUsername
    spotAuthUsername = username

    global token
    token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)

    global spotInstance
    spotInstance = spotipy.Spotify(auth=token)
    spotInstance.trace = False


def refresh_access_token():
    global token
    token = util.prompt_for_user_token(spotAuthUsername, scope, client_id, client_secret, redirect_uri)

    global spotInstance
    spotInstance = spotipy.Spotify(auth=token)
    spotInstance.trace = False


def remove_all_from_playlist(username, playlistURI):
    refresh_access_token()
    tracks = get_playlist_tracks(username, playlistURI)

    track_ids = []
    for i, item in enumerate(tracks['items']):
        track = item['track']
        tid = track['id']
        track_ids.append(tid)
    results = spotInstance.user_playlist_remove_all_occurrences_of_tracks(username, rPlaylistID, track_ids)


def get_playlist_tracks(username, playlistURI):
    refresh_access_token()
    global rPlaylistID
    p1, p2, p3, p4, rPlaylistID = playlistURI.split(':', 5)

    # the spotify api limits the number of tracks which can be retrieved from a playlist in a single request
    # make multiple requests to collect all playlist tracks before continuing
    print('Collecting tracks from playlist')
    tracks = spotInstance.user_playlist(username, rPlaylistID, fields='tracks,next')['tracks']
    sys.stdout.flush()
    #print('Collecting tracks from playlist ({}/{})'.format(len(tracks['items']), tracks['total']))
    paged_tracks = tracks
    while paged_tracks['next']:
        paged_tracks = spotInstance.next(paged_tracks)
        tracks['items'].extend(paged_tracks['items'])
        sys.stdout.flush()
        #print('Collecting tracks from playlist ({}/{})'.format(len(tracks['items']), tracks['total']))
    print('Collecting tracks from playlist ({}/{})'.format(len(tracks['items']), tracks['total']))

    return tracks


def get_track_json(track_uri):
    refresh_access_token()
    return spotInstance.track(track_uri)


# excludes 'appears on' albums for artist
def get_albums_with_filter(args, uri):
    refresh_access_token()
        
    # extract artist id from uri
    uri_tokens = uri.split(':')
    if len(uri_tokens) != 3:
        return []
    artistID = uri_tokens[2]

    album_type = args.artist_album_type[0] \
        if args.artist_album_type is not None else ""

    market = args.artist_album_market[0] \
        if args.artist_album_market is not None else ""

    # it is possible we won't get all the albums on the first request
    offset = 0
    album_uris = []
    album_titles = []
    total = None

    
    while total is None or offset < total:
        try:
            # rate limit if not first request
            if total is None:
                time.sleep(1.0)
            albums = spotInstance.artist_albums(artistID, album_type, None, 50, offset)
            if albums is None:
                break
            # extract album URIs
            album_uris += [album['uri'] for album in albums['items']]
            album_titles += [album['name'] for album in albums['items']]
            offset = len(album_uris)
            if total is None:
                total = albums['total']
        except KeyError as e:
            break
    print(str(len(album_uris)) + " albums found")
    #WebAPI.cache_result(WebAPI, uri, album_uris)
    return album_uris
        
    # check for cached result
    #cached_result = self.get_cached_result(uri)
    #if cached_result is not None:
    #    return cached_result

""" using spotipy for cover download, not working yet
def get_cover_url(album_uri):

    print('Trying to collect cover from Album URI')
        
    # extract album id from uri
    uri_tokens = str(album_uri).split(':')
    if len(uri_tokens) != 3:
        return None
    album_id = uri_tokens[2]
    print(str(album_id))
    album = spotInstance.album(album_id);
    print(str(album))
    imgPath = album.images[0].url
    return imgPath
"""
    
class WebAPI(object):

    def __init__(self, args, ripper):
        self.args = args
        self.ripper = ripper
        self.cache = {}

    def cache_result(self, uri, result):
        self.cache[uri] = result

    def get_cached_result(self, uri):
        return self.cache.get(uri)

    def request_json(self, url, msg):
        res = self.request_url(url, msg)
        return res.json() if res is not None else res

    def request_url(self, url, msg):
        print(Fore.GREEN + "Attempting to retrieve " + msg +
              " from Spotify's Web API" + Fore.RESET)
        print(Fore.CYAN + url + Fore.RESET)
        res = requests.get(url)
        if res.status_code == 200:
            return res
        else:
            print(Fore.YELLOW + "URL returned non-200 HTTP code: " +
                  str(res.status_code) + Fore.RESET)
        return None

    def api_url(self, url_path):
        return 'https://api.spotify.com/v1/' + url_path

    def charts_url(self, url_path):
        return 'https://spotifycharts.com/' + url_path

    def get_artists_on_album(self, uri):
        def get_album_json(album_id):
            url = self.api_url('albums/' + album_id)
            return self.request_json(url, "album")

        # check for cached result
        cached_result = self.get_cached_result(uri)
        if cached_result is not None:
            return cached_result

        # extract album id from uri
        uri_tokens = uri.split(':')
        if len(uri_tokens) != 3:
            return None

        album = get_album_json(uri_tokens[2])
        if album is None:
            return None

        result = [artist['name'] for artist in album['artists']]
        self.cache_result(uri, result)
        return result

        
    # genre_type can be "artist" or "album"
    def get_genres(self, genre_type, track):
        def get_genre_json(spotify_id):
            url = self.api_url(genre_type + 's/' + spotify_id)
            return self.request_json(url, "genres")

        # extract album id from uri
        item = track.artists[0] if genre_type == "artist" else track.album
        uri = item.link.uri

        # check for cached result
        cached_result = self.get_cached_result(uri)
        if cached_result is not None:
            return cached_result

        uri_tokens = uri.split(':')
        if len(uri_tokens) != 3:
            return None

        json_obj = get_genre_json(uri_tokens[2])
        if json_obj is None:
            return None

        result = json_obj["genres"]
        self.cache_result(uri, result)
        return result

    # doesn't seem to be officially supported by Spotify
    def get_charts(self, uri):
        def get_chart_tracks(metrics, region, time_window, from_date):
            url = self.charts_url(metrics + "/" + region + "/" + time_window +
                "/" + from_date + "/download")

            res = self.request_url(url, region + " " + metrics + " charts")
            if res is not None:
                csv_items = [enc_str(r) for r in res.text.split("\n")]
                reader = csv.DictReader(csv_items)
                return ["spotify:track:" + row["URL"].split("/")[-1]
                            for row in reader]
            else:
                return []

        # check for cached result
        cached_result = self.get_cached_result(uri)
        if cached_result is not None:
            return cached_result

        # spotify:charts:metric:region:time_window:date
        uri_tokens = uri.split(':')
        if len(uri_tokens) != 6:
            return None

        # some sanity checking
        valid_metrics = {"regional", "viral"}
        valid_regions = {"us", "gb", "ad", "ar", "at", "au", "be", "bg", "bo",
                         "br", "ca", "ch", "cl", "co", "cr", "cy", "cz", "de",
                         "dk", "do", "ec", "ee", "es", "fi", "fr", "gr", "gt",
                         "hk", "hn", "hu", "id", "ie", "is", "it", "lt", "lu",
                         "lv", "mt", "mx", "my", "ni", "nl", "no", "nz", "pa",
                         "pe", "ph", "pl", "pt", "py", "se", "sg", "sk", "sv",
                         "tr", "tw", "uy", "global"}
        valid_windows = {"daily", "weekly"}

        def sanity_check(val, valid_set):
            if val not in valid_set:
                print(Fore.YELLOW +
                      "Not a valid Spotify charts URI parameter: " +
                      val + Fore.RESET)
                print("Valid parameter options are: [" +
                      ", ".join(valid_set)) + "]"
                return False
            return True

        def sanity_check_date(val):
            if  re.match(r"^\d{4}-\d{2}-\d{2}$", val) is None and \
                    val != "latest":
                print(Fore.YELLOW +
                      "Not a valid Spotify charts URI parameter: " +
                      val + Fore.RESET)
                print("Valid parameter options are: ['latest', a date "
                      "(e.g. 2016-01-21)]")
                return False
            return True

        check_results = sanity_check(uri_tokens[2], valid_metrics) and \
            sanity_check(uri_tokens[3], valid_regions) and \
            sanity_check(uri_tokens[4], valid_windows) and \
            sanity_check_date(uri_tokens[5])
        if not check_results:
            print("Generally, a charts URI follow the pattern "
                  "spotify:charts:metric:region:time_window:date")
            return None

        tracks_obj = get_chart_tracks(uri_tokens[2], uri_tokens[3],
                                      uri_tokens[4], uri_tokens[5])
        charts_obj = {
            "metrics": uri_tokens[2],
            "region": uri_tokens[3],
            "time_window": uri_tokens[4],
            "from_date": uri_tokens[5],
            "tracks": tracks_obj
        }

        self.cache_result(uri, charts_obj)
        return charts_obj
