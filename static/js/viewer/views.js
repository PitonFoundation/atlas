/**
 * Views for the story viewer Backbone application
 */
Namespace('storybase.viewer');

storybase.viewer.views.ViewerApp = Backbone.View.extend({
  events: {
  },

  initialize: function() {
    this.navigationView = new storybase.viewer.views.StoryNavigation(); 
    this.headerView = new storybase.viewer.views.StoryHeader();
    this.sections = this.options.sections;
    this.story = this.options.story;
    this.setSection(this.sections.at(0));
  },

  render: function() {
    this.$('footer').append(this.navigationView.el);
    this.navigationView.render();
    return this;
  },

  updateSubviewSections: function() {
    this.navigationView.setSection(this.currentSection);
    this.headerView.setSection(this.currentSection);
  },

  setSection: function(section) {
    this.currentSection = section;
    this.updateSubviewSections();
  },

  setSectionById: function(id) {
    this.setSection(this.sections.get(id));
  },
});

storybase.viewer.views.SpiderViewerApp = storybase.viewer.views

storybase.viewer.views.StoryHeader = Backbone.View.extend({
  el: 'header',

  render: function() {
    var $titleEl = this.$el.find('.section-title').first();
    if ($titleEl.length == 0) {
      $titleEl = $('<h2 class="section-title">');
      this.$el.append($titleEl);
    }
    $titleEl.text(this.section.get('title'));
    return this;
  },

  setSection: function(section) {
    this.section = section;
    this.render();
  }
});

storybase.viewer.views.StoryNavigation = Backbone.View.extend({
  tagName: 'nav',

  className: 'story-nav',

  render: function() {
    var nextSection = this.section.collection.get(
      this.section.get('next_section_id'));
    var prevSection = this.section.collection.get(
      this.section.get('previous_section_id'));
    this.$el.html(ich.navigationTemplate({
      next_section: nextSection,
      previous_section: prevSection
    }));
    return this;
  },

  setSection: function(section) {
    this.section = section;
    this.render();
  }
});

storybase.viewer.views.Spider = Backbone.View.extend({
  initialize: function() {
    this.sections = this.options.sections;
  },

  render: function() {
    var elId = this.$el.attr('id');
    var width = this.$el.width(); 
    var height = this.$el.height(); 
    var vis = d3.select("#" + elId).insert("svg", "section")
        .attr("width", width)
        .attr("height", height)
      .append("g")
      .attr("transform", "translate(40, 100)");
    var rootSection = this.sections.at(0).populateChildren();
    var tree = d3.layout.tree().size([300, 150]);
    var diagonal = d3.svg.diagonal();
    var nodes = tree.nodes(rootSection);
    var links = tree.links(nodes);

    var link = vis.selectAll("path.link")
        .data(links)
      .enter().append("path")
        .attr("class", "link")
        .attr("d", diagonal);

    var node = vis.selectAll("g.node")
      .data(nodes)
      .enter().append("g")
      .attr("class", "node")
      .attr("transform",function(d) { return "translate(" + d.x + "," + d.y + ")"; });

    node.append("circle")
        .attr("r", 10);

    node.append("text")
      .attr("dx", function(d) { return d.children ? -20 : 20; })
      .attr("dy", 3)
      .attr("text-anchor", function(d) { return d.children ? "end" : "start"; }) 
      .text(function(d) { return d.get('title'); })

  }
});

storybase.viewer.views.SpiderViewerApp = storybase.viewer.views.ViewerApp.extend({
  initialize: function() {
    this.navigationView = new storybase.viewer.views.StoryNavigation(); 
    this.headerView = new storybase.viewer.views.StoryHeader();
    this.initialView = new storybase.viewer.views.Spider({
      el: this.$('#body'),
      sections: this.options.sections
    });
    this.sections = this.options.sections;
    this.story = this.options.story;
    this.setSection(this.sections.at(0));
  },

  render: function() {
    this.$('footer').append(this.navigationView.el);
    this.navigationView.render();
    this.initialView.render();
    return this;
  }

});

storybase.viewer.views.getViewerApp = function(structureType, options) {
  if (structureType == 'linear') {
    return new storybase.viewer.views.ViewerApp(options);
  }
  else if (structureType == 'spider') {
    return new storybase.viewer.views.SpiderViewerApp(options);
  }
  else {
    throw "Unknown story structure type '" + structureType + "'";
  }
};
