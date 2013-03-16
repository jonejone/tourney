(function(playeractions) {

    var Updater = function() {
        this.config = {
            'available-spots': $('.updater-available-spots'),
            'max-players': $('.updater-max-players'),
            'waiting-list-count': $('.updater-waiting-list-count'),
            'wildcard-spots': $('.updater-wildcard-spots'),
            'player-list-count': $('.updater-player-list-count'),
        };
    };

    Updater.prototype = {
        update: function(data) {
            $.each(data, function(key, value) {
                this.config[key].html(value);
            }.bind(this));
        }
    };

    playeractions.Updater = Updater;

    var ActionsManager = function(config) {
        this.config = config;
        this.updater = new Updater();
        this.bindEvents();

        /* Create a status bar for messaging */
        var mod = TOURNEY.module('status_bar');

        this.status_bar = new mod.StatusBar(
            config.status_bar_container)
    };

    ActionsManager.prototype = {
        bindEvents: function() {
            $('a[data-action="remove"]').bind('click', this.actionHandler('remove'));
            $('a[data-action="edit"]').bind('click', this.actionHandler('edit'));
            $('a[data-action="accept"]').bind('click', this.actionHandler('accept'));
        },

        actionHandler: function(action) {
            return function(e) {
                /* First we need to get the player ID */
                var parent = $(e.target).parents('tr');
                var player_id = parent.data('tournamentPlayerId');
                this.performAction(action, player_id);
            }.bind(this);
        },

        getPlayerRow: function(player_id) {
            return $('tr[data-tournament-player-id='
                + player_id + ']');
        },

        performAction: function(action, player_id) {

            // Some actions just want to redirect elsewhere
            if(action == 'edit') {
                console.log('Redirectin', player_id);
                return;
            }

            // Lets have our status bar easily available
            var s = this.status_bar;
            s.setWarning(this.config.lang[action + '_trying']);

            var url = this.config.action_url;
            var post_data = {
                'action': 'waiting-list-' + action,
                'tournamentplayer_id': player_id,
            };

            $.post(
                url,
                post_data,
                function(data, textStatus) {
                    if (data.success) {
                        if (data.removed) {
                            this.getPlayerRow(
                                player_id).remove();

                            s.setSuccess(
                                this.config.lang[action + '_success']);
                        }

                        /* Update counters if data available */
                        if (data.updater_data) {
                            this.updater.update(data.updater_data);
                        }
                    } else {
                        if (data.error) {
                            s.setError(this.config.lang['error_message'] +
                                ' ' + data.error)
                        } else {
                            s.setError(
                                this.config.lang['error']);
                        }
                    }
                }.bind(this),
                'json'
            );
        },
    };

    playeractions.ActionsManager = ActionsManager

}(TOURNEY.module('playeractions')));
