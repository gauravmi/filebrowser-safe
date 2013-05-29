var FileBrowserDialogue = {
    fileSubmit : function (FileURL) {
        this.parentWin.document.getElementById(this.parentWin.tinymce_activeInput).value = FileURL;
        this.parentWin.tinymce_activeFrame.close();
    },

    parentWin: (!window.frameElement && window.dialogArguments) || opener || parent || top
}
