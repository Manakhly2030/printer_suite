frappe.ui.form.on("Printer Compatibility", {

    setup(frm) {
        frm.set_query("printer_item", function() {
            return { filters: { item_group: "Printers" } };
        });

        frm.set_query("compatible_item", "items", function(doc, cdt, cdn) {
            let row = locals[cdt][cdn] || {};
            let filters = { custom_is_spare_part: 1 };

            if (row.item_type) {
                filters.custom_spare_part_type = row.item_type;
            }

            return { filters: filters };
        });
    },

    refresh(frm) {
        frm.fields_dict.printer_item.new_doc = function() {
            frappe.new_doc("Item", {
                item_group: "Printers",
                stock_uom: "Unit",
                is_stock_item: 1
            });
        };

        frm.fields_dict.items.grid.get_field("compatible_item").get_route_options_for_new_doc = function(doc, cdt, cdn) {
            let row = locals[cdt][cdn] || {};
            let options = {
                item_group: "Spare Parts",
                stock_uom: "Nos",
                is_stock_item: 1,
                custom_is_spare_part: 1
            };

            if (row.item_type) {
                options.custom_spare_part_type = row.item_type;
            }

            return options;
        };
    },

    printer_item(frm) {
        if (frm.doc.printer_item) {
            frappe.db.get_value('Item', frm.doc.printer_item, ['custom_printer_brand', 'custom_printer_model'], (r) => {
                if (!r) return;
                frm.set_value('printer_brand', r.custom_printer_brand || '');
                frm.set_value('printer_model', r.custom_printer_model || '');
            });
        } else {
            frm.set_value('printer_brand', '');
            frm.set_value('printer_model', '');
        }
    }

});

frappe.ui.form.on("Printer Compatibility Item", {

    compatible_item(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.compatible_item) {
            frappe.db.get_value('Item', row.compatible_item, ['custom_printer_brand', 'custom_printer_model'], (r) => {
                if (!r) return;
                frappe.model.set_value(cdt, cdn, 'compatible_brand', r.custom_printer_brand || '');
                frappe.model.set_value(cdt, cdn, 'compatible_model', r.custom_printer_model || '');
            });
        } else {
            frappe.model.set_value(cdt, cdn, 'compatible_brand', '');
            frappe.model.set_value(cdt, cdn, 'compatible_model', '');
        }
    }

});
