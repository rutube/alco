(function($, _, Backbone) {
    /* models */
    var LogModel = Backbone.Model.extend({
	    toJSON: function () {
		    var result = Backbone.Model.prototype.toJSON.apply(this);
		    result['time'] = this.time();
		    result['shortHost'] = this.shortHost();
		    result['level'] = this.level();
		    return result;
	    },
	    level: function() {
		    return this.get('js').levelname;
	    },
	    time: function () {
		    return this.get('datetime').split('T')[1].replace('000', '');
	    },
	    shortHost: function() {
		    return (this.get('js').host || '').split('.')[0]
	    }
    });

    /* collections */
    var LogCollection = Backbone.Collection.extend({
        model: LogModel,
        url: '/api/grep/',

        initialize: function(queryParams) {
            this.page = 1;
            this.logger_index = queryParams['logger_index'] || 'logger';
	        delete queryParams['logger_index'];
	        this.url += this.logger_index + '/';
            this.has_next = true;
            this.loading = false;
            this.queryParams = queryParams || {};
        },

        parse: function(resp) {
            this.has_next = resp.next || false;
            return resp.results;
        },

	    reset: function(models, options) {
		    Backbone.Collection.prototype.reset.apply(this, [models, options]);
		    this.has_next = true;
		    this.page = 1;
	    },

        loadMore: function() {
            if (this.loading || !this.has_next) {
                return false;
            }


	        var params = {
                'page': this.page
            };
            _.extend(params, this.queryParams);

            this.loading = true;
            this.page += 1;

            var res = this.fetch({
                data: this.queryParams
            });
            $.when(res).then(_.bind(function(e, x, y) {
                this.loading = false;
	            this.trigger("loaded");
            }, this));
            return res;
        },
        getUrl: function() {
            return this.url + '?' + $.param(this.queryParams, 'page');
        }
    });


    /* views */
    var LogView = Backbone.View.extend({
        tagName: 'div',
        className: 'log-line',

        template: _.template($('#log-template').html()),

        initialize: function() {
            this.listenTo(this.model, 'change', this.render);
        },

        render: function() {
            this.$el.html(this.template(this.model.toJSON()));
            return this;
        }
    });

    var GrepView = Backbone.View.extend({
        itemView: LogView,

	    events: {
		    "submit #search-form": "submitSearch",
		    "click .filter-trigger": "triggerFilter",
		    "click .column-trigger": "triggerColumn"
	    },

	    el: "#grep-view",
	    container: "#log-container",
	    triggerStates: {},
	    columns: [],

	    countTriggers: function () {
		    var states = {};
		    $(".filter-trigger").each(function(){
			    var e = $(this);
			    var field = e.attr('data-field');
			    if(!states[field]) {
				    states[field] = {active: 0, inactive: 0}
			    }
			    states[field]['active']++;

		    });

		    return states;
	    },
	    initialize: function() {
            this.listenTo(this.collection, "add", this.appendItem);
            this.listenTo(this.collection, "loaded", this.checkScroll);
            this.listenTo(this.collection, "update", this.appendPageNumber);
			this.container = $(this.container);
	        this.triggerStates = this.countTriggers();
		    this.collectColumns();
	        // prevent of query duplicating on scroll
            $(window).scroll(_.bind(this.checkScroll, this));
        },

	    updateLocation: function () {
		    var viewUrl = this.collection.getUrl().replace('api/', '');
		    if (this.columns){
			    var sep = (_.keys(this.collection.queryParams).length > 0)?'&':'';
			    viewUrl += sep + 'columns=' + this.columns.join(',');
		    }
		    window.history.pushState(null, null, viewUrl);
	    },
	    reloadCollection: function () {
		    this.collection.reset();
		    this.container.html('');
		    this.updateLocation();
		    this.collection.loadMore();
	    },

	    submitSearch: function(e) {
		    e.preventDefault();
		    this.collection.queryParams['search'] = $('#search-text').val();
		    this.reloadCollection();
	    },

	    triggerState: function(field, values) {
		    var states = this.triggerStates[field];
		    if (!values)
		        return states;
		    this.triggerStates[field] = states = values;
		    return states;
	    },

	    colorizeTrigger: function(elem, active) {
		    elem.attr('data-active', active + '');
		    elem.toggleClass('label-default', !active);
		    elem.toggleClass('label-success', active);
	    },

	    collectColumns: function () {
		    var columns = [];
		    var isActive = this.isActive;
		    $(".column-trigger").each(function () {
			    var elem = $(this);
			    if (isActive(elem)) {
				    var field = elem.data('value');
				    columns.push(field);
			    }
		    });
		    this.columns = columns;
	    },
	    triggerColumn: function(e) {
		    e.preventDefault();
		    var btn = $(e.target);
		    var field = btn.data('value');
		    var active = !this.isActive(btn);
		    this.colorizeTrigger(btn, active);
		    $(".column.column-"+field).toggle(active);
		    this.collectColumns();
		    this.updateLocation()
	    },
		isActive: function(e) {
		    return (e.attr('data-active') || "false") == 'true';
	    },
	    triggerFilter: function(e) {
            e.preventDefault();
		    var btn = $(e.target);
		    var field = btn.data('field');
		    var value = btn.data('value');
		    var state = this.triggerState(field);
		    var activeCount = state['active'];
		    var inactiveCount = state['inactive'];
		    var active = this.isActive(btn);
			var allItems = $('.filter-trigger[data-field="' + field  + '"]');

		    if (!window.event.ctrlKey) {
			    // leave only one selected item.
			    var total = activeCount + inactiveCount;
			    this.triggerState(field, {
				    active: 1,
				    inactive: total - 1
			    });
			    this.colorizeTrigger(allItems, false);
			    this.colorizeTrigger(btn, true)
		    } else {
			    // Ctrl+Click handler
			    if (active && activeCount == 1) {
				    // Was single active, become inactive
				    // All values are unselected now -that is meaningless.
				    // Activate all items.
				    this.triggerState(field, {
					    active: total,
					    inactive: 0
				    });
				    this.colorizeTrigger(allItems, true);
			    } else {

				    var d = (active)? 1: -1;
			        this.triggerState(field, {
				        active: activeCount - d,
			            inactive: inactiveCount + d
			        });
				    // Just toggle clicked value
				    this.colorizeTrigger(btn, !active);
			    }
		    }
		    // collect all filter values
			var filter = [];
		    var isActive = this.isActive;
		    if (this.triggerState(field).inactive != 0) {
			    allItems.each(function () {
				    var e = $(this);
				    if (!isActive(e))
					    return;
				    filter.push(e.data('value'));
			    });
		    }

            delete this.collection.queryParams[field + '__in'];
		    delete this.collection.queryParams[field];

		    if (filter.length > 1) {
			    this.collection.queryParams[field + '__in'] = filter.join(',');
		    } else if (filter.length == 1 ) {
		        this.collection.queryParams[field] = filter[0];
		    }
            this.reloadCollection();
	    },
        checkScroll: function() {
            var contentOffset = this.container.offset().top,
                contentHeight = this.container.height(),
                pageHeight = $(window).height(),
                scrollTop = $(window).scrollTop();
            var triggerPoint = 200;

            if (contentOffset + contentHeight - scrollTop - pageHeight < triggerPoint) {
                this.collection.loadMore();
            }
        },

        appendItem: function(item) {
            var itemView = new this.itemView({
                model: item
            });
            this.container.append(itemView.render().el);
        },

        appendPageNumber: function() {
            var p = this.collection.page - 1;
            this.$el.append(p + '<hr>');
        },

        render: function() {
            // FIXME
            return this;
        },

        remove: function() {
            Backbone.View.prototype.remove.apply(this, arguments);

            // disable scroll events subscription
            $(window).off('scroll');
        }

    });

    /* routers */
    var LogsRouter = Backbone.Router.extend({

        routes: {
            'grep/:logger_index/': 'grep'
        },

	    parseQueryString: function parseQueryString(queryString){
		    var params = {};
		    if(queryString){
		        _.each(
		            _.map(decodeURI(queryString).split(/&/g),function(el,i){
		                var aux = el.split('='), o = {};
		                if(aux.length >= 1){
		                    var val = undefined;
		                    if(aux.length == 2)
		                        val = aux[1];
		                    o[aux[0]] = val;
		                }
		                return o;
		            }),
		            function(o){
		                _.extend(params,o);
		            }
		        );
		    }
		    return params;
		},

        grep: function(logger_index) {
			var query_string = window.location.search.substring(1);
            if (this.view) {
                this.view.remove();
            }

            var filters = {
                logger_index: logger_index
            };

	        _.extend(filters, this.parseQueryString(query_string));
			delete filters['columns'];
            var collection = new LogCollection(filters);
            this.view = new GrepView({
                collection: collection
            });
            $('#log-container').html(''); //xxx

            collection.loadMore(); // get first page
        }
    });


    var router = new LogsRouter();
    Backbone.history.start({pushState: true});

})($, _, Backbone);