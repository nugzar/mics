from __future__ import print_function
import json, os, pymysql, import_tweet

def lambda_handler(event, context):

  con = pymysql.connect(
    host=os.environ['dbserver'],
    port=int(os.environ['dbport']),
    user=os.environ['dbuser'],
    passwd=os.environ['dbpassword'],
    db=os.environ['dbname'])

  cursor = con.cursor(pymysql.cursors.DictCursor)

  for record in event['Records']:
    likes = json.loads(record["body"])

    userid = likes["userid_str"]

    for tweet in likes["favorites"]:
      import_tweet.import_tweet(tweet, cursor)
      con.commit()

      cursor.execute("DELETE FROM favorited WHERE ID = %s", (tweet['id'],))
      con.commit()

      cursor.execute("""
        INSERT INTO favorited (ID, created_at, user_id, favorited_user_id, favorited_user_name, favorited_screen_name, full_text)
        VALUES(%s, STR_TO_DATE(%s, '%%a %%b %%d %%H:%%i:%%s +0000 %%Y'), %s, %s, %s, %s, %s)
      """, (
      tweet['id'],
      tweet['created_at'],
      userid,
      tweet['user']['id'],
      json.dumps(tweet['user']['name']),
      tweet['user']['screen_name'],
      json.dumps(tweet['text'])
    ))

    con.commit()

  con.close()

if __name__ == '__main__':

    os.environ['dbserver'] = "localhost"
    os.environ['dbport'] = "3306"
    os.environ['dbuser'] = "root"
    os.environ['dbpassword'] = ""
    os.environ['dbname'] = "w295"

    message = json.loads("""
    {
        "Records": [
            {
                "messageId": "059f36b4-87a3-44ab-83d2-661975830a7d",
                "receiptHandle": "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a...",
                "body": "Test message.",
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1545082649183",
                    "SenderId": "AIDAIENQZJOLO23YVJ4VO",
                    "ApproximateFirstReceiveTimestamp": "1545082649185"
                },
                "messageAttributes": {},
                "md5OfBody": "e4e68fb7bd0e697a0ae8f1bb342846b3",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-2:123456789012:my-queue",
                "awsRegion": "us-east-2"
            },
            {
                "messageId": "2e1424d4-f796-459a-8184-9c92662be6da",
                "receiptHandle": "AQEBzWwaftRI0KuVm4tP+/7q1rGgNqicHq...",
                "body": "Test message.",
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1545082650636",
                    "SenderId": "AIDAIENQZJOLO23YVJ4VO",
                    "ApproximateFirstReceiveTimestamp": "1545082650649"
                },
                "messageAttributes": {},
                "md5OfBody": "e4e68fb7bd0e697a0ae8f1bb342846b3",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-2:123456789012:my-queue",
                "awsRegion": "us-east-2"
            }
        ]
    }
    """)

    lambda_handler(message, None)