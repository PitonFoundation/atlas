(function($) {
  
  var defaultOptions = {
    markup: '<h3>Loading&hellip;</h3>',
    storyID: null,
    widgetUrl: '/stories/<id>/share-widget/',
    header: 'Sharing Options',
    appendeeSelector: 'body',
    addThisScriptTag: '<script type="text/javascript" src="http://s7.addthis.com/js/250/addthis_widget.js?domready=1"></script>',
    alignment: 'bottom left',
    addThisHeight: 32,
    onClick: function(event) {
      var $button = $(this);
      if ($button.data('share-popup').isOpen) {
        $button.data('share-popup').close();
      }
      else {
        $button.data('share-popup').open($button);
      }
      return false;
    }
  }; 
  
  var instances = [];
  
  var instanceMethods = {
    open: function() {
      var align = this.options.alignment.split(' ');
      var positionMethod = (this.$button.parent().get(0) == this.$popup.parent().get(0)) ? 'position' : 'offset';
      var position = {
        top: this.$button[positionMethod]().top + this.$button.outerHeight(),
        left: this.$button[positionMethod]().left
      }
      if (align[0] == 'top') {
        position.top = this.$button[positionMethod]().top - this.popupDimensions.outerHeight - this.options.addThisHeight;
      }
      if (align[1] == 'right') {
        position.left = this.$button[positionMethod]().left - this.popupDimensions.outerWidth + this.$button.outerWidth();
      }
      for (var i = 0; i < instances.length; i++) {
        if (instances[i] != this) {
          instances[i].close();
        }
      }
      this.$popup.css(position).slideDown().on('click', '.close', this.close);
      var firstTextInput = this.$popup.find('input, textarea').get(0);
      if (firstTextInput) firstTextInput.select();
      this.isOpen = true;
    },
    close: function() {
      this.$popup.slideUp().off('click', '.close');
      this.isOpen = false;
    }
  };
  
  // content cached per-story
  var widgetContent = {};
  
  // only add addThis script tag once
  var scriptAdded = false;
  
  var fetchContent = function(storyID, instance) {
    var header = '<header>' + instance.options.header + '<span class="close"></span></header>';
    if (!(storyID in widgetContent)) {
      $.ajax({
        url: instance.options.widgetUrl.replace('<id>', storyID),
        dataType: 'html',
        success: function(data, textStatus, jqXHR) {
          var content = header + data;
          if (!scriptAdded) {
            content += instance.options.addThisScriptTag;
            scriptAdded = true;
          }
          widgetContent[storyID] = content;
          loadContent(storyID, instance);
        },
        error: function(jqXHR, textStatus, errorThrown) {
          widgetContent[storyID] = header + '\
            <h1>Could not load widget!</h1>\
            <p class="error">' + errorThrown + '</p>\
          ';
          loadContent(storyID, instance);
        }
      });
    }
    else {
      loadContent(storyID, instance);
    }
  };
  
  var loadContent = function(id, instance) {
    instance.$popup.html(widgetContent[id]);
    // render off-screen, capture dimensions
    instance.$popup.css({
      left: '-1000px',
      top: '-1000px',
      display:'block'
    });
    if (!('popupDimensions' in instance)) {
      instance.popupDimensions = {
        outerHeight: instance.$popup.outerHeight(),
        outerWidth: instance.$popup.outerWidth()
      };
    }
  };
  
  var pluginMethods = {
    init: function(pluginOptions) {
      // override defaults with passed options
      pluginOptions = $.extend(true, {}, defaultOptions, pluginOptions);
      
      var plugin = this;
      this.each(function() {
        var $button = $(this);
        
        // clone pluginOptions for this instance
        var instanceOptions = $.extend(true, {}, pluginOptions);
        
        // defaults can be overridden by data-options JSON attribute on individual elements
        if ($button.data('options')) {
          $.extend(instanceOptions, $button.data('options'));
        }
        // story id can be specified by data-story-id, or via options
        instanceOptions.storyID = $button.data('story-id') || instanceOptions.storyID;
        
        var $appendee = $(instanceOptions.appendeeSelector);
        if ($appendee.length) {
          
          var instance = {};
          instance.$popup = $('<div class="storybase-share-popup"></div>');
          instance.$button = $button;
          instance.$appendee = $appendee;
          
          $appendee.append(instance.$popup);
          
          // copy over instance methods
          for (var name in instanceMethods) {
            instance[name] = $.proxy(instanceMethods[name], instance);
          }
          // store options used for this instance
          instance.options = instanceOptions;
          instance.isOpen = false;
          
          // attach instance to element
          $button.data('share-popup', instance);
          
          $button.on('click', instanceOptions.onClick);
          
          fetchContent(instanceOptions.storyID, instance);

          instances.push(instance);
        }
        else {
          $.error('jquery.storybaseshare Could not find element with selector ' + instanceOptions.appendeeSelector);
        }

      });
    },
    remove: function() {
      // @todo
    }
  };
  
  $.fn.storybaseShare = function(method) {
    if (pluginMethods[method]) {
      return pluginMethods[method].apply(this, Array.prototype.slice.call(arguments, 1));
    } 
    else if ($.isPlainObject(method) || !method) {
      return pluginMethods.init.apply(this, arguments);
    }
    else {
      $.error('Method ' +  method + ' does not exist on jQuery.storybaseShare');
    }
    
    return this;
  };
})(jQuery);
