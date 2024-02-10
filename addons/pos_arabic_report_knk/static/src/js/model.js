odoo.define('pos_arabic_report_knk.model', function(require) {
    "use strict";

    var models = require("point_of_sale.models");
    var rpc = require('web.rpc');
    var core = require('web.core');
    var _t = core._t;

    models.load_fields("res.company", [
        "arabic_name",
        "company_footer",
        "company_heading_1",
        "company_heading_2",
        "company_heading_3",
        "company_heading_4",
    ]);

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        export_for_printing: function() {
            var orders = _super_order.export_for_printing.apply(this, arguments);
            orders.company.arabic_name = this.pos.company.arabic_name;
            orders.company.currency_id = this.pos.company.currency_id;

            // QRCode
            const codeWriter = new window.ZXing.BrowserQRCodeSvgWriter()
            let qr_values = this.compute_sa_qr_code(orders.company.name, orders.company.vat, orders.date.isostring, orders.total_with_tax, orders.total_tax);
            let qr_code_svg = new XMLSerializer().serializeToString(codeWriter.write(qr_values, 150, 150));
            orders.qrcode_img = "data:image/svg+xml;base64," + window.btoa(qr_code_svg);

            // Barcode
            var canvas = document.createElement('canvas');
            JsBarcode(canvas, orders['name']);
            orders['barcode'] = canvas.toDataURL("image/png");

            return orders;
        },
        compute_sa_qr_code(name, vat, date_isostring, amount_total, amount_tax) {
            /* Generate the qr code for Saudi e-invoicing. Specs are available at the following link at page 23
            https://zatca.gov.sa/ar/E-Invoicing/SystemsDevelopers/Documents/20210528_ZATCA_Electronic_Invoice_Security_Features_Implementation_Standards_vShared.pdf
            */
            const seller_name_enc = this._compute_qr_code_field(1, name);
            const company_vat_enc = this._compute_qr_code_field(2, vat);
            const timestamp_enc = this._compute_qr_code_field(3, date_isostring);
            const invoice_total_enc = this._compute_qr_code_field(4, amount_total.toString());
            const total_vat_enc = this._compute_qr_code_field(5, amount_tax.toString());

            const str_to_encode = seller_name_enc.concat(company_vat_enc, timestamp_enc, invoice_total_enc, total_vat_enc);

            let binary = '';
            for (let i = 0; i < str_to_encode.length; i++) {
                binary += String.fromCharCode(str_to_encode[i]);
            }
            return btoa(binary);
        },

        _compute_qr_code_field(tag, field) {
            const textEncoder = new TextEncoder();
            const name_byte_array = Array.from(textEncoder.encode(field));
            const name_tag_encoding = [tag];
            const name_length_encoding = [name_byte_array.length];
            return name_tag_encoding.concat(name_length_encoding, name_byte_array);
        },

    });

    models.load_fields("pos.payment.method", ["arabic_translate"]);

    var _super_paymentline = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        initialize: function(attributes, options) {
            _super_paymentline.initialize.apply(this, arguments);
            this.arabic_translate = this.payment_method.arabic_translate;
        },
        export_for_printing: function() {
            var paymentline = _super_paymentline.export_for_printing.apply(this, arguments);
            paymentline['arabic_translate'] = this.arabic_translate;

            return paymentline;
        },
    });
});