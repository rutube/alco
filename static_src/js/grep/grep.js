(function($, _, Backbone) {
    /* models */
    var LogModel = Backbone.Model.extend({
	    toJSON: function () {
		    var result = Backbone.Model.prototype.toJSON.apply(this);
		    result['time'] = this.time();
		    result['shortHost'] = this.shortHost();
		    return result;
	    },
	    time: function () {
		    return this.get('datetime').split('T')[1].replace('000', '');
	    },
	    shortHost: function() {
		    return this.get('host').split('.')[0]
	    }
    });

    /* collections */
    var LogCollection = Backbone.Collection.extend({
        model: LogModel,
        url: '/api/grep/grep/',

        initialize: function(queryParams) {
            this.page = 1;
            this.logger_index = queryParams['logger_index'] || 'logger';
	        delete queryParams['logger_index'];

            this.has_next = true;
            this.loading = false;
            this.queryParams = queryParams || {};
        },

        parse: function(resp) {
            this.has_next = resp.next || false;
            return resp.results;
        },

        loadMore: function() {
            if (this.loading || !this.has_next) {
                return false;
            }

            _.extend(this.queryParams, {
                'page': this.page
            });

            this.loading = true;
            this.page += 1;

            var res = this.fetch({
                data: this.queryParams
            });

            $.when(res).then(_.bind(function() {
                this.loading = false;
	            this.trigger("loaded");
            }, this));

            return res;
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
		    "submit #search-form": "submitSearch"
	    },

	    el: "#grep-view",
	    container: "#log-container",

        initialize: function() {
            this.listenTo(this.collection, "add", this.appendItem);
            this.listenTo(this.collection, "loaded", this.checkScroll);
            this.listenTo(this.collection, "update", this.appendPageNumber);
			this.container = $(this.container);
            // prevent of query duplicating on scroll
            $(window).scroll(_.bind(this.checkScroll, this));
        },

	    submitSearch: function(e) {
		    e.preventDefault();
		    this.collection.queryParams['search'] = $('#search-text').val();
		    this.collection.reset();
		    this.container.html('');
		    this.collection.loadMore();
	    },
        checkScroll: function() {
            var contentOffset = this.$el.offset().top,
                contentHeight = this.$el.height(),
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