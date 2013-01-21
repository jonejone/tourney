(function(status_bar) {

    var StatusBar = function(container) {
        this.container = container;
        this.span = this.container.find('span');
        this.type = 'warning';
        this.fade = false;
    };

    StatusBar.prototype = {
        setType: function(type) {
            this.span.removeClass('label-' + this.type);
            this.span.addClass('label-' + type);
            this.type = type;
        },

        setMessage: function(message) {
            this.span.html(message);
        },

        setSuccess: function(message) {
            this.setType('success');
            this.setMessage(message);
            this.show();

            if (this.fade) {
                this.container.delay(3000).fadeOut();
            }
        },

        setError: function(message) {
            this.setType('important');
            this.setMessage(message);
            this.show();

            if (this.fade) {
                this.container.delay(3000).fadeOut();
            }
        },

        setWarning: function(message) {
            this.setType('warning');
            this.setMessage(message);
            this.show();
        },

        hide: function() {
            this.container.hide();
        },

        show: function() {
            this.container.fadeIn();
        },
    };

    status_bar.StatusBar = StatusBar;

}(TOURNEY.module('status_bar')));
