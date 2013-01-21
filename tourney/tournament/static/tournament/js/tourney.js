(function(window, document, undefined) {
    var mods = {};

    var TOURNEY = {
        module: function(name) {
            if (!mods[name]) {
                mods[name] = {};
            }

            return mods[name];
        }
    }

    window.TOURNEY = TOURNEY;
}(window, document));
