/*** Dialog class: handles dialog (modal) display and behavior. ***/

let dialog = (function() {
	// get the dialog object from the page
	let dialog = $(".dialog");
	let dialogText = dialog.children().children(".dialog-text");

	// display dialog
	let show = function(type, message) {
		dialog.addClass(type);
		dialogText.text(message);
	    dialog.addClass("show");
	    return true;
	}

	// shortcut to close dialog
	let hide = function() {
		dialog.removeClass("show");
		return true;
	}

	// shortcut for error handling
	let throwError = function(message) {
	    show("error", message);
	    return true;
	}

	dialog.on('click', ".close-dialog", hide);
	
	return {
        show: show,
        hide: hide,
        throwError: throwError
	}
})(); 
