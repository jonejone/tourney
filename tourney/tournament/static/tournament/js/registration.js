(function(registration) {

    var RegistrationPdga = function(config) {
        this.config = config;
        this.timeout;
        this.rating = 0;
        this.prepare();

        if (this.config.stages) {
            var rating_over_zero = false;
            var stage = this.getCurrentStage();

            $(stage.classes).each(function(i, class_) {
                if(class_.rating_required > 0) {
                    rating_over_zero = true;
                }
            });

            if(rating_over_zero) {
                this.disableButton();
            }
        }
    };

    RegistrationPdga.prototype = {
        prepare: function() {
            this.button = $('.btn-primary');

            /* Create a status bar */
            var module = TOURNEY.module('status_bar'),
                container = $('<div class="ajax-status-bar" style="display: none;">'
                    + '<span class="label"></span></div>');

            $('#id_pdga_number').parent().append(container);
            this.status_bar = new module.StatusBar(container);

            /* Bind event handler for class field */
            $('#id_player_class').bind('change', function(e) {
                this.validateRating();
            }.bind(this));

            var pdga_number = $('#id_pdga_number');

            var changeFunction = function(e) {

                if(this.timeout) {
                    clearTimeout(this.timeout);
                }

                if(pdga_number.val()) {
                    this.timeout = setTimeout(function() {

                            var pdga_url = this.config.ajax_url +
                                '?pdga_number=' + pdga_number.val();

                            this.status_bar.setWarning('Loading rating...');

                            $.get(pdga_url, {}, function(data, textStatus, jqXHR) {
                                if (data.success) {

                                    this.status_bar.setSuccess('Current PDGA rating: ' +
                                        data.rating)

                                    this.rating = data.rating;
                                    this.validateRating();

                                    if (data.name) {
                                        $('#id_name').val(data.name);
                                    }

                                    if (data.country_code) {
                                        $('#id_country').val(data.country_code);
                                    }

                                } else {
                                    this.status_bar.setError('Unable to retrieve rating.');
                                }
                            }.bind(this));

                    }.bind(this), this.config.delay);
                }
            }.bind(this);

            $('#id_pdga_number').bind('keyup', changeFunction);
            $('#id_pdga_number').bind('click', changeFunction);
            changeFunction();
        },

        disableButton: function() {
            this.button.addClass('disabled');
            this.button.attr('disabled', 'disabled');
        },

        enableButton: function() {
            this.button.removeClass('disabled');
            this.button.removeAttr('disabled');
        },

        getClassById: function(id) {
            var return_class = false;

            $(this.getCurrentStage().classes).each(function(i, class_) {
                if (class_.class_id == id) {
                    return_class = class_;
                }
            });

            return return_class;
        },

        validateRating: function() {
            if (!this.config.stages) {
                this.enableButton();
                return;
            }

            var stage = this.getCurrentStage();

            var class_id = parseInt(
                $('#id_player_class').val(), 10);

            var class_ = this.getClassById(class_id);

            if(!class_) {
                return;
            }

            var rating = this.rating;
            var required_rating = class_.rating_required;
            var diff = required_rating - rating;

            if (required_rating === 0) {
                this.enableButton();
                return;
            }

            if(required_rating > rating) {
                this.status_bar.setError('Rating ' + rating + ' does not meet criteria for this class (' + required_rating + ')');
                this.disableButton();
            } else {
                this.status_bar.setSuccess('Rating ' + rating + ' meets criteria for this class (' + required_rating + ')');
                this.enableButton();
            }
        },

        getCurrentStage: function() {
            var current;
            $(this.config.stages).each(function(i, stage) {
                if(stage.is_current) {
                    current = stage;
                }
            });

            return current;
        },
    };

    registration.RegistrationPdga = RegistrationPdga;

}(TOURNEY.module('registration')));
