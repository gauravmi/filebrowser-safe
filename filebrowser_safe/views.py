from __future__ import unicode_literals
import cgi
import json
from json import dumps
import os
import re
from httplib2 import Http
from urllib import urlencode
from itertools import chain

from django.conf import settings as django_settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import default_storage
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.dispatch import Signal
from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, HttpResponse
from django.template import RequestContext as Context
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
import gdata
import gdata.youtube
import gdata.youtube.service
import requests
from filebrowser_safe.youtube_client import YoutubeClient

try:
    from django.utils.encoding import smart_text
except ImportError:
    # Backward compatibility for Py2 and Django < 1.5
    from django.utils.encoding import smart_unicode as smart_text

from filebrowser_safe.settings import *
from filebrowser_safe.functions import (get_path, get_breadcrumbs,
    get_filterdate, get_settings_var, get_directory, convert_filename)
from filebrowser_safe.templatetags.fb_tags import query_helper
from filebrowser_safe.base import FileObject
from filebrowser_safe.decorators import flash_login_required

from mezzanine.utils.importing import import_dotted_path


# Add some required methods to FileSystemStorage
storage_class_name = django_settings.DEFAULT_FILE_STORAGE.split(".")[-1]
mixin_class_name = "filebrowser_safe.storage.%sMixin" % storage_class_name

# Workaround for django-s3-folder-storage
if django_settings.DEFAULT_FILE_STORAGE == 's3_folder_storage.s3.DefaultStorage':
    mixin_class_name = 'filebrowser_safe.storage.S3BotoStorageMixin'

try:
    mixin_class = import_dotted_path(mixin_class_name)
    storage_class = import_dotted_path(django_settings.DEFAULT_FILE_STORAGE)
except ImportError:
    pass
else:
    if mixin_class not in storage_class.__bases__:
        storage_class.__bases__ += (mixin_class,)


# Precompile regular expressions
filter_re = []
for exp in EXCLUDE:
    filter_re.append(re.compile(exp))
for k, v in VERSIONS.items():
    exp = (r'_%s.(%s)') % (k, '|'.join(EXTENSION_LIST))
    filter_re.append(re.compile(exp))

def get_access_token(request):
		client = YoutubeClient()
		client.authenticate()
		client.yt_service.ProgrammaticLogin()
		data = dict(request.GET.iterlists())

		title= data['title'][0]
		description= data['description'][0]

		media_group = gdata.media.Group(
		title=gdata.media.Title(text=title),
		description=gdata.media.Description(description_type='plain',
		                              text=description),
		keywords=gdata.media.Keywords(text='people'),
		category=[gdata.media.Category(
			text='Autos',
			scheme='http://gdata.youtube.com/schemas/2007/categories.cat',
			label='Autos')],
			player=None
		)
		# create video entry as usual
		video_entry = gdata.youtube.YouTubeVideoEntry(media=media_group)

		response = client.yt_service.GetFormUploadToken(video_entry)
		# parse response tuple and use the variables to build a form (see next code snippet)
		posturl = response[0]
		youtube_token = response[1]

		nexturl = ""
		if settings.YOUTUBE:
				print settings.YOUTUBE["redirect_url"]
				nexturl = settings.YOUTUBE["redirect_url"]

		redirect_url_with_video_type = '%s?%s' % (nexturl,'type=Video-Field')
		posturl = posturl+"?nexturl="+ redirect_url_with_video_type

		response_data = {
			'posturl':posturl,
			'youtube_token':youtube_token,
		}
		return HttpResponse(json.dumps(response_data), content_type="application/json")

def browse_videos(request):
    client = YoutubeClient()
    client.authenticate()
    client.yt_service.ProgrammaticLogin()
    search_terms = request.GET.get('q',False)
    if search_terms:
		query = gdata.youtube.service.YouTubeVideoQuery()
		query.vq = search_terms
		query.author = settings.YOUTUBE.get("username","")
		query.orderby = 'viewCount'
		videos = client.yt_service.YouTubeQuery(query)
    else:
        videos = client.yt_service.GetYouTubeVideoFeed("https://gdata.youtube.com/feeds/api/users/default/uploads")

    results_var = {'results_total': 0, 'results_current': 0, 'delete_total': 0, 'images_total': 0, 'select_total': 0}
    query = request.GET.copy()

    query['ot'] = "desc"
    p = Paginator(videos.entry, YT_DEFAULT_LIST_PER_PAGE)
    try:
        page_nr = request.GET.get('p', '1')
    except:
        page_nr = 1
    try:
        page = p.page(page_nr)
    except (EmptyPage, InvalidPage):
        page = p.page(p.num_pages)
    display = request.GET.get("type", False)
    results_var['results_current']=results_var['select_total']=results_var['results_total']=results_var['images_total'] = len(videos.entry)

    return render_to_response('filebrowser/index.html', {
        'yt_service': client.yt_service,
        'display': display,
        'p': p,
        'results_var':results_var,
        'query':query,
        'page': page,
        'settings_var': get_settings_var(),
        'breadcrumbs_title': _(u'Youtube Upload'),
        'videos': videos
    }, context_instance=Context(request))

def browse(request):
    """
    Browse Files/Directories.
    """

    # QUERY / PATH CHECK
    # type_of_list = ""
    query = request.GET.copy()
    path = get_path(query.get('dir', ''))
    directory = get_path('')

    if path is None:
        msg = _('The requested Folder does not exist.')
        messages.add_message(request, messages.ERROR, msg)
        if directory is None:
            # The directory returned by get_directory() does not exist, raise an error to prevent eternal redirecting.
            raise ImproperlyConfigured(_("Error finding Upload-Folder. Maybe it does not exist?"))
        redirect_url = reverse("fb_browse") + query_helper(query, "", "dir")
        return HttpResponseRedirect(True)
    abs_path = os.path.join(get_directory(), path)

    # INITIAL VARIABLES
    results_var = {'results_total': 0, 'results_current': 0, 'delete_total': 0, 'images_total': 0, 'select_total': 0}
    counter = {}
    for k, v in EXTENSIONS.items():
        counter[k] = 0

    dir_list, file_list = default_storage.listdir(abs_path)
    files = []
    for file in dir_list + file_list:

        # EXCLUDE FILES MATCHING VERSIONS_PREFIX OR ANY OF THE EXCLUDE PATTERNS

        filtered = not file or file.startswith('.')
        for re_prefix in filter_re:
            if re_prefix.search(file):
                filtered = True
        if filtered:
            continue
        results_var['results_total'] += 1

        # CREATE FILEOBJECT
        url_path = "/".join([s.strip("/") for s in
                            [get_directory(), path, file] if s.strip("/")])
        fileobject = FileObject(url_path)

        # FILTER / SEARCH
        append = False
        if fileobject.filetype == request.GET.get('filter_type', fileobject.filetype) and get_filterdate(request.GET.get('filter_date', ''), fileobject.date):
            append = True
        if request.GET.get('q') and not re.compile(request.GET.get('q').lower(), re.M).search(file.lower()):
            append = False

        # APPEND FILE_LIST
        if append:
            try:
                # COUNTER/RESULTS
                if fileobject.filetype == 'Image':
                    results_var['images_total'] += 1
                if fileobject.filetype != 'Folder':
                    results_var['delete_total'] += 1
                elif fileobject.filetype == 'Folder' and fileobject.is_empty:
                    results_var['delete_total'] += 1
                if query.get('type') and query.get('type') in SELECT_FORMATS and fileobject.filetype in SELECT_FORMATS[query.get('type')]:
                    results_var['select_total'] += 1
                elif not query.get('type'):
                    results_var['select_total'] += 1
            except OSError:
                # Ignore items that have problems
                continue
            else:
                files.append(fileobject)
                results_var['results_current'] += 1

        # COUNTER/RESULTS
        if fileobject.filetype:
            counter[fileobject.filetype] += 1


    # SORTING
    query['o'] = request.GET.get('o', DEFAULT_SORTING_BY)
    query['ot'] = request.GET.get('ot', DEFAULT_SORTING_ORDER)
    files = sorted(files, key=lambda f: getattr(f, request.GET.get('o', DEFAULT_SORTING_BY)))
    if not request.GET.get('ot') and DEFAULT_SORTING_ORDER == "desc" or request.GET.get('ot') == "desc":
        files.reverse()
    p = Paginator(files, LIST_PER_PAGE)
    try:
        page_nr = request.GET.get('p', '1')
    except:
        page_nr = 1
    try:
        page = p.page(page_nr)
    except (EmptyPage, InvalidPage):
        page = p.page(p.num_pages)
    display = request.GET.get("type", False)
    return render_to_response('filebrowser/index.html', {
        'display': display,
        'dir': path,
        'p': p,
        'page': page,
        'results_var': results_var,
        'counter': counter,
        'query': query,
        'title': _(u'Media Library'),
        'settings_var': get_settings_var(),
        'breadcrumbs': get_breadcrumbs(query, path),
        'breadcrumbs_title': _(u'Upload'),
    }, context_instance=Context(request))
browse = staff_member_required(never_cache(browse))


# mkdir signals
filebrowser_pre_createdir = Signal(providing_args=["path", "dirname"])
filebrowser_post_createdir = Signal(providing_args=["path", "dirname"])


def mkdir(request):
    """
    Make Directory.
    """

    from filebrowser_safe.forms import MakeDirForm

    # QUERY / PATH CHECK
    query = request.GET
    path = get_path(query.get('dir', ''))
    if path is None:
        msg = _('The requested Folder does not exist.')
        messages.add_message(request, messages.ERROR, msg)
        return HttpResponseRedirect(reverse("fb_browse"))
    abs_path = os.path.join(get_directory(), path)

    if request.method == 'POST':
        form = MakeDirForm(abs_path, request.POST)
        if form.is_valid():
            server_path = os.path.join(abs_path, form.cleaned_data['dir_name'])
            try:
                # PRE CREATE SIGNAL
                filebrowser_pre_createdir.send(sender=request, path=path, dirname=form.cleaned_data['dir_name'])
                # CREATE FOLDER
                default_storage.makedirs(server_path)
                # POST CREATE SIGNAL
                filebrowser_post_createdir.send(sender=request, path=path, dirname=form.cleaned_data['dir_name'])
                # MESSAGE & REDIRECT
                msg = _('The Folder %s was successfully created.') % (form.cleaned_data['dir_name'])
                messages.add_message(request, messages.SUCCESS, msg)
                # on redirect, sort by date desc to see the new directory on top of the list
                # remove filter in order to actually _see_ the new folder
                # remove pagination
                redirect_url = reverse("fb_browse") + query_helper(query, "ot=desc,o=date", "ot,o,filter_type,filter_date,q,p")
                return HttpResponseRedirect(redirect_url)
            except OSError as xxx_todo_changeme:
                (errno, strerror) = xxx_todo_changeme.args
                if errno == 13:
                    form.errors['dir_name'] = forms.util.ErrorList([_('Permission denied.')])
                else:
                    form.errors['dir_name'] = forms.util.ErrorList([_('Error creating folder.')])
    else:
        form = MakeDirForm(abs_path)

    return render_to_response('filebrowser/makedir.html', {
        'form': form,
        'query': query,
        'title': _(u'New Folder'),
        'settings_var': get_settings_var(),
        'breadcrumbs': get_breadcrumbs(query, path),
        'breadcrumbs_title': _(u'New Folder')
    }, context_instance=Context(request))
mkdir = staff_member_required(never_cache(mkdir))

def upload(request):
    """
    Multiple File Upload.
    """

    from django.http import parse_cookie

    # QUERY / PATH CHECK
    query = request.GET
    path = get_path(query.get('dir', ''))
    if path is None:
        msg = _('The requested Folder does not exist.')
        messages.add_message(request, messages.ERROR, msg)
        return HttpResponseRedirect(True)

    # SESSION (used for flash-uploading)
    cookie_dict = parse_cookie(request.META.get('HTTP_COOKIE', ''))
    engine = __import__(settings.SESSION_ENGINE, {}, {}, [''])
    session_key = cookie_dict.get(settings.SESSION_COOKIE_NAME, None)
    display = request.GET.get('type',False)
    posturl = "fb_do_upload"
    youtube_token = ""
    template = 'upload.html'
    allowed_file_formats = ",".join(chain.from_iterable(get_settings_var()['EXTENSIONS'].values()))
    print allowed_file_formats

    if display:
        template = 'yt_upload.html'
        allowed_file_formats = ",".join(chain.from_iterable(get_settings_var()['YT_SUPPORTED_FILE_FORMATS'].values()))
    return render_to_response('filebrowser/'+template, {
				'youtube_token':youtube_token,
				'posturl': posturl,
        'query': query,
        'allowed_file_formats':allowed_file_formats,
        'display': display,
        'title': _(u'Select files to upload'),
        'settings_var': get_settings_var(),
        'session_key': session_key,
        'breadcrumbs': get_breadcrumbs(query, path),
        'breadcrumbs_title': _(u'Upload')
    }, context_instance=Context(request))
upload = staff_member_required(never_cache(upload))


@csrf_exempt
def _check_file(request):
    """
    Check if file already exists on the server.
    """
    folder = request.POST.get('folder')
    fb_uploadurl_re = re.compile(r'^.*(%s)' % reverse("fb_upload"))
    folder = fb_uploadurl_re.sub('', folder)
    fileArray = {}
    if request.method == 'POST':
        for k, v in list(request.POST.items()):
            if k != "folder":
                if default_storage.exists(os.path.join(get_directory(), folder, v)):
                    fileArray[k] = v
    return HttpResponse(dumps(fileArray))


# upload signals
filebrowser_pre_upload = Signal(providing_args=["path", "file"])
filebrowser_post_upload = Signal(providing_args=["path", "file"])

def delete_video(request):
	client = YoutubeClient()
	client.authenticate()
	client.yt_service.ProgrammaticLogin()
	entry = client.yt_service.GetYouTubeVideoEntry('https://gdata.youtube.com/feeds/api/users/default/uploads/'+request.GET['video_id'])
	response = client.yt_service.DeleteVideoEntry(entry)
	redirect_url = reverse('yt_browse_videos')
	redirect_url_with_query_string = '%s?%s' % (redirect_url,'type=Video-Field')
	return HttpResponseRedirect(redirect_url_with_query_string)

@csrf_exempt
@flash_login_required
@staff_member_required
def _upload_file(request):
    """
    Upload file to the server.

    Implement unicode handlers - https://github.com/sehmaschine/django-filebrowser/blob/master/filebrowser/sites.py#L471
    """
    if request.method == 'POST':
        folder = request.POST.get('folder')
        fb_uploadurl_re = re.compile(r'^.*(%s)' % reverse("fb_upload"))
        folder = fb_uploadurl_re.sub('', folder)

        if request.FILES:
            filedata = request.FILES['Filedata']
            # PRE UPLOAD SIGNAL
            filebrowser_pre_upload.send(sender=request, path=request.POST.get('folder'), file=filedata)

            filedata.name = convert_filename(filedata.name)

            # HANDLE UPLOAD
            exists = default_storage.exists(os.path.join(get_directory(), folder, filedata.name))
            abs_path = os.path.join(get_directory(), folder, filedata.name)
            uploadedfile = default_storage.save(abs_path, filedata)

            path = os.path.join(get_directory(), folder)
            file_name = os.path.join(path, filedata.name)
            if exists:
                default_storage.move(smart_text(uploadedfile), smart_texst(file_name), allow_overwrite=True)

            # POST UPLOAD SIGNAL
            filebrowser_post_upload.send(sender=request, path=request.POST.get('folder'), file=FileObject(smart_text(file_name)))
    return HttpResponse('True')


# delete signals
filebrowser_pre_delete = Signal(providing_args=["path", "filename"])
filebrowser_post_delete = Signal(providing_args=["path", "filename"])


def delete(request):
    """
    Delete existing File/Directory.

    When trying to delete a Directory, the Directory has to be empty.
    """

    if request.method != "POST":
        return HttpResponseRedirect(reverse("fb_browse"))

    # QUERY / PATH CHECK
    query = request.GET
    path = get_path(query.get('dir', ''))
    filename = query.get('filename', '')
    if path is None or filename is None:
        if path is None:
            msg = _('The requested Folder does not exist.')
        else:
            msg = _('The requested File does not exist.')
        messages.add_message(request, messages.ERROR, msg)
        return HttpResponseRedirect(reverse("fb_browse"))
    abs_path = os.path.join(get_directory(), path)
    if request.GET.get('filetype') != "Folder":
        relative_server_path = os.path.join(get_directory(), path, filename)
        try:
            # PRE DELETE SIGNAL
            filebrowser_pre_delete.send(sender=request, path=path, filename=filename)
            # DELETE FILE
            default_storage.delete(os.path.join(abs_path, filename))
            # POST DELETE SIGNAL
            filebrowser_post_delete.send(sender=request, path=path, filename=filename)
            # MESSAGE & REDIRECT
            msg = _('The file %s was successfully deleted.') % (filename.lower())
            messages.add_message(request, messages.SUCCESS, msg)
        except OSError:
            msg = _("An error occurred")
            messages.add_message(request, messages.ERROR, msg)
    else:
        try:
            # PRE DELETE SIGNAL
            filebrowser_pre_delete.send(sender=request, path=path, filename=filename)
            # DELETE FOLDER
            default_storage.rmtree(os.path.join(abs_path, filename))
            # POST DELETE SIGNAL
            filebrowser_post_delete.send(sender=request, path=path, filename=filename)
            # MESSAGE & REDIRECT
            msg = _('The folder %s was successfully deleted.') % (filename.lower())
            messages.add_message(request, messages.SUCCESS, msg)
        except OSError:
            msg = _("An error occurred")
            messages.add_message(request, messages.ERROR, msg)
    qs = query_helper(query, "", "filename,filetype")
    return HttpResponseRedirect(reverse("fb_browse") + qs)
delete = staff_member_required(never_cache(delete))


# rename signals
filebrowser_pre_rename = Signal(providing_args=["path", "filename", "new_filename"])
filebrowser_post_rename = Signal(providing_args=["path", "filename", "new_filename"])


def rename(request):
    """
    Rename existing File/Directory.

    Includes renaming existing Image Versions/Thumbnails.
    """

    from filebrowser_safe.forms import RenameForm

    # QUERY / PATH CHECK
    query = request.GET
    path = get_path(query.get('dir', ''))
    filename = query.get('filename', '')
    if path is None or filename is None:
        if path is None:
            msg = _('The requested Folder does not exist.')
        else:
            msg = _('The requested File does not exist.')
        messages.add_message(request, messages.ERROR, msg)
        return HttpResponseRedirect(reverse("fb_browse"))
    abs_path = os.path.join(MEDIA_ROOT, get_directory(), path)
    file_extension = os.path.splitext(filename)[1].lower()

    if request.method == 'POST':
        form = RenameForm(abs_path, file_extension, request.POST)
        if form.is_valid():
            relative_server_path = os.path.join(get_directory(), path, filename)
            new_filename = form.cleaned_data['name'] + file_extension
            new_relative_server_path = os.path.join(get_directory(), path, new_filename)
            try:
                # PRE RENAME SIGNAL
                filebrowser_pre_rename.send(sender=request, path=path, filename=filename, new_filename=new_filename)
                # RENAME ORIGINAL
                default_storage.move(relative_server_path, new_relative_server_path)
                # POST RENAME SIGNAL
                filebrowser_post_rename.send(sender=request, path=path, filename=filename, new_filename=new_filename)
                # MESSAGE & REDIRECT
                msg = _('Renaming was successful.')
                messages.add_message(request, messages.SUCCESS, msg)
                redirect_url = reverse("fb_browse") + query_helper(query, "", "filename")
                return HttpResponseRedirect(redirect_url)
            except OSError as xxx_todo_changeme1:
                (errno, strerror) = xxx_todo_changeme1.args
                form.errors['name'] = forms.util.ErrorList([_('Error.')])
    else:
        form = RenameForm(abs_path, file_extension)

    return render_to_response('filebrowser/rename.html', {
        'form': form,
        'query': query,
        'file_extension': file_extension,
        'title': _(u'Rename "%s"') % filename,
        'settings_var': get_settings_var(),
        'breadcrumbs': get_breadcrumbs(query, path),
        'breadcrumbs_title': _(u'Rename')
    }, context_instance=Context(request))
rename = staff_member_required(never_cache(rename))
