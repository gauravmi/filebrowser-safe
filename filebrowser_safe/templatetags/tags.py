from django import template
from filebrowser_safe.settings import *
# from django.template.defaultfilters import stringfilter
from django.core.urlresolvers import reverse
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

def video_id(url):
	return re.findall(r'(?<=v=)(.*)(?=&)', url)[0]

@register.simple_tag(name='get_upload_url')
def get_upload_url(display,posturl):
	if display:
		return posturl
	else:
		return reverse(posturl)

register.filter('get_thumbnail_url',get_thumbnail_url)
register.filter('get_thumbnail_for_id',get_thumbnail_for_id)
register.filter('is_instance_of_file',is_instance_of_file)
register.filter('youtube',youtube)
register.filter('video_id',video_id)