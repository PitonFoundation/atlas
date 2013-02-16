/**
 * Handle uncaught JavaScript exceptions.
 */
;(function(window, document) {
  function errorPopup() {
    var errorBox = document.createElement("div");
    errorBox.className = 'error-popup';
    errorBox.innerHTML = "There was an unexpected error. You should try to reload the page while <a href='http://wikipedia.org/wiki/Wikipedia:Bypass_your_cache' title='Bypass your cache' onclick='window.open(this.href);return false;'>bypassing the cache</a>. If that doesn't fix the error, <a href='/contact/' title='Contact' onclick='window.open(this.href);return false;'>tell us what happened</a>.";
    document.body.appendChild(errorBox);
    return true;
  }
  
  function logError(logUrl, message, url, lineNumber) {
    if (logUrl && window.XMLHttpRequest) {
      var xhr = new XMLHttpRequest();
      var log = 'message='+message+'&url='+url+'&lineNumber='+lineNumber+'&location='+window.location.href;
      xhr.open("POST", logUrl);
      xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
      xhr.send(log);
    }
    return true;
  }

  window.onerror = function(message, url, lineNumber) {
    // For now don't show error popups until we have a way to make them
    // less obtrusive/blocking.
    // See https://github.com/PitonFoundation/atlas/issues/634
    //errorPopup();
    logError(window.jsLogUrl, message, url, lineNumber);
    return false;
  };
})(window, document);
