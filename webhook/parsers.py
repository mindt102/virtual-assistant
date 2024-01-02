from bs4 import BeautifulSoup


def youtube_parser(content: str) -> str:
    """Parse the content of a YouTube feed and return the link to the video"""
    # id, title, channelId, watchTime, duration
    video_url = None
    video = dict()
    try:
        soup = BeautifulSoup(content, 'xml')
        if not soup.entry:
            # TODO: log response
            return None
        entry = soup.entry
        video = {
            "_id": entry.videoId.text,
            "channelId": entry.channelId.text,
            "title": entry.title.text,
        }
        print(entry.prettify())
        print(video)
    # except Exception as e:
    #     unexpected_error_handler(logger, e, content=content)
    finally:
        return video_url


if __name__ == "__main__":
    content = """<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015"
         xmlns="http://www.w3.org/2005/Atom">
  <link rel="hub" href="https://pubsubhubbub.appspot.com"/>
  <link rel="self" href="https://www.youtube.com/xml/feeds/videos.xml?channel_id=CHANNEL_ID"/>
  <title>YouTube video feed</title>
  <updated>2015-04-01T19:05:24.552394234+00:00</updated>
  <entry>
    <id>yt:video:VIDEO_ID</id>
    <yt:videoId>VIDEO_ID</yt:videoId>
    <yt:channelId>CHANNEL_ID</yt:channelId>
    <title>Video title</title>
    <link rel="alternate" href="http://www.youtube.com/watch?v=VIDEO_ID"/>
    <author>
     <name>Channel title</name>
     <uri>http://www.youtube.com/channel/CHANNEL_ID</uri>
    </author>
    <published>2015-03-06T21:40:57+00:00</published>
    <updated>2015-03-09T19:05:24.552394234+00:00</updated>
  </entry>
</feed>"""
    print(youtube_parser(content))
