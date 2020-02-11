import sys, json, pymysql, numpy as np
from sklearn.naive_bayes import MultinomialNB

def import_tweet(j, cursor, cv, mnb):
  print (j['id'])

  cursor.execute("SELECT * FROM tweets WHERE id = %s", (int(j["id"]),))
  results = cursor.fetchall()

  mentioned_user_ids = []

  if ("entities" in j) and (j['entities'] is not None):
    mentioned_user_ids.extend([x["id_str"] for x in j['entities']['user_mentions']])

  if ("retweeted_status" in j) and (j["retweeted_status"] is not None):
    mentioned_user_ids.append(j["retweeted_status"]["user"]["id_str"])

  if ("quoted_status" in j) and (j["quoted_status"] is not None):
    mentioned_user_ids.append(j["quoted_status"]["user"]["id_str"])

  if ("in_reply_to_user_id_str" in j) and (j["in_reply_to_user_id_str"] != "") and (j["in_reply_to_user_id_str"] is not None):
    mentioned_user_ids.append(j["in_reply_to_user_id_str"])

  tweet_text = j['text'].encode('utf-8').decode('unicode_escape')
  data = cv.transform([tweet_text]).toarray()
  mnb_sentiment = mnb.predict(data)
  mnb_score = mnb.predict_proba(data)

  if len(results) == 0:
    #Adding new tweet
    cursor.execute("""
        INSERT INTO tweets (id, id_str, coordinates, created_at, current_user_retweet,
          entities, favorite_count, favorited, filter_level, in_reply_to_screen_name,
          in_reply_to_status_id, in_reply_to_status_id_str, in_reply_to_user_id,
          in_reply_to_user_id_str, lang, possibly_sensitive, quote_count, reply_count,
          retweet_count, retweeted, retweeted_status, source, scopes, text,
          full_text, display_text_range, place, truncated, user, withheld_copyright,
          withheld_in_countries, withheld_scope, extended_entities, extended_tweet,
          quoted_status_id, quoted_status_id_str, quoted_status, user_id, user_id_str, 
          mentioned_user_ids_str, mnb_sentiment, mnb_score)
        VALUES (%s, %s, %s, STR_TO_DATE(%s, '%%a %%b %%d %%H:%%i:%%s +0000 %%Y'), %s,
          %s, %s, %s, %s, %s,
          %s, %s, %s,
          %s, %s, %s, %s, %s,
          %s, %s, %s, %s, %s, %s,
          %s, %s, %s, %s, %s, %s,
          %s, %s, %s, %s,
          %s, %s, %s, %s, %s, 
          %s, %s, %s)""",
        (
          j['id'],
          j['id_str'],
          json.dumps(j['coordinates']),
          j['created_at'],
          json.dumps(j['current_user_retweet'] if 'current_user_retweet' in j else ''),
          json.dumps(j['entities']),
          j['favorite_count'],
          json.dumps(j['favorited']),
          json.dumps(j['filter_level'] if 'filter_level' in j else ''),
          j['in_reply_to_screen_name'],
          j['in_reply_to_status_id'],
          j['in_reply_to_status_id_str'],
          j['in_reply_to_user_id'],
          j['in_reply_to_user_id_str'],
          j['lang'],
          json.dumps(j['possibly_sensitive'] if 'possibly_sensitive' in j else False),
          j['quote_count'] if 'quote_count' in j else 0,
          j['reply_count'] if 'reply_count' in j else 0,
          j['retweet_count'] if 'retweet_count' in j else 0,
          json.dumps(j['retweeted']),
          json.dumps(j['retweeted_status'] if "retweeted_status" in j else ''),
          json.dumps(j['source']),
          json.dumps(j['scopes'] if 'scopes' in j else ''),
          json.dumps(j['text']),
          json.dumps(j['full_text'] if 'full_text' in j else ''),
          json.dumps(j['display_text_range'] if 'display_text_range' in j else ''),
          json.dumps(j['place']),
          json.dumps(j['truncated']),
          json.dumps(j['user']),
          json.dumps(j['withheld_copyright'] if 'withheld_copyright' in j else ''),
          json.dumps(j['withheld_in_countries'] if 'withheld_in_countries' in j else ''),
          json.dumps(j['withheld_scope'] if 'withheld_scope' in j else ''),
          json.dumps(j['extended_entities'] if 'extended_entities' in j else ''),
          json.dumps(j['extended_tweet'] if 'extended_tweet' in j else ''),
          j['quoted_status_id'] if 'quoted_status_id' in j else 0,
          j['quoted_status_id_str'] if 'quoted_status_id_str' in j else '',
          json.dumps(j['quoted_status'] if 'quoted_status' in j else ''),
          j['user']['id'],
          j['user']['id_str'],
          '|'.join(np.unique(mentioned_user_ids)),
          int(mnb_sentiment[0]),
          round(float(mnb_score[0][mnb_sentiment[0]]), 8),
        ))
  else:
    cursor.execute("""
        UPDATE tweets
        SET
          id_str = %s,
          coordinates = %s,
          created_at = STR_TO_DATE(%s, '%%a %%b %%d %%H:%%i:%%s +0000 %%Y'),
          current_user_retweet = %s,
          entities = %s,
          favorite_count = %s,
          favorited = %s,
          filter_level = %s,
          in_reply_to_screen_name = %s,
          in_reply_to_status_id = %s,
          in_reply_to_status_id_str = %s,
          in_reply_to_user_id = %s,
          in_reply_to_user_id_str = %s,
          lang = %s,
          possibly_sensitive = %s,
          quote_count = %s,
          reply_count = %s,
          retweet_count = %s,
          retweeted = %s,
          retweeted_status = %s,
          source = %s,
          scopes = %s,
          text = %s,
          full_text = %s,
          display_text_range = %s,
          place = %s,
          truncated = %s,
          user_id = %s,
          user_id_str = %s,
          user = %s,
          withheld_copyright = %s,
          withheld_in_countries = %s,
          withheld_scope = %s,
          extended_entities = %s,
          extended_tweet = %s,
          quoted_status_id = %s,
          quoted_status_id_str = %s,
          quoted_status = %s,
          mentioned_user_ids_str = %s,
          mnb_sentiment = %s, 
          mnb_score = %s
        WHERE id = %s
      """, (
          j['id_str'],
          json.dumps(j['coordinates']),
          j['created_at'],
          json.dumps(j['current_user_retweet'] if 'current_user_retweet' in j else ''),
          json.dumps(j['entities']),
          j['favorite_count'],
          json.dumps(j['favorited']),
          json.dumps(j['filter_level'] if 'filter_level' in j else ''),
          j['in_reply_to_screen_name'],
          j['in_reply_to_status_id'],
          j['in_reply_to_status_id_str'],
          j['in_reply_to_user_id'],
          j['in_reply_to_user_id_str'],
          j['lang'],
          json.dumps(j['possibly_sensitive'] if 'possibly_sensitive' in j else False),
          j['quote_count'] if 'quote_count' in j else 0,
          j['reply_count'] if 'reply_count' in j else 0,
          j['retweet_count'] if 'retweet_count' in j else 0,
          json.dumps(j['retweeted']),
          json.dumps(j['retweeted_status'] if "retweeted_status" in j else ''),
          json.dumps(j['source']),
          json.dumps(j['scopes'] if 'scopes' in j else ''),
          json.dumps(j['text']),
          json.dumps(j['full_text'] if 'full_text' in j else ''),
          json.dumps(j['display_text_range'] if 'display_text_range' in j else ''),
          json.dumps(j['place']),
          json.dumps(j['truncated']),
          j['user']['id'],
          j['user']['id_str'],
          json.dumps(j['user']),
          json.dumps(j['withheld_copyright'] if 'withheld_copyright' in j else ''),
          json.dumps(j['withheld_in_countries'] if 'withheld_in_countries' in j else ''),
          json.dumps(j['withheld_scope'] if 'withheld_scope' in j else ''),
          json.dumps(j['extended_entities'] if 'extended_entities' in j else ''),
          json.dumps(j['extended_tweet'] if 'extended_tweet' in j else ''),
          j['quoted_status_id'] if 'quoted_status_id' in j else 0,
          j['quoted_status_id_str'] if 'quoted_status_id_str' in j else '',
          json.dumps(j['quoted_status'] if 'quoted_status' in j else ''),
          '|'.join(np.unique(mentioned_user_ids)),
          int(mnb_sentiment[0]),
          round(float(mnb_score[0][mnb_sentiment[0]]), 8),
          j['id']
        ))

  cursor.execute("SELECT * FROM users WHERE id = %s", (int(j['user']['id']),))
  results = cursor.fetchall()

  if len(results) == 0:
    #Adding new user
    cursor.execute("""
        INSERT INTO users (contributors_enabled, created_at, default_profile, default_profile_image,
          description, email, entities, favourites_count, follow_request_sent, following, followers_count,
          friends_count, geo_enabled, id, id_str, is_translator, lang, listed_count, location, name,
          notifications, profile_background_color, profile_background_image_url, profile_background_image_url_https,
          profile_background_tile, profile_banner_url, profile_image_url, profile_image_url_https,
          profile_link_color, profile_sidebar_border_color, profile_sidebar_fill_color, profile_text_color,
          profile_use_background_image, protected, screen_name, show_all_inline_media, status,
          statuses_count, time_zone, url, utc_offset, verified, withheld_in_countries, withheld_scope)
        VALUES (%s, STR_TO_DATE(%s, '%%a %%b %%d %%H:%%i:%%s +0000 %%Y'), %s, %s, %s, %s, %s, %s, %s, %s,
          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (
          (1 if j['user']['contributors_enabled'] == 'True' else 0),
          j['user']['created_at'],
          (1 if j['user']['default_profile'] == 'True' else 0),
          (1 if j['user']['default_profile_image'] == 'True' else 0),
          json.dumps(j['user']['description']),
          j['user']['email'] if 'current_user_retweet' in j else '',
          json.dumps(j['user']['entities']),
          j['user']['favourites_count'],
          (1 if j['user']['follow_request_sent'] == 'True' else 0),
          (1 if j['user']['following'] == 'True' else 0),
          j['user']['followers_count'],
          j['user']['friends_count'],
          (1 if j['user']['geo_enabled'] == 'True' else 0),
          j['user']['id'],
          j['user']['id_str'],
          (1 if j['user']['is_translator'] == 'True' else 0),
          j['user']['lang'],
          j['user']['listed_count'],
          json.dumps(j['user']['location']),
          json.dumps(j['user']['name']),
          (1 if j['user']['notifications'] == 'True' else 0),
          j['user']['profile_background_color'],
          j['user']['profile_background_image_url'],
          j['user']['profile_background_image_url_https'],
          (1 if j['user']['profile_background_tile'] == 'True' else 0),
          j['user']['profile_banner_url'] if 'current_user_retweet' in j else '',
          j['user']['profile_image_url'],
          j['user']['profile_image_url_https'],
          j['user']['profile_link_color'],
          j['user']['profile_sidebar_border_color'],
          j['user']['profile_sidebar_fill_color'],
          j['user']['profile_text_color'],
          (1 if j['user']['profile_use_background_image'] == 'True' else 0),
          (1 if j['user']['protected'] == 'True' else 0),
          j['user']['screen_name'],
          (1 if j['user']['show_all_inline_media'] == 'True' else 0) if 'current_user_retweet' in j else 0,
          json.dumps(j['user']['status'] if 'current_user_retweet' in j else ''),
          j['user']['statuses_count'],
          json.dumps(j['user']['time_zone']),
          j['user']['url'],
          json.dumps(j['user']['utc_offset']),
          (1 if j['user']['verified'] == 'True' else 0),
          json.dumps(j['user']['withheld_in_countries'] if 'current_user_retweet' in j else ''),
          json.dumps(j['user']['withheld_scope'] if 'current_user_retweet' in j else '')
        ))


  if ("retweeted_status" in j) and (j["retweeted_status"] is not None):
    #print ("retweeted_status", j["retweeted_status"])
    import_tweet(j["retweeted_status"], cursor, cv, mnb)

  if ("quoted_status" in j) and (j["quoted_status"] is not None):
    #print ("quoted_status", j["quoted_status"])
    import_tweet(j["quoted_status"], cursor, cv, mnb)
