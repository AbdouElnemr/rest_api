odoo.define('ni_pos_customer_detail.popups', function (require) {
"use strict";

    const Popup = require('point_of_sale.ConfirmPopup');
    const Registries = require('point_of_sale.Registries');
    const PosComponent = require('point_of_sale.PosComponent');

    class NiCustomerDetailsPopupWidget extends Popup {

        constructor() {
            super(...arguments);
        }
        go_back_screen() {
            this.showScreen('PaymentScreen');
            this.trigger('close-popup');
        }
        confirm_details_customer(event) {
            var infos = {
                'ni_customer_contact': $('.ni_customer_contact').val(),
                'ni_customer_flat': $('.ni_customer_flat').val(),
                'ni_customer_bldg': $('.ni_customer_bldg').val(),
                'ni_customer_street': $('.ni_customer_street').val(),
                'ni_customer_area': $('.ni_customer_area').val(),
                };
            this.env.pos.get_order().add_client_detail(infos);
           this.trigger('close-popup');
        }



    };
    NiCustomerDetailsPopupWidget.template = 'NiCustomerDetailsPopupWidget';

    Registries.Component.add(NiCustomerDetailsPopupWidget);

    return NiCustomerDetailsPopupWidget;
});