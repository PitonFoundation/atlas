/* Models shared across multiple storybase apps */
;(function(_, Backbone, storybase) {
  if (_.isUndefined(storybase.collections)) {
    storybase.collections = {};
  }
  var Collections = storybase.collections;

  if (_.isUndefined(storybase.models)) {
    storybase.models = {};
  }
  var Models = storybase.models;

  var Forms = storybase.forms;
  var makeRequired;
  if (Forms) {
    makeRequired = Forms.makeRequired;
  }

  /**
   * Mixin that expects the model attributes to be within an objects attribute
   * 
   * This is the way Tastypie structures its response the objects.
   */
  var TastypieCollectionMixin = Collections.TastypieMixin = {
    parse: function(response) {
      return response.objects;
    }
  };

  var TastypieModelMixin = Models.TastypieMixin = {
    url: function() {
      // Ensure data always ends in a '/', for Tastypie
      var url = Backbone.Model.prototype.url.call(this); 
      url = url + (url.charAt(url.length - 1) == '/' ? '' : '/'); 
      return url;
    }
  };

  /**
   * Collection that has an additional save method.
   *
   * This method uses a PUT request to replace entire server-side collection
   * with the models in the Backbone collection.
   */
  var SaveableCollection = Collections.SaveableCollection = Backbone.Collection.extend({
    save: function(options) {
      // TODO: Test this 
      options = options ? _.clone(options) : {};
      var collection = this;
      var success = options.success;
      options.success = function(collection, resp, options) {
        collection.reset(collection.parse(resp, options), options);
        if (success) success(collection, resp);
      };
      return (this.sync || Backbone.sync).call(this, 'update', this, options);
    }
  });

  /**
   * Model that can sync a file attribute to the server as multipart form data.
   */
  var FileUploadModel = Models.FileUploadModel = Backbone.Model.extend({
    // List if model attributes that can take uploaded files
    fileAttributes: [],

    /**
     * Return a FormData object corresponding to the model's
     * attributes
     */
    toFormData: function(options) {
      var attrs = options.attrs || this.attributes;
      var formData = new FormData();
      _.each(attrs, function(value, key) {
        // Only add non-null values as it seems like Firefox
        // encodes null values as strings with a value of 'null',
        // confusing the server-side code
        if (!_.isNull(value)) {
          formData.append(key, value); 
        }
      }, this);
      return formData;
    },

    /**
     * Custom implementation of Backbone.Model.sync that sends
     * file attributes to the server as multipart form data
     * in a hidden IFRAME.
     *
     * This is for browsers that don't support the FileReader
     * API.
     *
     * It requires the jQuery Iframe Transport to be available. 
     * See http://cmlenz.github.com/jquery-iframe-transport/ 
     */
    syncWithUploadIframe: function(method, model, options) {
      var data; // Attribute data, passed to jQuery.sync

      _.extend(options, {
        iframe: true, // Tell jQuery to use the IFRAME transport
        files: options.form.find(':file'), 
        processData: false,
        dataType: 'json',
        // We can't set the accepts header of the IFRAMEd post,
        // so explicitly ask for the response as JSON.
        url: _.result(model, 'url') + '?format=json&iframe=iframe'
      });

      if (!options.data) {
        data = options.attrs || model.toJSON(options);
        // Remove file attributes from the data
        options.data = _.omit(data, model.fileAttributes);
      }

      return Backbone.sync(method, model, options);
    },

    /**
     * Custom implementation of Backbone.Model.sync that sends
     * file attributes to the server as multipart form data.
     *
     * Additional options:
     *
     * @param {Object} [form] jQuery object for the HTML form element. This is
     *     needed if we have to POST using a hidden IFRAME in older browsers.
     * @param {function} [progressHandler] Handler function for the ``progress``
     *     event of the underlying ``XMLHttpRequest`` object.
     */
    syncWithUpload: function(method, model, options) {
      if (window.FormData && window.FileReader && !options.iframe) {
        if (!options.xhr) {
          // Wire up the upload progress handler if one has been specified
          options.xhr = function() {
            var newXhr = $.ajaxSettings.xhr();
            if (newXhr.upload && options.progressHandler) {
              newXhr.upload.addEventListener('progress', options.progressHandler, false);
            }
            return newXhr;
          };
        }
        if (!options.data) {
          // Convert model attributes to a FormData object
          options.data = model.toFormData(options);
        }

        // Set some defaults for jQuery.ajax to make sure that
        // our multipart form data will get sent correctly.
        // See http://stackoverflow.com/a/5976031
        _.extend(options, {
          cache: false,
          contentType: false,
          processData: false
        });

        return Backbone.sync(method, model, options);
      }
      else {
        // Browser (i.e. IE < 10) doesn't support the FormData interface for
        // XMLHttpRequest. Or IFRAME uploads have been explictely requested.
        // We'll have to upload using a hidden IFRAME
        this.syncWithUploadIframe(method, model, options);
      }
    },

    /**
     * Custom implementation of Backbone.Model.sync that delegates to
     * syncWithFileUpload when a file to be uploaded is present.
     *
     * Additional parameters:
     *
     * @param {Boolean} [upload] Should we attempt to upload files on sync
     * @param {Object} [form] jQuery object for the HTML form element. This is
     *     needed if we have to POST using a hidden IFRAME in older browsers.
     * @param {function} [progressHandler] Handler function for the ``progress``
     *     event of the underlying ``XMLHttpRequest`` object.
     */
    sync: function(method, model, options) {
      if (options.upload) {
        return this.syncWithUpload(method, model, options);
      }
      else {
        return Backbone.sync.apply(this, arguments);
      }
    }
  });


  var DataSet = Models.DataSet = FileUploadModel.extend({
    idAttribute: "dataset_id",

    /**
     * Return the server URL for a model instance.
     *
     * This version always uses the collection's URL if the instance is new,
     * otherwise it uses the value returned by the API.  This is needed
     * because sometimes a collection will have a URL set to fetch a
     * particular story's data sets.  By default, Backbone uses the 
     * collection's URL to build an individual model's URL.  We don't want
     * to do this.
     */
    url: function() {
      var url = Backbone.Model.prototype.url.call(this);
      if (!this.isNew() && this.has('resource_uri')) {
        url = this.get('resource_uri');
      }
      // Make sure the URL ends in a '/'
      url = url + (url.charAt(url.length - 1) == '/' ? '' : '/');
      return url; 
    },

    /**
     * Schema for backbone-forms
     */
    schema: function() {
      if (!_.isUndefined(Forms)) {
        var schema = {
          title: makeRequired({
            type: 'Text'
          }),
          source: {
            type: 'Text'
          },
          url: {
            type: 'Text',
            validators: ['url'],
            fieldClass: 'mutex-group'
          },
          file: {
            type: Forms.File,
            fieldClass: 'mutex-group'
          }
        };

        if (!this.isNew()) {
          // For a saved model, only show the fields that have a value set.
          _.each(['file', 'url'], function(field) {
            var value = this.get(field);
            if (!value) {
              delete schema[field];
            }
          }, this);

          // Mark a standalone URL field as required.  Don't mark the file URL as
          // required because the user doesn't have to specify a new
          // file
          if (schema.url) {
            makeRequired(schema.url);
          }
        }

        return schema;
      }
    },

    /**
     * Validate the model attributes
     *
     * Make sure only one of the content variables is set to a truthy
     * value.
     */
    validate: function(attrs) {
      var contentAttrNames = ['file', 'url'];
      var found = [];
      var msg = gettext("You must specify either the file or url field, but not both");
      var errs = {};

      if (_.isUndefined(attrs.title)) {
        errs.title = gettext("You must specify a title");
      }

      if (attrs.url && attrs.url.length > 200) {
        errs.url = { type: 'url', message: gettext("URL must be 200 characters or less.  You could try using a URL shortener.") };
      }

      _.each(contentAttrNames, function(attrName) {
        if (_.has(attrs, attrName) && attrs[attrName]) {
          found.push(attrName);
        }
      });

      // We allow existing datasets with a file attribute to have a
      // missing file and url attributes, which is the case when updating
      // an existing dataset. Otherwise, one and only one of the fields
      // is required
      if (found.length !== 1 && (this.isNew() || !this.get('file'))) {
        errs.file = { type: 'file', message: msg };
        errs.url = { type: 'url', message: msg };
      }

      if (_.size(errs) > 0) {
        return errs;
      }
    }
  });


  Collections.DataSets = Backbone.Collection.extend( 
    _.extend({}, TastypieCollectionMixin, {
      model: DataSet,

      initialize: function() {
        this._story = null;
        this._asset = null;
      },

      url: function() {
        var url = storybase.API_ROOT + 'datasets/';
        if (this._asset !== null) {
          url = url + 'assets/' + this._asset.id + '/';
        }
        else if (this._story !== null) {
          url = url + 'stories/' + this._story.id + '/';
        }
        return url; 
      },

      /**
       * Specify that this collection represent's a particular asset's
       * dataset.
       */
      setAsset: function(asset) {
        this._asset = asset;
      },

      /**
       * Specify that this collection represent's a particular
       * story's data sets
       */
      setStory: function(story) {
        this._story = story;
      },

      // TODO: Test this method, particularly checking which events are fired on
      // the removed model
      /**
       * Remove a single model from a collection at the server
       *
       * This method is for endpoints that support support removing an
       * item from a collection with a DELETE request to an endpoint like
       * /<collection-url>/<model-id>/.
       */
      removeSync: function(models, options) {
        models = _.isArray(models) ? models.slice() : [models];
        var i, l, index, model, url;
        for (i = 0, l = models.length; i < l; i++) {
          model = models[i]; 
          url = _.result(this, 'url') + model.id + '/';
          this.sync('delete', model, {
            url: url
          });
        }
        return this;
      },

      /**
       * Remove a model (or an array of models) from the collection.
       *
       * Unlike the default ``Collection.remove`` this takes an additional
       * ``sync`` option that, if truthy, will cause the models to be 
       * removed on the server.
       */
      remove: function(models, options) {
        var model = this;
        if (!_.isUndefined(options.sync)) {
          if(_.result(options, 'sync')) {
            this.once('remove', function() {
              model.removeSync(models, options);
            }, this);
          }
        }
        Backbone.Collection.prototype.remove.apply(this, arguments);
      }
    })
  );

  var Location = Models.Location = Backbone.Model.extend({
    idAttribute: 'location_id',

    urlRoot: function() {
      return storybase.API_ROOT + 'locations';
    },

    /**
     * Get the URL for the model.  
     *
     * Unlike the default version, for new models this uses the collection url
     * first, instead of the urlRoot value.
     */
    url: function() {
      var base = _.result(this, 'urlRoot') || _.result(this.collection, 'url') || urlError();
      if (this.isNew()) {
        base = _.result(this.collection, 'url') || _.result(this, 'urlRoot') || urlError();
        return base;
      }
      else {
        base = base + (base.charAt(base.length - 1) == '/' ? '' : '/') + encodeURIComponent(this.id);
      }
      return base + (base.charAt(base.length - 1) == '/' ? '' : '/');
    }
  });

  Collections.Locations = Backbone.Collection.extend(
    _.extend({}, TastypieCollectionMixin, {
      model: Location,

      initialize: function(models, options) {
        this._story = _.isUndefined(options.story) ? null : options.story;
      },

      url: function() {
        var url = storybase.API_ROOT + 'locations/';
        if (this._story) {
          url = url + 'stories/' + this._story.id + '/';
        }
        return url;
      },

      setStory: function(story) {
        this._story = story;
      }
    })
  );

  var Story = Models.Story = Backbone.Model.extend(
    _.extend({}, TastypieModelMixin, {
      idAttribute: "story_id",

      urlRoot: function() {
        return storybase.API_ROOT + 'stories';
      },

      defaults: {
        'title': '',
        'byline': '',
        'summary': '',
        'connected': false,
        'connected_prompt': ''
      },

      initialize: function(options) {
        this.sections = new Sections();
        this.unusedAssets = new Assets();
        this.assets = new Assets();
        this.setCollectionUrls();
        this.on("change", this.setCollectionUrls, this);
        this.sections.on("add", this.resetSectionWeights, this);
      },

      /**
       * Set the url property of collections.
       *
       * This is needed because the URL of the collections are often based
       * on the model id.
       */
      setCollectionUrls: function() {
        if (!this.isNew()) {
          this.sections.url = this.url() + 'sections/';
          this.unusedAssets.url = storybase.API_ROOT + 'assets/stories/' + this.id + '/sections/none/'; 
          this.assets.url = storybase.API_ROOT + 'assets/stories/' + this.id + '/';
        }
      },

      /**
       * Set the featured assets collection.
       */
      setFeaturedAssets: function(collection) {
        this.featuredAssets = collection;
        this.featuredAssets.setStory(this);
        this.trigger('set:featuredassets', this.featuredAssets);
      },

      /**
       * Set the related stories collection.
       */
      setRelatedStories: function(relatedStories) {
        this.relatedStories = relatedStories;
        this.relatedStories.setStory(this);
      },

      /**
       * Re-set the section weights based on their order in the collection 
       */
      resetSectionWeights: function() {
        this.sections.each(function(section, index) {
          section.set('weight', index);
        });
      },

      /**
       * Set the featured asset.
       *
       * This method provides an interface for the actual set operation
       * since it's a little unintuitive.
       */
      setFeaturedAsset: function(asset, options) {
        // The data model supports having multiple featured assets, but
        // our current use case only needs to keep one.
        options = options ? _.clone(options) : {};
        var model = this;
        var success = options.success;
        options.success = function(collection, resp, options) {
          if (success) success(collection, resp, options);
        };
        this.featuredAssets.reset(asset);
        model.trigger("set:featuredasset", asset);
        this.featuredAssets.save(options);
      },

      getFeaturedAsset: function(index) {
        index = _.isUndefined(index) ? 0 : index; 
        if (this.featuredAssets) {
          return this.featuredAssets.at(index);
        }
        else {
          return undefined;
        }
      },

      saveFeaturedAssets: function() {
        if (this.featuredAssets) {
          this.featuredAssets.save();
        }
      },

      saveRelatedStories: function() {
        if (this.relatedStories) {
          this.relatedStories.save();
        }
      },


      /**
       * Save all the sections of the story
       */
      saveSections: function(options) {
        this.sections.each(function(section) {
          section.save();
        });
      },


      /**
       * Copy selected properties from another story.
       *
       * @param {Object} story  Story model instance to use as the template
       *   for this model
       * @param {Object} sectionAttrs Attributes to set on each section
       *   copied from the template story.  These override any attribute copied
       *   from the template.
       */
      fromTemplate: function(story, sectionAttrs) {
        this.set('structure_type', story.get('structure_type'));
        this.set('summary_suggestion', story.get('summary'));
        this.set('call_to_action_suggestion', story.get('call_to_action'));
        this.set('template_story', story.get('story_id'));
                      
        story.sections.each(function(section) {
          var sectionCopy = new Section();
          sectionCopy.set("title_suggestion", section.get("title"));
          sectionCopy.set("title", "");
          sectionCopy.set("layout", section.get("layout"));
          sectionCopy.set("root", section.get("root"));
          sectionCopy.set("weight", section.get("weight"));
          sectionCopy.set("layout_template", section.get("layout_template"));
          sectionCopy.set("template_section", section.get("section_id"));
          sectionCopy.set("help", section.get("help"));
          if (!_.isUndefined(sectionAttrs)) {
            sectionCopy.set(sectionAttrs);
          }
          this.sections.push(sectionCopy);
        }, this);
      },

      /**
       * Get suggestions for some properties of a story from
       * another story.
       *
       * @param {Object} story  Story model instance to use as the template
       *   for this model
       */
      suggestionsFromTemplate: function(story) {
        this.set('summary_suggestion', story.get('summary'));
        this.set('call_to_action_suggestion', story.get('call_to_action'));
        this.sections.each(function(section) {
          var templateSection = story.sections.get(section.get('template_section'));

          if (templateSection) {
            section.set("title_suggestion", templateSection.get("title"));
          }
        }, this);
      },

      /**
       * Confirm that the story has its essential components.
       *
       * Returns nothing if the story has all its components. If it is
       * missing a required component, returns an object with an
       * ``errors`` property, with keys for each missing required
       * component.  If it is missing a reccomended component, the
       * return object will have a ``warnings`` property, with keys
       * for each missing reccomended component.
       */
      validateStory: function() {
        var requiredFields = ['title'];
        var reccomendedFields = ['byline', 'summary'];
        var hasErrors = false;
        var hasWarnings = false;
        var errors = {};
        var warnings = {};
        var response = {};

        _.each(requiredFields, function(fieldName) {
          var value = this.get(fieldName);

          if (_.isUndefined(value) || value === '') {
            // TODO: Decide if a warning should be set instead of a boolean
            errors[fieldName] = true; 
            hasErrors = true;
          }
        }, this);

        _.each(reccomendedFields, function(fieldName) {
          var value = this.get(fieldName);

          if (_.isUndefined(value) || value === '') {
            warnings[fieldName] = true;
            hasWarnings = true;
          }
        }, this);

        if (_.isUndefined(this.getFeaturedAsset())) {
          warnings.featuredAsset = true;
          hasWarnings = true;
        }

        if (hasErrors) {
          response.errors = errors;
        }

        if (hasWarnings) {
          response.warnings = warnings;
        }

        if (hasErrors || hasWarnings) {
          return response;
        }
      }
    })
  );


  Collections.Stories = Backbone.Collection.extend({
      model: Story,

      url: function() {
        return storybase.API_ROOT + 'stories';
      }
  });

  Collections.StorySearchResults = Backbone.Collection.extend({
    model: Story,

    parse: function(response) {
      return response.objects;
    },

    url: function() {
      return storybase.API_ROOT + 'stories/search';
    }
  });

  var Section = Models.Section = Backbone.Model.extend(
    _.extend({}, TastypieModelMixin, {
      idAttribute: "section_id",

      initialize: function() {
        this.assets = new SectionAssets();
        this.assets.setSection(this);
        this.setCollectionUrls();
        this.on("change", this.setCollectionUrls, this);
      },

      populateChildren: function() {
        var $this = this;
        this.children = this.get('children').map(function(childId) {
          return $this.collection.get(childId).populateChildren();
        });
        return this;
      },

      /**
       * Set the url property of collections.
       *
       * This is needed because the URL of the collections are often based
       * on the model id.
       */
      setCollectionUrls: function() {
        if (!this.isNew()) {
          this.assets.url = this.url() + 'assets/';
        }
      },

      title: function() {
        return this.get("title");
      },

      urlRoot: function() {
        return storybase.API_ROOT + 'sections';
      },

      /**
       * Return the server URL for a model instance.
       *
       * This version always tries to use the model instance's collection
       * URL first.
       */
      url: function() {
        var base = _.result(this.collection, 'url') || _.result(this, 'urlRoot') || urlError();
        if (this.isNew()) {
          return base;
        }
        else {
          base = base + (base.charAt(base.length - 1) == '/' ? '' : '/') + encodeURIComponent(this.id);
        }
        return base + (base.charAt(base.length - 1) == '/' ? '' : '/');
      }
    })
  );

  var Sections = Collections.Sections = Backbone.Collection.extend(
    _.extend({}, TastypieCollectionMixin, {
      model: Section,

      url: storybase.API_ROOT + 'sections/',

      initialize: function() {
        _.bindAll(this, '_assetsFetchedSuccess', '_assetsFetchedError');
      },

      sortByIdList: function(idList) {
        var that = this;
        _.each(idList, function(id, index) {
          var section = that.get(id);
          section.set('weight', index);
        });
        this.models = this.sortBy(function(section) {
          var weight = section.get('weight');
          return weight;
        });
      },

      /**
       * Callback for when an individual section's asset is fetched.
       */
      _assetsFetchedSuccess: function(section, assets, response) {
        var callback = this._fetchAssetsSuccess ? this._fetchAssetsSuccess : null;
        this._assetsFetched.push(section.id);  
        if (this._assetsFetched.length == this.length) {
          // All the sections have been fetched!
          this._fetchAssetsCleanup();
          if (callback) {
            callback(this);
          }
        }
      },

      /**
       * Callback for when an individual section's assets failed to be 
       * fetched
       */
      _assetsFetchedError: function(section, assets, response) {
        var callback = this._fetchAssetsError ? this._fetchAssetsError : null;
        this._fetchAssetsCleanup();
        if (callback) {
          callback(this);
        }
      },

      _fetchAssetsCleanup: function() {
        this._assetsFetched = [];
        this._fetchAssetsSuccess = null; 
        this._fetchAssetsError = null; 
      },

      /**
       * Fetch the assets for each section in the collection.
       */
      fetchAssets: function(options) {
        options = options ? options : {};
        this._assetsFetched = [];
        if (options.success) {
          this._fetchAssetsSuccess = options.success;
        }
        if (options.error) {
          this._fetchAssetsError = options.error;
        }
        this.each(function(section) {
          var coll = this;
          var success = function(assets, response) {
            coll._assetsFetchedSuccess(section, assets, response);
          };
          var error = function(assets, response) {
            coll._assetsFetchedError(section, assets, response);
          };
          section.assets.fetch({
            success: success,
            error: error 
          });
        }, this);
      }
    })
  );

  var StoryRelation = Models.StoryRelation = Backbone.Model.extend({
    idAttribute: "relation_id"
  });

  Collections.StoryRelations = SaveableCollection.extend(
    _.extend({}, TastypieCollectionMixin, {
      model: StoryRelation,

      initialize: function(models, options) {
        if (!_.isUndefined(options)) {
          this.setStory(options.story);
        }
      },

      fillTargets: function() {
        this.each(function(rel) {
          if (rel.isNew()) {
            // Unsaved story relation
            if (_.isUndefined(rel.get('target'))) {
              rel.set('target', this._story.id);
            }
          }
        }, this);
      },

      save: function(options) {
        this.fillTargets();
        return SaveableCollection.prototype.save.call(this, options);
      },

      setStory: function(story) {
        this._story = story;
      },

      url: function() {
        return _.result(this._story, 'url') + 'related/';
      }
    })
  );

  /**
   * Utility model for managing relations between sections and assets.
   *
   * This should not be instantiated by calling code.  Generally, this type
   * of model is just used internally by the SectionAssets collection.  If
   * you need an instance, you can retrieve one by calling
   * SectionAssets.getSectionAsset(asset).
   */
  var SectionAsset = Backbone.Model.extend(
    _.extend({}, TastypieModelMixin, {
      /**
       * Constructor.
       *
       * @param attributes {object} attributes Hash of model attributes, as
       *   would be passed to the constructor of Backbone.Model.  However,
       *   certain attributes are preprocessed rather than being set as a
       *   model attribute.  The ``asset`` attribute's url property is set on
       *   the constructed model.  The ``id`` of the model is taken from the 
       *   ``asset`` attributes id property.  The ``attribute`` is
       *   assigned to ``model.section`` instead of being set as a model
       *   attribute.
       */
      constructor: function(attributes, options) {
        var attrs = attributes || {};
        // Preprocess some of the attributes
        if (attrs.asset) {
          // This item's ID will be the same as the asset's ID
          attrs.id = attrs.asset.id;
          // As will the container
          attrs.container = attrs.container || attrs.asset.get('container');
          // Relations in Tastypie use URLs.
          attrs.asset = attrs.asset.url();
        }
        if (attrs.section) {
          // If a section attribute is passed, assign it and
          // remove it from the attributes hash
          this.section = attrs.section;
          delete attrs.section;
        }
        Backbone.Model.call(this, attributes, options);
      },

      urlRoot: function() {
        return this.section.url() + 'assets';
      }
    })
  );


  var Asset = Models.Asset = FileUploadModel.extend(
    _.extend({}, TastypieModelMixin, {
      fileAttributes: ['image'],

      showFormField: {
        url: {
          'image': true,
          'audio': true,
          'video': true,
          'map': true,
          'table': true,
          'chart': true
        },

        image: {
          'image': true,
          'map': true,
          'chart': true
        },

        body: {
          'text': true,
          'quotation': true,
          'map': true,
          'table': true,
          'chart': true
        },

        caption: {
          'image': true,
          'audio': true,
          'video': true,
          'map': true,
          'table': true,
          'chart': true
        },

        attribution: {
          'quotation': true,
          'table': true,
          'chart': true
        },


        source_url: {
          'quotation': true,
          'table': true
        },

        title: {
          'table': true
        }
      },
      
      mutexGroups: {
        image: ['url', 'image'],
        map: ['url', 'image', 'body'],
        chart: ['url', 'image', 'body'],
        table: ['url', 'body']
      },

      formFieldVisible: function(name, type) {
        return _.has(this.showFormField[name], type);
      },

      /**
       * Build the schema for backbone-forms
       *
       * This is done with a function instead of declaring an object because
       * the fields differ depending on the type of asset.
       */
      schema: function() {
        if (!_.isUndefined(Forms)) {
          var schema = {
            title: {title: gettext("Title"), type: 'Text'},
            url: {title: gettext("URL"), type: 'Text', validators: ['url']},
            image: {title: gettext("Image file"), type: Forms.File},
            body: {title: gettext("Body"), type: 'TextArea'},
            caption: {title: gettext("Caption"), type: 'TextArea'},
            attribution: {title: gettext("Attribution"), type: 'TextArea'},
            source_url: {title: gettext("Source URL"), type: 'Text', validators: ['url']}
          };
          var type = this.get('type');
          // Remove fields that aren't relevant for a particular type
          _.each(schema, function(field, name, schema) {
            if (!this.formFieldVisible(name, type)) {
              delete schema[name];
            }
          }, this);
          if (!this.isNew()) {
            // For a saved model, only show the fields that have a value set.
            _.each(['image', 'url', 'body'], function(field) {
              var value = this.get(field);
              if (!value) {
                delete schema[field];
              }
            }, this);
          }
          else {
            // markup groups
            if (_.has(this.mutexGroups, type)) {
              var groups = this.mutexGroups[type];
              _.each(schema, function(def, name) {
                if (_.indexOf(groups, name) >= 0) {
                  def.fieldClass = (('fieldClass' in def) ? def.fieldClass + ' mutex-group' : 'mutex-group');
                }
              });
            }
          }
          return schema;
        }
      },

      idAttribute: "asset_id",

      urlRoot: function() {
        return storybase.API_ROOT + 'assets/';
      },

      /**
       * Validate the model attributes
       *
       * Make sure that only one of the content attributes is set to a truthy
       * value.
       */
      validate: function(attrs, options) {
        var contentAttrNames = ['body', 'image', 'url'];
        var found = [];
        _.each(contentAttrNames, function(attrName) {
          if (_.has(attrs, attrName) && attrs[attrName]) {
            found.push(attrName);
          }
        }, this);
        if (found.length > 1) {
          return "You must specify only one of the following values: " + found.join(', ') + '.';
        }
        else if (found.length === 0 && (this.isNew() || !this.get('image'))) {
          return 'You must specify at least one option: ' + _.intersection(_.keys(attrs), contentAttrNames).join(', ') + '.';
        }
      },

      /**
       * Can this asset type accept related data?
       */
      acceptsData: function() {
        var type = this.get('type');
        if (type === 'map' || type === 'chart' || type === 'table') {
          return true;
        }
        else {
          return false;
        }
      },

      /**
       * Set the asset's datasets collection.
       */
      setDataSets: function(collection) {
        this.datasets = collection;
        this.datasets.setAsset(this);
        this.trigger('set:datasets', this.datasets);
      }
    })
  );

  var Assets = Collections.Assets = Backbone.Collection.extend(
    _.extend({}, TastypieCollectionMixin, {
      model: Asset
    })
  );

  /**
   * Collection for handling Asset models associated with a Section.
   */
  var SectionAssets = Collections.SectionAssets = Assets.extend(
    _.extend({}, {
      initialize: function() {
        // When a model is added or removed from this collection, associate
        // it with a section, optionally persisting this relationship to
        // the server.
        this.on('add', this.setAssetSection, this);
        this.on('remove', this.unsetAssetSection, this);
      },

      parse: function(response) {
        var models = [];
        _.each(response.objects, function(sectionAsset) {
          var asset = sectionAsset.asset;
          asset.container = sectionAsset.container;
          models.push(asset);
        });
        return models;
      },

      /**
       * Set the section associated with this model.
       */
      setSection: function(section) {
        this._section = section;
      },

      /**
       * Get the Section associated with this model.
       */
      getSection: function(section) {
        return this._section;
      },

      /**
       * Disassociate this collection with a Section.
       */
      unsetSection: function() {
        delete this._section;
      },

      /**
       * Associate an asset in the collection with this collection's Section.
       *
       * This is used as a handler for the ``add`` event triggered
       * on this collection. 
       *
       * @param {Asset} asset Asset model.
       * @param {SectionAssets} collection This argument is needed to match
       *   the signature of the ``add`` event. Defaults to the collection
       *   itself.
       * @param {object} [options]
       * @param {string} [options.container] If present, this is set as the
       *   ``container`` attribute on ``asset``.
       * @param {boolean} [options.sync] If truthy, persist the relationship
       *   to the server.
       *
       * Triggers a ``save:sectionasset`` event if the relationship is 
       * successfully persisted to the server, and an ``error:sectionasset``
       * event if there's a problem. Listeners to tese events as well as the 
       * ``success`` and ``error`` callbacks take (asset, response, options)
       * as the arguments.
       *
       * This function delegates to ``updateSectionAsset()`` for most of its
       * heavy lifting. See the documentation for that function for other
       * options and events fired.
       *
       */
      setAssetSection: function(asset, collection, options) {
        collection = collection || this;
        options = options || {};

        if (options.container) {
          asset.set('container', options.container);
        }

        if (options.sync) {
          this.updateSectionAsset(asset, options);
        }
      },

      /**
       * Disassociate an asset in the collection with the collection's Section.
       *
       * This is used as a handler for the ``remove`` event triggered on this
       * collection.
       *
       * @param {Asset} asset Asset model.
       * @param {boolean} [options.sync] If truthy, remove the relationship
       *   to the server.
       * @param {function} [options.success] Callback for a successful request
       *   to the server.
       * @param {function} [options.error] Callback for a successful request
       *   to the server.
       *
       * The success and error callbacks are passed (asset, response, options)
       * as arguments.
       */
      unsetAssetSection: function(asset, collection, options) {
        collection = collection || this;
        options = options || {};

        asset.unset('container');
        
        if (options.sync) {
          var success = options.success;
          var error = options.error;

          this.getSectionAsset(asset).destroy({
            success: function(model, xhr, options) {
              if (success) {
                success(asset, xhr, options);
              }

              collection.trigger('remove:sectionasset', asset, xhr, options);
            },
            error: function(model, xhr, options) {
              if (error) {
                error(asset, xhr, options);
              }

              collection.trigger('error:sectionasset', asset, xhr, options); 
            }
          });
        }
      },

      /**
       * Returns a SectionAsset instance for the given asset and container.
       */
      getSectionAsset: function(asset, container) {
        return new SectionAsset({
          section: this.getSection(),
          asset: asset,
          container: container
        });
      },

      /**
       * Create or update the relationship between an asset in the collection,
       * with this collection's Section.
       *
       * @param {Asset} asset Asset model.
       * @param {object} [options]
       * @param {function} [options.success] Callback for a successful request
       *   to the server.
       * @param {function} [options.error] Callback for a successful request
       *   to the server.
       *
       * Triggers a ``save:sectionasset`` event if the relationship is 
       * successfully persisted to the server, and an ``error:sectionasset``
       * event if there's a problem. Listeners to tese events as well as the 
       * ``success`` and ``error`` callbacks take (asset, response, options)
       * as the arguments.
       *
       */
      updateSectionAsset: function(asset, options) {
        var collection = this;
        options = options || {};
        var success = options.success;
        var error = options.error;

        this.getSectionAsset(asset).save(null, {
          success: function(sectionAsset, xhr, options) {
            if (success) {
              success(asset, xhr, options);
            }

            collection.trigger('save:sectionasset', asset, xhr, options);
          },

          error: function(sectionAsset, xhr, options) {
            if (error) {
              error(asset, xhr, options);
            }

            collection.trigger('error:sectionasset', asset, xhr, options); 
          }
        });
      }
    })
  );

  Collections.FeaturedAssets = SaveableCollection.extend(
    _.extend({}, TastypieCollectionMixin, {
      model: Asset,

      initialize: function(models, options) {
        if (!_.isUndefined(options)) {
          this.setStory(options.story);
        }
      },

      save: function(options) {
        return SaveableCollection.prototype.save.call(this, options);
      },

      setStory: function(story) {
        this._story = story;
      },

      url: function() {
        return storybase.API_ROOT + 'assets/stories/' + this._story.id + '/featured/';
      }
    })
  );

  var Tag = Models.Tag = Backbone.Model.extend({
    idAttribute: "tag_id",

    /**
     * Check whether the model has been saved to the server.
     *
     * This version checks for a resource_uri attribute instead of
     * Backbone's default behavior, which is to check for a non-null id.
     * This is needed because of the API semantics which associate a new
     * tag with a story by POSTing to /API_ROOT/tags/stories/STORY_ID/
     * with a payload that includes a tag_id property. It makes sense to
     * do this with Backbone.Collection.create, but setting tag_id (this
     * model's idAttribute) causes the default isNew implementation to
     * think the model already exists and do a PUT request to the 
     * wrong url.
     */
    isNew: function() {
      return _.isUndefined(this.get('resource_uri'));
    }
  });

  Collections.Tags = Backbone.Collection.extend(
    _.extend({}, TastypieCollectionMixin, {
      model: Tag,

      initialize: function(models, options) {
        this._story = _.isUndefined(options.story) ? null : options.story;
      },

      url: function() {
        var url = storybase.API_ROOT + 'tags/';
        if (this._story) {
          url = url + 'stories/' + this._story.id + '/';
        }
        return url;
      },

      setStory: function(story) {
        this._story = story;
      }
    })
  );
})(_, Backbone, storybase);
