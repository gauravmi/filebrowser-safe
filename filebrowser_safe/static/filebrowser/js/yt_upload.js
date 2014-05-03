function bytesToSize(bytes) {
   var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
   if (bytes == 0) return '0 Bytes';
   var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
   return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
};

$('#yt_file_upload').change(function(event){
	var filenamewithpath = $('#yt_file_upload').val();
	var filename = filenamewithpath.split('\\').pop()

	var sizeIn = bytesToSize($('#yt_file_upload').get(0).files[0].size)

	$('.file-name-container').text(filename+'  (' +sizeIn+')');
	$('.file-name-container').show();
	$('.progress').show();
});

$('#submit-button').click(function(){
	file = $('#yt_file_upload').get(0).files[0]
	metadata = {
		title: file.name,
		description: file.name,
	}
	document.getElementById('disablingDiv').style.display='block';
	document.getElementById('message').style.display='block';

	$.ajax("/admin/media-library/get_access_token",{
		method: 'POST',
		contentType: 'application/json',
		data: metadata
	}).done(function(data, status, xhr){
		document.upload_video_to_youtube.action = data.posturl
		$('[name="token"]').val(data.youtube_token);
		document.upload_video_to_youtube.submit();
	}).fail(function(data){
		console.log(data);
	});
});