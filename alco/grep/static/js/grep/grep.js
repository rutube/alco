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
		    var result = Backbone.Model.prototype.toJSON.call(this);
		    result['time'] = this.time();
		    result['shortHost'] = this.shortHost();
		    result['level'] = this.level();
		    result['columns'] = this.collection.columns;
		    result['logline'] = this.snippet();
		    return result;
	    },
	    snippet: function() {
		    var s = (this.get('logline_snippet') || this.get('logline'));
		    s = _.escape(s);
		    s = s.replace(/&lt;b&gt;/g, '<span class="match label label-info">').replace(/&lt;\/b&gt;/g, '</span>');
		    return s;
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


	var BaseFilterModel = Backbone.Model.extend({
		defaults: {
            name: null,
            active: true
	    },
		triggerEvent: 'visible-changed',

		triggerFilterChange: function(options) {
			this.trigger(this.triggerEvent, this, options);
		}
	});

	var ColumnModel = BaseFilterModel.extend({
		name: 'ColumnModel',
		defaults: {
            name: null,
            visible: true
	    },
		triggerEvent: 'column-visible-changed'
	});

	var DateModel = BaseFilterModel.extend({
		name: 'DateModel',
		defaults: {
            date: null,
            active: true
	    },

		triggerEvent: 'date-active-changed'

	});

	var FieldModel = BaseFilterModel.extend({
		name: 'FieldModel',
		defaults: {
            name: null,
			active: true,
            value: null
	    },

		triggerEvent: 'field-active-changed'

	});

    /* collections */

    var ColumnCollection = Backbone.Collection.extend({
	    model: ColumnModel,
	    isActive: function (model) {
		    return model.get('visible')
	    },
	    updateActiveState: function (model) {
		    if (this.filter(this.isActive).length == 0){
			    for (var i=0; i<this.models.length; i++) {
				    var cur = this.models[i];
				    cur.set({'visible': true});
			    }
		    }
		    filterEvents.trigger('filter-changed', 'columns');
	    },

	    initialize: function (models, options) {
		    var params = (options|| {}).queryParams || {};
		    var columns = params['columns'];
		    if (columns)
			    columns = columns.split(',');

		    for (var i=0; i<models.length; i++){
			    var m = models[i];
			    m.on(m.triggerEvent, this.updateActiveState, this);
			    if (columns)
				    m.set('visible', _.contains(columns, m.get('name')));
		    }
	    },

	    getFilterParams: function() {
			var visible = this.filter(this.isActive);
			if (visible.length == 0 || visible.length == this.models.length)
				return {};
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

    var FieldCollection = Backbone.Collection.extend({
	    model: FieldModel,
	    isActive: function (model) {
		    return model.get('active')
	    },
	    updateActiveState: function (model, options) {
		    var cur, i, ctrl = (options || {})['ctrl'] || false;
		    var field = false;
		    var selected = this.filter(this.isActive).length;
		    var currentActive = model.get('active');
		    for (i=0; i<this.models.length; i++) {
			    cur = this.models[i];
			    var current = cur.get('value') == model.get('value');
				if (!ctrl) {
					cur.set('active', current);
				} else {
					if (selected == 0)
						// all disabled - revert to all active
						cur.set('active', true);
					//else if (cure)
					//	cur.set('active', current)
				}
		    }
		    filterEvents.trigger('filter-changed', 'field-' + field);
	    },

	    initialize: function (models, options) {
		    options = options|| {};
		    var params = options.queryParams || {};
		    var filterName = options.filterName;
		    var values = params[filterName];
		    if (values)
			    values = [values];
		    else {
			    values =  params[filterName + '__in'];
			    if (values) values = values.split(',')
		    }

		    for (var i=0; i<models.length; i++){
			    var m = models[i];
			    m.on(m.triggerEvent, this.updateActiveState, this);
			    if (values)
				    m.set('active', _.contains(values, m.get('value')));
		    }
	    },

	    getFilterParams: function() {
			var visible = this.filter(this.isActive);
			if (visible.length == 0 || visible.length == this.models.length)
				return {};
		    var result = {};
		    var suffix = (visible.length > 1)? '__in': '';
		    result[visible[0].get('field') + suffix] = visible.map(function(model) {
					return model.get('value')
				}).join(',');
			return result;
		}
    });

	var LogCollection = Backbone.Collection.extend({
        model: LogModel,
        url: '/api/grep/',

        initialize: function(models, queryParams) {
            this.logger_index = queryParams['logger_index'] || 'logger';
	        if (queryParams['columns'])
	            this.columns = queryParams['columns'].split(',');
	        this.queryParams = _.omit(queryParams, 'logger_index') || {};
	        this.url += this.logger_index + '/?';
	        this.baseUrl = this.url + $.param(this.queryParams);
            this.next = this.baseUrl;
            this.loading = false;
            this.search = this.queryParams['search'];
        },

        parse: function(resp) {
            this.next = ('next' in resp) && resp['next'];
            return resp['results'];
        },

		updateMatches: function() {
			if (this.search) {
				this.matchedIds = this.pluck('id');
				this.lastKnownMatch = _.last(this.matchedIds);

			}
		},

		checkMatch: function(id) {
			if (!this.search) {
				return null;
			}
			if (_.contains(this.matchedIds, id)) {
				if (id >= this.lastKnownMatch) {
					this.loadMore();
				}
				return this.get(id);
			}
		},

	    reset: function(models, options) {
		    Backbone.Collection.prototype.reset.call(this, models, options);
		    this.baseUrl = this.url + $.param(this.queryParams);
            this.next = this.baseUrl;
	    },

        loadMore: function() {
            if (this.loading || !this.next) {
                return false;
            }

            this.loading = true;
            this.url = this.next;

            var res = this.fetch({
                error: _.bind(function(col) {
                    col.loading = false;
	            })
            });
            $.when(res).then(_.bind(function(e, x, y) {
                this.loading = false;
	            if (this.search)
		            this.updateMatches();
	            this.trigger("loaded");
            }, this));
            return res;
        },

		reloadLastPage: function() {
			if (this.loading) {
                return false;
            }

            this.loading = true;
			var res = this.fetch({
                error: _.bind(function(col) {
                    col.loading = false;
	            })
            });
            $.when(res).then(_.bind(function(e, x, y) {
                this.loading = false;
	            if (this.search)
		            this.updateMatches();
	            this.trigger("loaded");
            }, this));
            return res;
		},

        getUrl: function() {
            return this.url;
        }
    });

    /* views */

    var LogView = Backbone.View.extend({
        tagName: 'div',
        className: 'log-row log-row-ellipsis',

	    events: {
		    'click .logline': 'toggleEllipsis',
		    'click .column': 'toggleFilter',
		    'click a.context': 'toggleContext'
	    },

	    template: _.template($('#log-template').html()),

        toggleFilter: function(e) {
		    var el = $(e.target);
		    var field = el.data('field');
		    var value = el.data('value');
		    filterEvents.trigger("cell-click:" + field, value);
	    },

		toggleEllipsis: function(e) {
			this.$el.toggleClass('log-row-ellipsis');
		},

	    toggleContext: function(e) {
		    e.preventDefault();
		    this.$el.filter('pre.context').removeClass('active');
		    var pill = $(e.target);
		    var activate = !pill.hasClass('active');
		    pill.toggleClass('active', activate);
		    var ctx = pill.data('context');
		    var tab = this.$el.find('pre.context[data-context="' + ctx + '"]');
		    tab.toggleClass("active", activate);
		    this.$el.find('div.tab-content').toggle(activate);
	    },

        initialize: function() {
            this.listenTo(this.model, 'change', this.render);

        },

        render: function() {
            this.$el.html(this.template(this.model.toJSON()));
	        if ((this.model.get('logline_snippet') || '').indexOf("<b>") > -1) {
		        this.$el.toggleClass('logline-found', true);
	        }
            return this;
        }
    });


	var BaseFilterItemView = Backbone.View.extend({
		tagName: 'a',
		events: {
			'click': 'toggleFilter'
		},
		stateField: 'active',
		nameField: 'name',

		initialize: function(options) {
			var params = (options||{})['params'];
			this.colorize(this.model);
			this.listenTo(this.model, 'change:' + this.stateField, this.colorize)
		},

		toggleFilter: function(e){
			e.preventDefault();
			var active = !this.model.get(this.stateField);
			this.model.set(this.stateField, active);

			// add separate version of change:active event, because of
			// modifications of model done by collection
			this.model.triggerFilterChange({ctrl: filterEvents.ctrlKey});
		},

		colorize: function(model) {
			colorizeTrigger(this.$el, model.get(this.stateField));
		}
	});

	var ColumnView = BaseFilterItemView.extend({
		name: 'ColumnView',
		className: 'column-trigger',
		stateField: 'visible'
	});

	var BaseFilterView = Backbone.View.extend({
		name: 'BaseFilterView',
		fields: {
			'active': 'active',
			'name': 'name',
			'value': 'value'
		},

		model: Backbone.Model.extend({}),
		itemView: Backbone.View.extend({}),
		collection: Backbone.Collection.extend({}),
		itemSelector: '.filter-trigger',

		initialize: function (options) {
			this.itemViews = [];
			var models = this.initItemViews((options|| {})['queryParams']);
			this.collection = new this.collection(models, options);
		},

		initItemViews: function (params) {
			params = params || {};

			var self = this;
			return _.map(this.$el.find(this.itemSelector), function (el) {
				var elem = $(el);
				var data = {};
				for (var modelKey in this.fields) {
					if (!this.fields.hasOwnProperty(modelKey))
						continue;
					var elemKey = this.fields[modelKey];
					data[modelKey] = elem.data(elemKey);
				}
				var model = new this.model(data);
				var view = new this.itemView({el: el, model: model, params: params});
				self.itemViews.push(view);
				return model;
			}, this);
		},

		getFilterParams: function(){
			return this.collection.getFilterParams();
		}
	});

	var ColumnFilterView = BaseFilterView.extend({
		name: 'ColumnFilterView',
		el: "#columns-trigger-container",
		itemSelector: '.column-trigger',
		model: ColumnModel,
		itemView: ColumnView,
		collection: ColumnCollection,
		fields: {
			'visible': 'active',
			'name': 'value'
		}
	});

	var DateView = BaseFilterItemView.extend({
		name: 'DateView',
		className: 'dates-trigger',
		nameField: 'date'
	});

	var DateFilterView = BaseFilterView.extend({
		name: 'DateFilterView',
		el: "#dates-trigger-container",
		itemSelector: '.dates-trigger',
		model: DateModel,
		itemView: DateView,
		collection: DateCollection,
		events: {
			'keydown #start-time': 'updateStartTime'
		},
		fields: {
			date: 'value',
			active: 'active'
		},

		initStartTime: function (options) {
			var params = (options || {}).queryParams || {};
			var start_ts = (params || {})['start_ts'] || '';
			var tokens = start_ts.split(' ', 2);
			if (tokens.length > 1)
				this.time = tokens[1];
			else
				this.time = '';
			this.timeInput = this.$el.find('#start-time');
			this.timeInput.val(this.time);
		},

		initialize: function(options) {
			BaseFilterView.prototype.initialize.call(this, options);
			this.initStartTime(options);
		},

		updateStartTime: function(e) {
			if (e.keyCode != 13)
				return;
			e.preventDefault();
			this.time = this.timeInput.val();

			filterEvents.trigger('filter-changed', 'time');
		},

		getFilterParams: function() {
			var params = BaseFilterView.prototype.getFilterParams.call(this);
			if(params['start_ts'] && this.time) {
				params['start_ts'] += ' ' + this.time;
			}
			return params;
		}
	});

	var FieldView = BaseFilterItemView.extend({
		name: 'FieldView',
		className: 'filter-trigger',
		nameField: 'field',

		markActive: function() {
			this.model.set(this.stateField, true);

			// add separate version of change:active event, because of
			// modifications of model done by collection
			this.model.triggerFilterChange({ctrl: false});
		}

	});

	var FieldFilterView = BaseFilterView.extend({
		name: 'FieldFilterView',
		itemSelector: '.filter-trigger',
		model: FieldModel,
		itemView: FieldView,
		collection: FieldCollection,
		fields: {
			value: 'value',
			active: 'active',
			field: 'field'
		},

		initialize: function (options) {
			BaseFilterView.prototype.initialize.call(this, options);
			options = options || {};
			this.filterName = options['filterName'];
			this.listenTo(filterEvents, 'cell-click:' + this.filterName, this.toggleFilter);

		},

		toggleFilter: function(value) {
			for (var i in this.itemViews) {
				if (!this.itemViews.hasOwnProperty(i))
						continue;
				var view = this.itemViews[i];
				if (view.model.get('value') == value) {
					view.markActive();
					break;
				}
			}
		}
	});

	var GrepView = Backbone.View.extend({
		el: "#grep-view",

		initialize: function(options) {
			var focused = $('body');
			focused.on('keydown', this.updateSpecialKeys);
			focused.on('keyup', this.updateSpecialKeys);

			this.queryParams = options['queryParams'] || {};
			this.pageUrl = options['pageUrl'];
			this.dateFilterView = new DateFilterView({queryParams: this.queryParams});
			this.columnFilterView = new ColumnFilterView({queryParams: this.queryParams});
			this.resultsView = new ResultsView({
				queryParams: this.queryParams,
				pageUrl: this.pageUrl
			});
			this.searchView = new SearchFormView({
				queryParams: this.queryParams
			});
			this.listenTo(filterEvents, 'filter-changed', this.updateQueryParams);
			this.fieldFilters = [];
			_.map($('.filter-trigger-container'), this.initFilterView, this);
		},

		updateSpecialKeys: function(e) {
			filterEvents.ctrlKey = e.ctrlKey;
			filterEvents.altKey = e.altKey;
			filterEvents.shiftKey = e.shiftKey;
		},

		constructQueryParams: function () {
			this.queryParams = {};
			_.extend(this.queryParams, this.dateFilterView.getFilterParams());
			_.extend(this.queryParams, this.columnFilterView.getFilterParams());
			_.extend(this.queryParams, this.searchView.getFilterParams());
			_.each(this.fieldFilters, function (view) {
				_.extend(this.queryParams, view.getFilterParams());

			}, this);
		},
		updateQueryParams: function (what) {
			this.constructQueryParams();
			var viewUrl = this.pageUrl + '?' + $.param(this.queryParams).replace(/\+/g, '%20');
			if (what == 'columns') {
				this.resultsView.updateVisibility(this.queryParams);
				router.navigate(viewUrl)
			} else {
			    router.navigate(viewUrl, {trigger: true});
			}
		},

		initFilterView: function(el) {
			var filterName = $(el).data('field');
			var view = new FieldFilterView({
				el: el,
				queryParams: this.queryParams,
				filterName: filterName
			});
			view.listenTo(this.resultsView, 'cell-click', view.toggleFilter);
			this.fieldFilters.push(view);
		},


        remove: function() {
	        this.stopListening();
	        this.fieldFilters.push(
	            this.dateFilterView,
	            this.columnFilterView,
		        this.searchView,
		        this.resultsView
	        )

	        _.each(this.fieldFilters, function(view){
		        view.stopListening();
		        view.undelegateEvents();
	        });
	        this.fieldFilters = null;
	        // !!! Backbone.View.prototype.remove.call(this, arguments);

			// disable scroll events subscription
            $(window).off('scroll');

	        var focused = $('body');
			focused.unbind('keydown');
			focused.unbind('keyup');
        }

	});

	var SearchFormView = Backbone.View.extend({
		name: 'SearchFormView',
		el: "#search-form",
		events: {
			'submit': 'updateSearch',
			'click .filter-toggler': 'toggleSearchFilter',
			'click #context-btn': 'toggleContext'
		},
		initialize: function(options) {
			options = options || {};
		    var queryParams = options.queryParams || {};

			this.input = this.$el.find('#search-text');
			this.context_btn = this.$el.find('#context-btn');
			this.context = !!queryParams['context'];
			this.context_btn.toggleClass('active', this.context);

			this.fields = [];
			_.each(this.$el.find('.filter-toggler'), function(el) {
				var field = $(el).val();
				this.fields.push(field)
			}, this);
			this.filters = {};

			for (var i=0;i<this.fields.length; i++) {
				var field = this.fields[i];
				if (queryParams[field] && this.fields.indexOf(field) > -1) {
					this.filters[field] = queryParams[field];
				}
			}

			this.search = _.unescape(queryParams.search).replace(/^\s*(.+)\s*$/, '$1');
			this.updateInput();
		},
		updateInput: function() {
			if (!this.search && $.isEmptyObject(this.filters)) {
				this.input.val('');
			}

			var result = this.search || '';
			for (var i=0;i<this.fields.length; i++) {
				var field = this.fields[i];
				var value = this.filters[field];
				var active = false;
				if (value !== null && typeof value !== 'undefined') {
					result += ' @' + field + '=' + value;
					active = true;
				}
				var button = this.$el.find('.filter-toggler[value="' + field + '"]');
				button.toggleClass('btn-success', active);
				button.toggleClass('btn-default', !active);
			}
			this.input.val(result.replace(/^\s*(.+)\s*$/, '$1'));
		},
		toggleSearchFilter: function(e) {
			var button = $(e.target);
			var active = button.hasClass('btn-success');
			button.toggleClass('btn-success', !active);
			button.toggleClass('btn-default', active);
			var field = button.val();

			if (!active) {
				this.filters[field] = ''
			} else {
				delete this.filters[field]
			}
			this.updateInput();
		},
		toggleContext: function(e) {
			var button = $(e.target);
			var active = button.hasClass('active');
			button.toggleClass('active', !active);
			this.context = !active;
			filterEvents.trigger('filter-changed', 'context');
			this.input.focus();
		},
		updateSearch: function(e){
			e.preventDefault();
			this.parseInput();
			filterEvents.trigger('filter-changed', 'search');
		},
		parseInput: function() {
			var value = this.input.val();
			if (!value) {
				this.filters = {};
				this.search = null;
				return;
			}
			re = /@([\w_]+)=(("[^\"]+")|([^\s]+))/g;
			filters = value.match(re) || [];
			this.filters = {};
			for (var i=0;i<filters.length; i++) {
				var filter = filters[i].substring(1).split('=', 2);
				var key = filter[0];
				if (this.fields.indexOf(key) == -1)
					continue;
				this.filters[key] = filter[1].replace(/^"(.+)"$/, '$1');
			}

			var search = value.replace(/@([\w_]+)=(("[^\"]+")|([^\s]+))/g, '');
			search = search.replace(/\s+/g, ' ');
			if (search && search != ' ')
				this.search = search;
			else
				this.search = ''
		},

		getFilterParams: function(e) {
			var result = {};
			_.extend(result, this.filters);
			if (this.search)
				result['search'] = this.search;
			if (this.context)
				result['context'] = 'y';
			return result;
		}

	});

    var ResultsView = Backbone.View.extend({
        itemView: LogView,
	    name: 'ResultsView',
	    el: "#log-list",
	    container: "#log-container",
	    events: {
		    'click #log-error': 'reloadLastPage'
	    },

	    initCollection: function (queryParams) {
		    this.search = queryParams['search'];
		    this.context = queryParams['context'] || !this.search;
		    this.nothingFound = false;
		    this.loader = $('#log-progress');
		    this.error = $('#log-error');
		    if (this.search) {
			    this.searchCollection = new LogCollection([], queryParams);
			    if (!this.context)
			        this.listenTo(this.searchCollection, "add", this.appendItem);
			    else
	                this.listenToOnce(this.searchCollection, "loaded", this.startContextLoading);
			    this.listenTo(this.searchCollection, "loaded", this.checkScroll);
			    this.listenTo(this.searchCollection, "error", this.showError);
		        queryParams = _.omit(queryParams, 'search');
		    } else {
			    this.searchCollection = null;
		    }

		    this.collection = new LogCollection([], queryParams);
		    this.listenTo(this.collection, "add", this.appendItem);
		    this.listenTo(this.collection, "loaded", this.checkScroll);
		    this.listenTo(this.collection, 'request', this.showLoader);
		    this.listenTo(this.collection, "error", this.showError);
		    if (!this.search)
		        this.collection.loadMore();
		    else
		        this.searchCollection.loadMore();
	    },
	    noSearchResults: function () {
		    this.loader.hide();
		    this.container.html('<div class="row col12"><div class="h3 text-center">404</div></div>');
		    this.nothingFound = true;

	    },
	    startContextLoading: function() {
		    if (this.searchCollection.models.length == 0) {
			    this.noSearchResults();
			    return;
		    }
		    if (!this.context)
			    return;
		    var firstResult = this.searchCollection.models[0];
		    this.collection.queryParams['start_ts'] = firstResult.get('datetime').replace('T', ' ');
		    this.collection.loadMore();
	    },
	    initialize: function(options) {
		    options = options || {};
		    this.url = options.pageUrl;
		    var queryParams = options.queryParams;
		    this.initCollection(queryParams);
		    this.container = $(this.container);
		    this.container.html('');
	        // prevent of query duplicating on scroll
            $(window).scroll(_.bind(this.checkScroll, this));
        },

	    showLoader: function(options) {
		    this.loader.show();
		    this.error.hide();
	    },

	    showError: function(e) {
		    this.loader.hide();
		    this.error.show()
	    },

	    updateVisibility: function(queryParams) {
		    var columns = queryParams['columns'];

		    if (columns) {
			    $('.column-toggle ').hide();
			    columns = columns.split(',');
			    this.collection.columns = columns;
			    if (this.searchCollection)
			        this.searchCollection.columns = columns;
			    for(var i=0; i< columns.length; i++) {
				    var col = columns[i];
					$('.column-' + col).show();
			    }
		    } else {
			    $('.column-toggle ').show();
			    this.collection.columns = null;
		    }
	    },

	    reset: function() {
		    this.container.html('');
		    this.loader.show();
		    this.error.hide();
	    },

	    reloadLastPage: function() {
		    this.loader.show();
		    this.error.hide();
		    if (this.context)
		        this.collection.reloadLastPage();
	    },

	    checkScroll: function() {
		    if (this.searchCollection && this.searchCollection.loading
		        || this.collection.loading)
		        return;
            this.loader.hide();
		    if (this.nothingFound)
		        return;
		    var contentOffset = this.container.offset().top,
                contentHeight = this.container.height(),
                pageHeight = $(window).height(),
                scrollTop = $(window).scrollTop();
            var triggerPoint = 200;

            if (contentOffset + contentHeight - scrollTop - pageHeight < triggerPoint) {
	            if (!this.search ||!this.searchCollection.loading)
                    if (this.context && this.collection.loadMore()) {
	                    this.loader.show();
	                    this.error.hide();
                    }
	        }
        },

        appendItem: function(item) {
	        if (this.search) {
		        var match = this.searchCollection.checkMatch(item.get('id'));
		        if (match) item = match;
	        }
            var itemView = new this.itemView({
                model: item
            });
            this.container.append(itemView.render().el);
        },
        render: function() {
            return this;
        }
    });

    /* routers */
    var LogsRouter = Backbone.Router.extend({

        routes: {
            'grep/:logger_index/': 'grep'
        },

	    parseQueryString: function (queryString){
		    var params = {};
		    if(queryString){
		        _.each(
		            _.map(decodeURI(queryString).split(/&/g),function(el,i){
		                var aux = el.split('='), o = {};
		                if(aux.length >= 1){
		                    var val = undefined;
		                    if(aux.length == 2)
		                        val = aux[1];
		                    o[aux[0]] = decodeURIComponent(val);
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

	        var queryParams = this.parseQueryString(query_string);

            queryParams['logger_index'] = logger_index;
            this.view = new GrepView({
				pageUrl: window.location.pathname,
	            queryParams: queryParams
            });

        }
    });


    var router = new LogsRouter();
    Backbone.history.start({pushState: true});

})($, _, Backbone);