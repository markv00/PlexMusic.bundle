#
# Copyright (c) 2014 Plex Development Team. All rights reserved.
#

from urllib import quote
from Utils import normalize_artist_name

FANART_TV_API_KEY = '72519ab36caf49c09f69a028fb7f741d'
FANART_TV_ARTIST_URL = 'http://webservice.fanart.tv/v3/music/%s' # TODO: Cloudflare this.
FANART_TV_PREVIEW_URL = '%s/preview.jpg'

MB_ARTIST_URL = 'http://musicbrainz.org/ws/2/artist/%s'
MB_RELEASE_URL = 'http://musicbrainz.org/ws/2/release/%s?inc=release-groups'
MB_NS = {'a': 'http://musicbrainz.org/ns/mmd-2.0#'}

HTBACKDROPS_API_KEY = '15f8fe4ad7760d77c85e686eefafd26f'
HTBACKDROPS_SEARCH_URL = 'http://htbackdrops.org/api/%s/searchXML?mbid=%%s&default_operator=and&limit=50&aid=1' % HTBACKDROPS_API_KEY
HTBACKDROPS_THUMB_URL = 'http://htbackdrops.org/api/%s/download/%%s/thumbnail' % HTBACKDROPS_API_KEY
HTBACKDROPS_FULL_URL = 'http://htbackdrops.org/api/%s/download/%%s/fullsize' % HTBACKDROPS_API_KEY

def find_artist_posters(posters, artist, album_titles, lang):

    # Last.fm.
    try:
      lastfm_artist = Core.messaging.call_external_function('com.plexapp.agents.lastfm', 'MessageKit:ArtistSearch', kwargs = dict(artist=artist, albums=album_titles, lang=lang))
      if lastfm_artist and lastfm_artist['name'] != 'Various Artists':
        posters.extend([image['#text'] for image in lastfm_artist['image'] if len(image['#text']) > 0 and image['size'] == 'mega'])
        posters.extend([image['#text'] for image in lastfm_artist['image'] if len(image['#text']) > 0 and image['size'] == 'extralarge'])
      else:
        Log('No artist result from Last.fm')
    except Exception, e:
      Log('Error calling in to Last.fm for artist posters: ' + str(e))

    # Discogs cache.
    try:
      images = XML.ElementFromURL('http://meta.plex.tv/a/' + quote(normalize_artist_name(artist))).xpath('//image')
      posters.extend([image.get('url') for image in images if image.get('primary') == '1'])
      posters.extend([image.get('url') for image in images if image.get('primary') == '0'])
    except:
      Log('No artist result from Discogs cache')


def find_artist_art(arts, artist, album_titles, lang):

    # Get the artist from Last.fm so we can grab the musicbrainz id.
    try:
      lastfm_artist = Core.messaging.call_external_function('com.plexapp.agents.lastfm', 'MessageKit:ArtistSearch', kwargs = dict(artist=artist, albums=album_titles, lang=lang))
    except Exception, e:
      Log('Error calling in to Last.fm for artist artwork (MBID): ' + str(e))
      return

    # Fanart.tv.
    artist_json = None
    if 'mbid' in lastfm_artist and len(lastfm_artist['mbid']) == 36:  # Sanity check.
      try:
        artist_json = JSON.ObjectFromURL(FANART_TV_ARTIST_URL % lastfm_artist['mbid'], headers={'api-key':FANART_TV_API_KEY})
      except:
        # Go back and ask MB for a potentially updated id.
        Log('No results for Last.fm-returned mbid %s, checking for an updated one' % lastfm_artist['mbid'])
        try:
          artist_mbid = XML.ElementFromURL(MB_ARTIST_URL % lastfm_artist['mbid']).xpath('//a:artist/@id', namespace=MB_NS)[0]
          artist_json = JSON.ObjectFromURL(FANART_TV_ARTIST_URL % lastfm_artist['mbid'], headers={'api-key':FANART_TV_API_KEY})
        except:
          pass

      if artist_json and 'artistbackground' in artist_json:
        for art in artist_json['artistbackground']:
          arts.append((art['url'], FANART_TV_PREVIEW_URL % art['url']))

      # HT Backdrops.
      for image_id in XML.ElementFromURL(HTBACKDROPS_SEARCH_URL % lastfm_artist['mbid']).xpath('//image/id/text()'):
        arts.append((HTBACKDROPS_FULL_URL % image_id, HTBACKDROPS_THUMB_URL % image_id))