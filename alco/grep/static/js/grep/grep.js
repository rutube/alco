(function($, _, Backbone) {

	/* helpers */

	var colorizeTrigger = function(elem, active) {
	    elem.attr('data-active', active + '');
	    elem.toggleClass('label-default', !active);
	    elem.toggleClass('label-success', active);
    };


	var filterEvents = _.extend({}, Backbone.Events);

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
		    return this.get('js')['levelname'];
	    },
	    time: function () {
		    return this.get('datetime').split('T')[1].replace('000', '');
	    },
	    shortHost: function() {
		    return (this.get('js').host || '').split('.')[0]
	    }
    });

	var ColumnModel = Backbone.Model.extend({
		defaults: {
            name: null,
            visible: true
	    }
	});

	var DateModel = Backbone.Model.extend({
		defaults: {
            date: null,
            active: true
	    }
	});

	var FilterModel = Backbone.Model.extend({
		defaults: {
            name: null,
            values: true
	    }

	});

	var ValueModel = Backbone.Model.extend({
		defaults: {
			value: null,
			selected: true
		}
	});

    /* collections */

    var ColumnCollection = Backbone.Collection.extend({
	    model: ColumnModel,
	    isVisible: function (model) {
		    return model.get('visible')
	    },
	    updateActiveState: function (model) {
		    var seen = false;
		    if (this.filter(this.isVisible).length == 0){
			    for (var i=0; i<this.models.length; i++) {
				    var cur = this.models[i];
				    cur.set({'visible': true});
			    }
		    }
		    filterEvents.trigger('filter-changed', 'columns');
	    },
	    initialize: function (models, options) {
		    var params = (options|| {}).queryParams || {};
		    var columns = params.columns;
		    if (columns)
			    columns = columns.split(',');

		    for (var i=0; i<models.length; i++){
			    var m = models[i];
			    m.on('column-visible-changed', this.updateActiveState, this);
			    if (columns)
				    m.set('visible', _.contains(columns, m.get('name')));
		    }
	    },

	    getFilterParams: function() {
			var visible = this.filter(this.isVisible);
			if (visible.length == 0)
				visible = this.models;
		    return {columns: visible.map(function(model) {
					return model.get('name')
				}).join(',')}
		}
    });

    var DateCollection = Backbone.Collection.extend({
	    model: DateModel,
	    updateActiveState: function (model) {
		    var seen = false;
		    for (var i=0; i<this.models.length; i++) {
			    var cur = this.models[i];
			    if (cur.get('date') == model.get('date')) {
				    seen = true;
			    }
			    if (i < this.models.length - 1)
			        cur.set({'active': seen});
			    else
			        cur.set({'active': true});
		    }
		    filterEvents.trigger('filter-changed', 'dates');
	    },

	    initialize: function (models, options) {
		    var params = (options|| {}).queryParams || {};
		    var start_ts = params.start_ts;
		    var date = null;
		    if (start_ts) {
			    date = start_ts.split(' ')[0]
		    }
		    for (var i=0; i<models.length; i++){
			    var m = models[i];
			    m.on('date-active-changed', this.updateActiveState, this);
			    if (date)
				    m.set('active', m.get('date') >= date);
		    }
		    models[models.length - 1].set('active', true);
	    },

		getFilterParams: function() {
			var active = _.first(this.filter(function (model) {
				return model.get('active')
			}));
			var date = active.get('date');
			return {start_ts: date}
		}

    });

    var FilterCollection = Backbone.Collection.extend({
	    model: FilterModel
    });

    var ValueCollection = Backbone.Collection.extend({
	    model: ValueModel
    });

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
            this.has_next = resp['next'] || false;
            return resp['results'];
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
                data: params
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

	var ColumnView = Backbone.View.extend({
		tagName: 'a',
		className: 'column-trigger',

		events: {
			'click': 'toggleVisible'
		},

		initialize: function() {
			this.listenTo(this.model, 'change:visible', this.colorize)
		},

		toggleVisible: function(e){
			e.preventDefault();
			var visible = !this.model.get('visible');
			this.model.set({visible: visible});
			console.log("column " + this.model.get('name') + " now is " + visible);
			// add separate version of change:active event, because of
			// modifications of model done by collection
			this.model.trigger('column-visible-changed', this.model);
		},

		colorize: function(model) {
			colorizeTrigger(this.$el, model.get('visible'));
		}
	});

	var ColumnFilterView = Backbone.View.extend({
		el: "#columns-trigger-container",

		initItemViews: function () {
			var self = this;
			return this.$el.find('.column-trigger').map(function (i, el) {
				var elem = $(el);
				var model = new ColumnModel({
					'visible': elem.data('active'),
					'name': elem.data('value')
				});
				var view = new ColumnView({el: el, model: model});
				self.itemViews.push(view);
				return model;
			});
		},

		initialize: function (options) {
			var params = (options || {}).queryParams || {};
			this.itemViews = [];
			var models = this.initItemViews();
			this.collection = new ColumnCollection(models.toArray(),
				{queryParams: params});
		},

		getFilterParams: function(){
			return this.collection.getFilterParams();
		}
	});

	var DateView = Backbone.View.extend({
		tagName: 'a',
		className: 'dates-trigger',

		events: {
			'click': 'toggleActive'
		},

		initialize: function() {
			this.listenTo(this.model, 'change:active', this.colorize)
		},

		toggleActive: function(e){
			e.preventDefault();
			var active = !this.model.get('active');
			this.model.set({active: active});
			console.log("date " + this.model.get('date') + " now is " + active);
			// add separate version of change:active event, because of
			// modifications of model done by collection
			this.model.trigger('date-active-changed', this.model);
		},

		colorize: function(model) {
			colorizeTrigger(this.$el, model.get('active'));
		}
	});

	var DateFilterView = Backbone.View.extend({
		el: "#dates-trigger-container",
		events: {
			'keydown #start-time': 'updateTime'
		},
		initItemViews: function () {
			var self = this;
			return this.$el.find('.dates-trigger').map(function (i, el) {
				var elem = $(el);
				var model = new DateModel({
					'active': elem.data('active'),
					'date': elem.data('value')
				});
				var view = new DateView({el: el, model: model});
				self.itemViews.push(view);
				return model;
			});

		},
		getStartTime: function (params) {
			var start_ts = (params || {})['start_ts'] || '';
			var tokens = start_ts.split(' ', 2);
			if (tokens.length > 1)
				return tokens[1];
			return '';
		},
		initialize: function(options) {
			var params = (options || {}).queryParams || {};
			this.itemViews = [];
			var models = this.initItemViews();
			this.collection = new DateCollection(models.toArray(),
				{queryParams: params});
			this.time = this.getStartTime(params);
			this.timeInput = this.$el.find('#start-time');
			this.timeInput.val(this.time);
        },

		updateTime: function(e) {
			if (e.keyCode != 13)
				return;
			e.preventDefault();
			this.time = this.timeInput.val();

			filterEvents.trigger('filter-changed', 'time');
		},

		getFilterParams: function() {
			var params = this.collection.getFilterParams();
			if(params['start_ts'] && this.time) {
				params['start_ts'] += ' ' + this.time;
			}
			return params;
		}
	});

	var GrepView = Backbone.View.extend({
		el: "#grep-view",
		initialize: function(options) {
			this.queryParams = options['queryParams'] || {};
			this.dateFilterView = new DateFilterView({queryParams: this.queryParams});
			this.columnFilterView = new ColumnFilterView({queryParams: this.queryParams});
			this.listenTo(filterEvents, 'filter-changed', this.updateQueryParams);
		},
		updateQueryParams: function (args) {
			console.log(args);
			this.queryParams = {};
			_.extend(this.queryParams, this.dateFilterView.getFilterParams());
			_.extend(this.queryParams, this.columnFilterView.getFilterParams());
			console.log(this.queryParams);
		}

	});

    var ResultsView = Backbone.View.extend({
        itemView: LogView,

	    events: {
		    "submit #search-form": "submitSearch",
		    "click .filter-trigger": "triggerFilter"
		    //"click .column-trigger": "triggerColumn",
		    //"keydown #start-time": "checkStartTime"
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

	        var queryParams = this.parseQueryString(query_string);
	        _.extend(filters, queryParams);
			delete filters['columns'];
            var collection = new LogCollection(filters);
            this.view = new GrepView({
                collection: collection,
	            queryParams: queryParams
            });
            $('#log-container').html(''); //xxx

            collection.loadMore(); // get first page
        }
    });


    var router = new LogsRouter();
    Backbone.history.start({pushState: true});

})($, _, Backbone);