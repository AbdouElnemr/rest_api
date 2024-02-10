odoo.define('ni_pos_customer_detail.PaymentScreenButton', function(require) {
'use strict';
    const { Gui } = require('point_of_sale.Gui');
    const PosComponent = require('point_of_sale.PosComponent');
    const { posbus } = require('point_of_sale.utils');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const NiCustomerInfoDetails = (PaymentScreen) =>
       class extends PaymentScreen {
           constructor() {
               super(...arguments);
           }
           NiCustomerDetails() {
                var self = this;
                var order = self.env.pos.get_order();
                var infos = {
                'ni_customer_contact': order.ni_customer_contact,
                'ni_customer_flat': order.ni_customer_flat,
                'ni_customer_bldg': order.ni_customer_bldg,
                'ni_customer_street': order.ni_customer_street,
                'ni_customer_area': order.ni_customer_area,
                };
                self.showPopup('NiCustomerDetailsPopupWidget',infos);
           }
       };
   Registries.Component.extend(PaymentScreen, NiCustomerInfoDetails);
   return NiCustomerInfoDetails;
});