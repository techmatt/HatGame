/*** Dialog class: handles dialog (modal) display and behavior. ***/

let dialog = (function() {
	// get the dialog object from the page
	let dialog = $(".dialog");
	let dialogText = dialog.children().children(".dialog-text");
	let activeDialog = false;

	// display dialog
	let show = function(type, message) {
		activeDialog = true;
		dialog.addClass(type);
		dialogText.text(message);
	    dialog.addClass("show");
	    return true;
	}

	// shortcut to close dialog
	let hide = function() {
		if(activeDialog === true) {
			dialog.removeClass("show");
		}
		activeDialog = false;
		return true;
	}

	// shortcut for error handling
	let throwError = function(message) {
	    show("error", message);
	    return true;
	}
    
    // close if X is clicked
	dialog.on('click', ".close-dialog", hide);
	// todo: figure out clean way to close if outside is clicked
	// without causing it to instantly close
    
	return {
        show: show,
        hide: hide,
        throwError: throwError
	}
})(); 
