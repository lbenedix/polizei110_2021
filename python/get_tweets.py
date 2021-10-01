import json
from collections import OrderedDict
from datetime import timedelta
from difflib import get_close_matches
import urllib
from twython import Twython
from dateutil.parser import parse as parse_d

from stuff import known_locations, bezirke

APP_KEY = '***'
APP_SECRET = '***'

twitter = Twython(APP_KEY, APP_SECRET, oauth_version=2)
ACCESS_TOKEN = twitter.obtain_access_token()

twitter = Twython(APP_KEY, access_token=ACCESS_TOKEN)

all_hashtags = dict()
all_bezirke = dict()
done_ids = list()
all_tweets = list()

max_id = None
for _ in range(35):
    result = twitter.search(q='(#polizei110) (from:polizeiberlin_e)',
                            result_type='recent',
                            count=100,
                            max_id=max_id)

    next_url = result['search_metadata'].get('next_results', '').replace('?', '')
    if 'max_id' in next_url:
        max_id = urllib.parse.parse_qs(next_url)['max_id'][0]

    tweets = result['statuses']
    print(len(result['statuses']), result['search_metadata']['count'])

    for tweet in tweets:
        hash_tags = list()

        for h in tweet.get('entities',{}).get('hashtags',[]):
            hash_tags.append(h['text'].lower())

        if 'polizei110' in hash_tags:  # and not tweet['in_reply_to_screen_name']:
            t = OrderedDict()
            t['bezirk'] = ''
            t['text'] = tweet['text']
            t['hashtags'] = hash_tags
            dt = parse_d(tweet['created_at']) + timedelta(hours=2)
            t['time'] = dt.strftime('%Y%m%d%H%M%S')
            t['id'] = tweet['id']
            t['url'] = 'https://twitter.com/{}/status/{}'.format('polizeiberlin_e', tweet['id'])
            if int(t['time'][:4]) < 2019:
                continue

            for h in hash_tags:
                if h not in ['polizei110', ]:
                    # known locations with missing hashtag
                    if h.lower() in known_locations:
                        h = known_locations[h.lower()]
                    b = get_close_matches(h, bezirke, n=1)

                    if len(b) == 1:
                        t['bezirk'] = b[0]
                        if b[0] in all_bezirke:
                            all_bezirke[b[0]] += 1
                        else:
                            all_bezirke[b[0]] = 1

                if h in all_hashtags:
                    all_hashtags[h] += 1
                else:
                    all_hashtags[h] = 1

            if t['id'] not in done_ids:
                all_tweets.append(t)
                done_ids.append(t['id'])
                t['hashtags'] = ';'.join(t['hashtags'])
                # else:
                #     print('duplicate:', t)

    if 'next_results' not in result['search_metadata']:
        break

print(len(all_tweets))
json.dump(
    all_tweets,
    open('polizei110_2021.json', 'w', encoding='utf8'),
    indent=2,
    ensure_ascii=False,
    sort_keys=False
)

