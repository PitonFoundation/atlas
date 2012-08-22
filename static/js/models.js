/* Models shared across multiple storybase apps */
Namespace('storybase.globals');
Namespace('storybase.models');
Namespace('storybase.collections');

/**
 * Mixin that expects the model attributes to be within an objects attribute
 * 
 * This is the way Tastypie structures its response the objects.
 */
storybase.collections.TastypieMixin = {
  parse: function(response) {
    return response.objects;
  }
}

storybase.models.TastypieMixin = {
  url: function() {
    // Ensure data always ends in a '/', for Tastypie
    var url = Backbone.Model.prototype.url.call(this); 
    url = url + (url.charAt(url.length - 1) == '/' ? '' : '/'); 
    return url;
  }
}

storybase.models.DataSet = Backbone.Model.extend({
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
      if (!_.isUndefined(storybase.forms)) {
        var schema = {
          title: {type: 'Text', validators: ['required']},
          source: {type: 'Text', validators: []},
          url: {type: 'Text', validators: ['url']},
          file: {type: storybase.forms.File}
        };
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
      _.each(contentAttrNames, function(attrName) {
        if (_.has(attrs, attrName) && attrs[attrName]) {
          found.push(attrName);
        }
      });
      if (found.length > 1) {
        // TODO: Translate this
        return "You must specify only one of the following values " + found.join(', ');
      }
    }
});


storybase.collections.DataSets = Backbone.Collection.extend( 
  _.extend({}, storybase.collections.TastypieMixin, {
    model: storybase.models.DataSet,

    initialize: function() {
      this._story = null;
    },

    url: function() {
      var url = storybase.globals.API_ROOT + 'datasets/';
      if (this._story !== null) {
        url = url + 'stories/' + this._story.id + '/';
      }
      return url; 
    },

    /**
     * Specify that this collection represent's a particular
     * story's data sets
     */
    setStory: function(story) {
      this._story = story;
    }
  })
);

storybase.models.Location = Backbone.Model.extend({
  idAttribute: 'location_id',

  urlRoot: function() {
    return storybase.globals.API_ROOT + 'locations';
  },

  /**
   * Get the URL for the model.  
   *
   * Unlike the default version, for new models this uses the collection url
   * first, instead of the urlRoot value.
   */
  url: function() {
    var base = getValue(this, 'urlRoot') || getValue(this.collection, 'url') || urlError();
    if (this.isNew()) {
      base = getValue(this.collection, 'url') || getValue(this, 'urlRoot') || urlError();
      return base;
    }
    else {
      base = base + (base.charAt(base.length - 1) == '/' ? '' : '/') + encodeURIComponent(this.id);
    }
    return base + (base.charAt(base.length - 1) == '/' ? '' : '/');
  }
});

storybase.collections.Locations = Backbone.Collection.extend(
  _.extend({}, storybase.collections.TastypieMixin, {
    model: storybase.models.Location,

    initialize: function(models, options) {
      this._story = _.isUndefined(options.story) ? null : options.story;
    },

    url: function() {
      var url = storybase.globals.API_ROOT + 'locations/';
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

storybase.models.Story = Backbone.Model.extend(
  _.extend({}, storybase.models.TastypieMixin, {
    idAttribute: "story_id",

    urlRoot: function() {
      return storybase.globals.API_ROOT + 'stories';
    },

    defaults: {
      'title': '',
      'byline': '',
      'summary': ''
    },

    initialize: function(options) {
      this.sections = new storybase.collections.Sections;
      this.unusedAssets = new storybase.collections.Assets;
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
        this.unusedAssets.url = storybase.globals.API_ROOT + 'assets/stories/' + this.id + '/sections/none/'; 
      }
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
     * Save all the sections of the story
     */
    saveSections: function(options) {
      this.sections.each(function(section) {
        section.save();
      });
    }
  })
);


storybase.collections.Stories = Backbone.Collection.extend({
    model: storybase.models.Story,

    url: function() {
      return storybase.globals.API_ROOT + 'stories';
    }
});

storybase.models.Section = Backbone.Model.extend(
  _.extend({}, storybase.models.TastypieMixin, {
    idAttribute: "section_id",

    populateChildren: function() {
      var $this = this;
      this.children = this.get('children').map(function(childId) {
        return $this.collection.get(childId).populateChildren();
      });
      return this;
    },

    title: function() {
      return this.get("title");
    }
  })
);

storybase.collections.Sections = Backbone.Collection.extend(
  _.extend({}, storybase.collections.TastypieMixin, {
    model: storybase.models.Section,

    url: storybase.globals.API_ROOT + 'sections/',

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
  })
);

storybase.models.Asset = Backbone.Model.extend(
  _.extend({}, storybase.models.TastypieMixin, {
    showFormField: {
      url: {
        'image': true,
        'audio': true,
        'video': true,
        'map': true,
        'table': true,
      },

      image: {
        'image': true,
        'map': true
      },

      body: {
        'text': true,
        'quotation': true,
        'map': true,
        'table': true,
      },

      caption: {
        'image': true,
        'audio': true,
        'video': true,
        'map': true,
        'table': true,
      },

      attribution: {
        'quotation': true,
        'table': true
      },


      source_url: {
        'quotation': true,
        'table': true
      },

      title: {
        'table': true
      }
    },

    formFieldVisible: function(name, type) {
      return _.has(this.showFormField[name], type);
    },

    /**
     * Build the schema for backbone-forms
     *
     * This is done witha function instead of declaring an object because
     * the fields differ depending on the type of asset.
     */
    schema: function() {
      if (!_.isUndefined(storybase.forms)) {
        var schema = {
          title: {title: gettext("Title"), type: 'Text'},
          url: {title: gettext("URL"), type: 'Text', validators: ['url']},
          image: {title: gettext("Image file"), type: storybase.forms.File},
          body: {title: gettext("Body"), type: 'TextArea'},
          //caption: {title: gettext("Caption"), type: 'TextArea'},
          attribution: {title: gettext("Attribution"), type: 'TextArea'},
          source_url: {title: gettext("Source URL"), type: 'Text', validators: ['url']}
        };
        var type = this.get('type');
        var self = this;
        // Remove fields that aren't relevant for a particular type
        _.each(schema, function(field, name, schema) {
          if (!this.formFieldVisible(name, type)) {
            delete schema[name];
          }
        }, this);
        if (!this.isNew()) {
          // For a saved model, only show the fields that have a value set.
          _.each(['image', 'url', 'body'], function(field) {
            var value = self.get(field);
            if (!value) {
              delete schema[field];
            }
          });
        }

        return schema;
      }
    },

    idAttribute: "asset_id",

    urlRoot: function() {
      return storybase.globals.API_ROOT + 'assets/'
    },

    /**
     * Validate the model attributes
     *
     * Make sure that only one of the content attributes is set to a truthy
     * value.
     */
    validate: function(attrs) {
      var contentAttrNames = ['body', 'image', 'url'];
      var found = [];
      _.each(contentAttrNames, function(attrName) {
        if (_.has(attrs, attrName) && attrs[attrName]) {
          found.push(attrName);
        }
      });
      if (found.length > 1) {
        return "You must specify only one of the following values " + found.join(', ');
      }
    }
  })
);

storybase.collections.Assets = Backbone.Collection.extend(
  _.extend({}, storybase.collections.TastypieMixin, {
    model: storybase.models.Asset
  })
);

storybase.collections.SectionAssets = storybase.collections.Assets.extend({
  parse: function(response) {
    var models = [];
    _.each(response.objects, function(sectionAsset) {
      var asset = sectionAsset.asset;
      asset.container = sectionAsset.container;
      models.push(asset);
    });
    return models;
  }
});

storybase.models.Tag = Backbone.Model.extend({
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

storybase.collections.Tags = Backbone.Collection.extend(
  _.extend({}, storybase.collections.TastypieMixin, {
    model: storybase.models.Tag,

    initialize: function(models, options) {
      this._story = _.isUndefined(options.story) ? null : options.story;
    },

    url: function() {
      var url = storybase.globals.API_ROOT + 'tags/';
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
