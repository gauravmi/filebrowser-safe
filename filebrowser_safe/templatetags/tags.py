from django import template
from filebrowser_safe.settings import *
# from django.template.defaultfilters import stringfilter
from django.core.urlresolvers import reverse
import re
import datetime
import time

register = template.Library()

def get_thumbnail_url(video):
    return video.media.thumbnail[2].url

def is_instance_of_file(obj):
    return obj.__class__.__name__ == "FileObject"

def get_yt_url(url):
	return 'http://www.youtube.com/watch?v='+url.name

def get_thumbnail_for_id(url):
	return "http://img.youtube.com/vi/"+url.name+"/0.jpg"

def youtube(v):
	try:
		settings.YOUTUBE
	except AttributeError:
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

@register.simple_tag(name='get_video_status')
def get_video_status(yt_service,entry):
	upload_status = yt_service.CheckUploadStatus(entry)
	status = ""
	if upload_status is not None:
		video_upload_state = upload_status[0]
		detailed_message = upload_status[1]
		status = video_upload_state
		if detailed_message:
			status = video_upload_state+'( '+ detailed_message +' )'
	return status

def format_date(date):
	_tmp = time.strptime(date, '%Y-%m-%dT%H:%M:%S.000Z')
	ptime = datetime.datetime(*_tmp[:6])
	return ptime

register.filter('format_date',format_date)
register.filter('get_thumbnail_url',get_thumbnail_url)
register.filter('get_thumbnail_for_id',get_thumbnail_for_id)
register.filter('is_instance_of_file',is_instance_of_file)
register.filter('youtube',youtube)
register.filter('video_id',video_id)
register.filter('get_yt_url',get_yt_url)