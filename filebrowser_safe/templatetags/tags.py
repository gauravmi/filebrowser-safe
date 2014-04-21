from django import template
# import gdata
# import gdata.youtube
# from filebrowser_safe.templatetags.fb_tags import register
#
register = template.Library()

# def typeof(obj):
#     print "obj----------------------------------"
#     return isinstance(obj,gdata.youtube.YouTubeVideoEntry)
#
def get_thumbnail_url(video):
    return video.media.thumbnail[2].url

register.filter('get_thumbnail_url',get_thumbnail_url)