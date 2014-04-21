from django import template
import re
# import gdata
# import gdata.youtube
# from filebrowser_safe.templatetags.fb_tags import register
#
register = template.Library()

def get_thumbnail_url(video):
    return video.media.thumbnail[2].url

def is_instance_of_file(obj):
    return obj.__class__.__name__ == "FileObject"

def get_thumbnail_for_id(url):
    return "http://img.youtube.com/vi/"+re.findall(r'(?<=v=)(.*)(?=&)', url.name)[0]+"/0.jpg"

register.filter('get_thumbnail_url',get_thumbnail_url)
register.filter('get_thumbnail_for_id',get_thumbnail_for_id)
register.filter('is_instance_of_file',is_instance_of_file)