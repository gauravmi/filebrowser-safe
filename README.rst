
Overview
========

filebrowser_safe was created to provide a snapshot of the 
`FileBrowser asset manager <http://code.google.com/p/django-filebrowser/>`_ 
for `Django <http://www.djangoproject.com/>`_, to be referenced as a 
dependency for the `Mezzanine CMS for Django <http://mezzanine.jupo.org/>`_.

At the time of filebrowser_safe's creation, FileBrowser was incorrectly 
packaged on `PyPI <http://pypi.python.org/pypi>`_, and had also dropped 
compatibility with Django 1.1 - filebrowser_safe was therefore created to 
address these specific issues.

This repository exists for bug fixes and minor enhancements, and 
should some day become redundant, once the original FileBrowser becomes 
a feasibly stable dependency target.


This library is modified to integrate youbue api. this integration uses gdata-python-client library 
https://code.google.com/p/gdata-python-client/ to add youtube video management 
features which includes deleting videos from youtbe, listing user uploaded videos, searching.

to make the add the feature you need to add following configurations to your projct settings file

YOUTUBE={  
      "developer_key": 'xxx',  
      "client_id": 'xxx',  
      "email": 'xxx',  
      "password": 'xxx',  
      "username": 'xxx',  
      "source": 'youtube',  
      "redirect_url": "http:expectedurl.com",  
      "ssl": False,  
}

where
developer_key : you can get your developer key from here http://code.google.com/apis/youtube/dashboard/
                 create a account and regster the project
client_id: this va,ue you is the api credentials for the prject you have registered in gogle console https://console.developers.google.com/project  
other: these values are the normal gmail account credentials

also youcan configure the parameters like

      YOUTUBE_DEFAULT_LIST_PER_PAGE = 10  
      YOUTUBE_MAX_UPLOAD_SIZE = 2147000000  

for pagenation and file size limit respectively.
