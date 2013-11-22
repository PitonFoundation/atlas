/**
 * Custom editors for backbone-forms
 */
;(function($, _, Backbone, wysihtml5, storybase) {

  if (_.isUndefined(storybase.forms)) {
    storybase.forms = {};
  }
  var forms = storybase.forms;

  forms.File = Backbone.Form.editors.Text.extend({
    initialize: function(options) {
      Backbone.Form.editors.Base.prototype.initialize.call(this, options);

      this.$el.attr('type', 'file');

    },

    /**
     * Set up for file/image thumbnail rendering.
     * 
     * We can't seem to render thumbnails directly from here. It seems that
     * render is called while our element is detached, so inserting an image
     * before or after the input element has no effect once this editor's 
     * element is inserted into the page.
     * 
     * We *could* probably customize this editor to use a div container
     * and render the thumbnail inside the div, as a sibling to the input,
     * making the thumbnail a part of the BB.Forms "editor" definition.
     *
     * For now, just annotate the input with its thumbnail as data—either a
     * path or a special value of some sort. The view can then be
     * responsible for actually rendering the thumb at the appropriate time.
     * 
     * Also @see BBFFormMixin.renderFileFieldThumbnail.
     */
    render: function() {
      Backbone.Form.editors.Base.prototype.render.apply(this, arguments);
      if (this.model.get('thumbnail_url')) {
        this.$el.data('file-thumbnail', this.model.get('thumbnail_url'));
      }
      else if (this.model.get('file')) {
        this.$el.data('file-thumbnail', '__set__');
      }
      return this;
    },

    /**
     * Set the editor value.
     *
     * This version doesn't do anything because the browser doesn't
     * let you set the value of a file input for security reasons.
     */
    setValue: function(value) {
    },

    getValue: function() {
      // Check if the files property is defined.  It won't be for browsers
      // that don't support the HTML5 File API
      if (this.el.files) {
        // If the File API is supported, return a FILE object
        return this.el.files[0];
      }
      else {
        // Otherwise, return the element value, probably a string
        // representation of the filename.
        return this.$el.val();
      }
    },
   
    /**
     * Retrieve the file selected in this input as a data URL
     */
    getValueAsDataURL: function(loadCallback, errorCallback) {
      var file = this.el.files[0];
      if (file) {
        var reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = function(evt) {
          loadCallback(evt.target.result);
        };
      }
    }
  });


  /**
   * Custom validator for checkboxes.  
   *
   * For whatever reason, 'required' didn't work
   */
  forms.isChecked = function(value, formValues) {
    var err = {
      type: 'checked',
      message: gettext("You must check this checkbox")
    };
    if (!value.length) {
      return err;
    }
  };

  /**
   * Update a field's schema definiton with properties
   * relevant to a required field
   */
  forms.makeRequired = function(fieldDef) {
    var validators = fieldDef.validators || [];
    var fieldClass = fieldDef.fieldClass || '';
    var editorAttrs = fieldDef.editorAttrs || {};

    validators.push('required');
    fieldClass += ' required'; 

    // For now, we are not using the "required" attribute. Browser
    // support and UI for validation is inconsistent.
    //editorAttrs.required = 'required';

    return _.extend(fieldDef, {
      validators: validators,
      fieldClass: fieldClass,
      editorAttrs: editorAttrs
    });
  };

  /**
   * Output text for a form field's label, taking
   * into account whehter or not the field is required.
   */
  forms.getLabelText = function(s, required) {
    var labelText = s;
    if (required) {
      labelText += " (" + gettext("required") + ")";
    }
    return labelText;
  };
  
  /**
   * A form which groups any fields with a "mutex-group" class under a
   * pill selection menu. The first label in the field becomes the title
   * of the pill. Only supports one such group per form. Assumes 
   * fields are rendered as list items.
   */
  forms.MutexGroupedInputForm = Backbone.Form.extend({
    
    events: {
      'click .nav a': 'handleNavClick'
    },
    activeOption: 0,
    valueStash: {},

    render: function() {
      var result = Backbone.Form.prototype.render.apply(this, arguments);
      var $itemsToGroup = this.$el.find('.mutex-group');
      if ($itemsToGroup.length > 1) {
        var $formItem = $('<li class="mutex-group">').insertBefore($itemsToGroup[0]);
        var $groupContainer = $('<fieldset>').appendTo($formItem);
        var $nav = $('<ul class="nav pills">').appendTo($groupContainer);
        $itemsToGroup.each(function(index) {
          var $originalItem = $(this);
          var typeClass = _.find($originalItem.attr('class').split(' '), function(className) { return (className.indexOf('field-') >= 0); });
          var $navLink = $('<a data-option="' + index + '" href="#"></a>').text($originalItem.find('label').remove().text());
          var $option = $('<div class="option option-' + index + ' '  + (typeClass || '') + '">');
          $nav.append($('<li class="option-' + index + '">').append($navLink));
          $groupContainer.append(
            $option.data('option-index', index).append($originalItem.children())
          );
          $originalItem.remove();
        });
        if ('mutexGroupName' in this.options) {
          $groupContainer.prepend('<legend>' + this.options.mutexGroupName + '</legend>');
        }
        this.showOption(0);
      }
      return result;
    },
    
    showOption: function(index) {
      this.$el.find('.option').hide().filter('.option-' + index).show();
      this.$el.find('.nav li').removeClass('active').filter('.option-' + index).addClass('active');
      this.activeOption = index;
    },
    
    handleNavClick: function(event) {
      var index = $(event.target).data('option');
      this.showOption(index);
      event.preventDefault();
    },
    
    clearInactiveOptions: function(event) {
      this.$el.find('.mutex-group .option')
        .not('.option-' + this.activeOption)
          .find(':input')
            .val('');
    },
    
    stashOptions: function() {
      var view = this;
      this.$el.find('.mutex-group .option :input').each(function() {
        view.valueStash[$(this).attr('name')] = $(this).val();
      });
    },
    
    /**
     * Note that security restrictions forbid setting a file input 
     * programmatically.
     */
    restoreOptions: function() {
      for (var name in this.valueStash) {
        this.$el.find('.mutex-group .option :input[name="' + name + '"]')
          .not('[type="file"]') // avoid security exception
          .val(this.valueStash[name]);
      }
      this.valueStash = {};
    },
    
    /**
     * Override to clear hidden input values before submission. If 
     * client-side validation fails, restore the hidden values before
     * continuing.
     */
    validate: function() {
      this.stashOptions();
      this.clearInactiveOptions();
      var result = Backbone.Form.prototype.validate.apply(this, arguments);
      // result will be non-null in the case of validation failure
      if (result) {
        this.restoreOptions();
      }
      return result;
    }
  });

  var RichTextEditor = forms.RichTextEditor = wysihtml5.Editor.extend({
    /*
     * Create a rich text editor bound to a textarea. 
     *
     * Currently uses the wysihtml5 editor
     *
     * @param {Object} el textarea element to which the rich text editor will be bound
     * @param {Object} [callbacks] Callback functions that will be
     *   bound to events fired by the editor
     * @param {Object} [options] Options for configuring the editor.
     *   Options not listed below will be passed on to the
     *   constructor for wysihtml5.Editor.
     * @param {boolean} [options.grow=false} - Automatically expand the
     *   editor's height to fit the content.
     * @param {boolean} [options.toggleToolbar=true} - Hide the toolbar when
     *   leaving the editor.
     */
    constructor: function(el, callbacks, options) {
      var opts;
      var defaults = {
        grow: false,
        toggleToolbar: true
      };
      var customOpts = _.defaults({}, defaults);
      // Note that the editor currently does not publish a change
      // event that fires on every *visible* change in the editor. :(
      var defaultCallbacks = {};

      opts = options ? _.clone(options) : {};
      // Remove our options, so we can pass the remaining options to the
      // constructor of wysihtml5.Editor
      _.each(defaults, function(val, key) {
        if (!_.isUndefined(opts[key])) {
          customOpts[key] = opts[key];
          delete opts[key];
        }
      });

      if (_.isUndefined(opts.toolbar)) {
        opts.toolbar = this._createEditorToolbarEl();
        $(el).before(opts.toolbar);
      }

      if (customOpts.toggleToolbar) {
        _.extend(defaultCallbacks, this._toggleToolbarCallbacks);
      }

      wysihtml5.Editor.call(this,
        el,    
        _.defaults(opts, {
          parserRules: wysihtml5ParserRules
        })
      );
      // Create a shortcut for the toolbar element
      this.$toolbar = $(opts.toolbar);
      callbacks = _.isUndefined(callbacks) ? {} : callbacks;
      _.defaults(callbacks, defaultCallbacks);
      _.each(callbacks, function(value, key, list) {
        this.on(key, value);
      }, this);

      if (customOpts.grow) {
        this._initEditorGrowth();
      }
    },

    _toolbarTemplateSource: $('#editor-toolbar-template').html(),

    _createEditorToolbarEl: function() {
      return $(this._toolbarTemplateSource)[0]; 
    }, 

    _toggleToolbarCallbacks: {
      'focus': function() {
         this.$toolbar.show();
      },

      'blur': function() {
        if (this._okToHideToolbar) {
          this.$toolbar.hide();
        }
      },

      'load': function() {
        var editor = this;
        this._okToHideToolbar = true;
        this.$toolbar.hide();
        this.$toolbar.mouseover(function() {
          editor._okToHideToolbar = false;
        });
        this.$toolbar.mouseout(function() {
          editor._okToHideToolbar = true;
        });
      }
    },

    /**
     * Initialize event listeners that cause editor to automatically grow
     * with its contents
     *
     */
    _initEditorGrowth: function() {
      this.on('load', function() {
        $(this.composer.element).css('overflow-y', 'hidden');
        this._growEditor();
      });
      this.on('newword:composer', function() {
        this._growEditor();
      });
    },

    /**
     * Expand the wysihtml5.Editor iframe to
     * be taller than its contents.
     *
     */
     _growEditor: function() {
       var $iframe = $(this.composer.iframe);
       var $el = $(this.composer.element);
       var height = $el.height();
       var extraHeight = 40;
       var newHeight = height + extraHeight;
       if ($iframe.height() < height) {
          $iframe.height(newHeight);
          // HACK: WYSIHTML5, when initialized, copies styles from the
          // textarea to two DOM elements. It then restores the styles
          // from these elements on focus/blur. We need to update the
          // height of these elements as well, otherwise the height will
          // jump back to the original value when the editor loses/regains
          // focus
          $(this.composer.blurStylesHost).height(newHeight);
          $(this.composer.focusStylesHost).height(newHeight);
        }
    }
  });
  
})($, _, Backbone, wysihtml5, storybase);
