from django import template
from filebrowser_safe.settings import *
# from django.template.defaultfilters import stringfilter

import re

register = template.Library()

def get_thumbnail_url(video):
    return video.media.thumbnail[2].url

def is_instance_of_file(obj):
    return obj.__class__.__name__ == "FileObject"

def get_thumbnail_for_id(url):
    return "http://img.youtube.com/vi/"+re.findall(r'(?<=v=)(.*)(?=&)', url.name)[0]+"/0.jpg"

def youtube(v):
	try:
		settings.YOUTUBE
	except NameError:
		settings.YOUTUBE = None
	return settings.YOUTUBE is not None

register.filter('get_thumbnail_url',get_thumbnail_url)
register.filter('get_thumbnail_for_id',get_thumbnail_for_id)
register.filter('is_instance_of_file',is_instance_of_file)
register.filter('youtube',youtube)