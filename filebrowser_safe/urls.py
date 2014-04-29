from __future__ import unicode_literals

from django.conf.urls import *

urlpatterns = patterns('',

    #youtube upload urls
    url(r'^browse_videos/$', 'filebrowser_safe.views.browse_videos', name="yt_browse_videos"),
		url(r'^delete_from_yt$', 'filebrowser_safe.views.delete_video', name="yt_delete_video"),
		# filebrowser urls
    url(r'^browse/$', 'filebrowser_safe.views.browse', name="fb_browse"),
    url(r'^mkdir/', 'filebrowser_safe.views.mkdir', name="fb_mkdir"),
    url(r'^upload/', 'filebrowser_safe.views.upload', name="fb_upload"),
    url(r'^rename/$', 'filebrowser_safe.views.rename', name="fb_rename"),
    url(r'^delete/$', 'filebrowser_safe.views.delete', name="fb_delete"),
    url(r'^check_file/$', 'filebrowser_safe.views._check_file', name="fb_check"),
    url(r'^upload_file/$', 'filebrowser_safe.views._upload_file', name="fb_do_upload"),
)
