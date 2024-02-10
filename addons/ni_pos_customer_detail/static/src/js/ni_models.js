odoo.define('ni_pos_customer_detail.models', function (require) {
"use strict";

    var models = require('point_of_sale.models');
    var ni_order_super = models.Order.prototype;
    models.load_fields('pos.order',['ni_customer_contact']);

    models.Order = models.Order.extend({
        init_from_JSON: function (json) {
            ni_order_super.init_from_JSON.apply(this, arguments);
            this.ni_customer_contact = json.ni_customer_contact;
            this.ni_customer_flat = json.ni_customer_flat;
            this.ni_customer_bldg = json.ni_customer_bldg;
            this.ni_customer_street = json.ni_customer_street;
            this.ni_customer_area = json.ni_customer_area;
        },
        export_as_JSON: function () {
            return _.extend(ni_order_super.export_as_JSON.apply(this, arguments), {
                ni_customer_contact: this.ni_customer_contact,
                ni_customer_flat: this.ni_customer_flat,
                ni_customer_bldg: this.ni_customer_bldg,
                ni_customer_street: this.ni_customer_street,
                ni_customer_area: this.ni_customer_area,
            });
        },
        add_client_detail: function(infos) {
            this.assert_editable();
            this.ni_customer_contact = infos.ni_customer_contact;
            this.ni_customer_flat = infos.ni_customer_flat;
            this.ni_customer_bldg = infos.ni_customer_bldg;
            this.ni_customer_street = infos.ni_customer_street;
            this.ni_customer_area = infos.ni_customer_area;
        },
        export_for_printing: function() {
        var json = ni_order_super.export_for_printing.apply(this,arguments);
        json.ni_customer_contact = this.ni_customer_contact;
        json.ni_customer_flat = this.ni_customer_flat;
        json.ni_customer_bldg = this.ni_customer_bldg;
        json.ni_customer_street = this.ni_customer_street;
        json.ni_customer_area = this.ni_customer_area;
        return json;
    },

    });
    return models;
});