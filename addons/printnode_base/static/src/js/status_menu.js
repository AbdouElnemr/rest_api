odoo.define('printnode.status_menu', function (require) {
  "use strict";

  var SystrayMenu = require('web.SystrayMenu');
  var Widget = require('web.Widget');

  var ActionMenu = Widget.extend({
    template: 'printnode_status_menu',

    init: function(parent, options) {
      this._super(parent);

      this.limits = [];
      this.releases = [];
      this.newRelease = false;
      this.loaded = false;
    },

    willStart: function() {
      const limitsPromise = this._rpc({ model: 'printnode.account', method: 'get_limits' });

      // Check if model with releases already exists 
      const releasesPromise = this._rpc({
        model: 'ir.model',
        method: 'search',
        args: [[['model', '=', 'printnode.release']],]
      }).then((data) => {
        // If model exists load releases
        if (data.length) {
          return this._rpc({ model: 'printnode.release', method: 'search_read' });
        }
        // If not exist return empty array
        return [];
      });
      
      return Promise.all([limitsPromise, releasesPromise]).then(([limits, releases]) => {
        // Process limits
        this.limits = limits;

        // Process accounts
        this.releases = releases;
        this.newRelease = releases.length > 0;

        // Loading ended
        this.loaded = true;
      });
    }
  });

  SystrayMenu.Items.push(ActionMenu);

  return ActionMenu;
});
