import gdata
import gdata.youtube
import gdata.youtube.service
from django.conf import settings as django_settings
from filebrowser_safe.settings import *

class YoutubeClient:
	def __init__(self):
		self.yt_service = gdata.youtube.service.YouTubeService()

	def login(self):
		try:
			print settings.YOUTUBE
		except Exception as e:
			print e

		if settings.YOUTUBE:
			self.yt_service.ssl = settings.YOUTUBE.get("developer_key",False)

			self.yt_service.developer_key = settings.YOUTUBE["developer_key"]
			self.yt_service.client_id = settings.YOUTUBE["developer_key"]

			self.yt_service.email = settings.YOUTUBE["email"]
			self.yt_service.password = settings.YOUTUBE["password"]
			self.yt_service.source = settings.YOUTUBE["source"]
			self.yt_service.redirect_url = settings.YOUTUBE["redirect_url"]
			self.yt_service.ProgrammaticLogin()
			return self.yt_service