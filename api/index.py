from flask import Flask, jsonify, request
import yt_dlp
import re

app = Flask(__name__)

def is_valid_youtube_url(url):
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube\.com|youtu\.be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    return re.match(youtube_regex, url) is not None

def fetch_youtube_data(video_url):
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'bestvideo+bestaudio/best',
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            title = info.get('title', 'Unknown Title')
            duration = int(info.get('duration', 0))
            thumbnail = info.get('thumbnail', '')

            items = []
            for fmt in info.get('formats', []):
                ext = fmt.get('ext', '')
                height = fmt.get('height', -1)
                width = fmt.get('width', -1)
                fps = fmt.get('fps', -1)
                url = fmt.get('url', '')
                acodec = fmt.get('acodec', 'none')
                vcodec = fmt.get('vcodec', 'none')

                if acodec != 'none' and vcodec != 'none':
                    type_ = 'video_with_audio'
                elif vcodec != 'none':
                    type_ = 'video'
                elif acodec != 'none':
                    type_ = 'audio'
                else:
                    continue

                if type_ == 'audio':
                    bitrate = fmt.get('abr', 0)
                    label = f"{ext} ({bitrate}kb/s)" if bitrate else f"{ext}"
                else:
                    label = f"{ext} ({height}p)" if height > 0 else f"{ext}"

                items.append({
                    'ext': ext,
                    'fps': fps if fps else -1,
                    'height': height if height else -1,
                    'label': label,
                    'type': type_,
                    'url': url,
                    'width': width if width else -1
                })

            return {
                'code': 0,
                'data': {
                    'cover': thumbnail,
                    'duration': duration,
                    'items': items,
                    'title': title
                }
            }
    except Exception as e:
        return {
            'code': 1,
            'error': f"Failed to fetch video data: {str(e)}"
        }

@app.route('/youtube', methods=['GET'])
def youtube_api():
    video_url = request.args.get('url')
    if not video_url or not is_valid_youtube_url(video_url):
        return jsonify({'code': 1, 'error': 'Invalid or missing YouTube URL'}), 400
    return jsonify(fetch_youtube_data(video_url))

# For Vercel
def handler(event, context):
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    return app
