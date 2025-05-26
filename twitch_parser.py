import os
import re
import requests
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional

from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")


class TwitchClipParser:
    def __init__(self):
        self.token = self.get_access_token()

    def get_access_token(self) -> str:
        url = 'https://id.twitch.tv/oauth2/token'
        params = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'client_credentials'
        }
        response = requests.post(url, params=params).json()
        return response['access_token']

    def get_user_id(self, username: str, headers: dict) -> Optional[str]:
        url = 'https://api.twitch.tv/helix/users'
        params = {'login': username}
        response = requests.get(url, headers=headers, params=params).json()
        if response.get('data'):
            return response['data'][0]['id']
        return None

    def get_clips(self, user_id: str, headers: dict) -> List[dict]:
        start_time = datetime.utcnow() - timedelta(days=14)
        started_at = start_time.isoformat("T") + "Z"
        url = 'https://api.twitch.tv/helix/clips'
        params = {
            'broadcaster_id': user_id,
            'first': 20,
            'started_at': started_at,
            'sort': 'views'
        }
        response = requests.get(url, headers=headers, params=params).json()
        return response.get('data', [])

    def get_best_new_clip(self, channels: List[str], processed_ids: Set[str]) -> Optional[dict]:
        headers = {
            'Client-ID': CLIENT_ID,
            'Authorization': f'Bearer {self.token}'
        }

        all_clips = []
        for channel in channels:
            user_id = self.get_user_id(channel, headers)
            if not user_id:
                continue
            clips = self.get_clips(user_id, headers)
            for clip in clips:
                clip['channel'] = channel
                if clip['id'] not in processed_ids:
                    all_clips.append(clip)

        if not all_clips:
            return None

        best = sorted(all_clips, key=lambda c: c['view_count'], reverse=True)[0]
        return best

    def sanitize_filename(self, name: str) -> str:
        return re.sub(r'[\\/:"*?<>|]+', '_', name)

    def download_clip(self, clip: dict, output_dir: str) -> str:
        title = clip['title']
        channel = clip['channel']
        clip_url = clip['url']
        clip_id = clip['id']

        filename = f"{channel} - {title}.mp4"
        filename = self.sanitize_filename(filename)
        output_path = os.path.join(output_dir, filename)

        subprocess.run(["yt-dlp", "-o", output_path, clip_url], check=True)
        return output_path, clip_id
