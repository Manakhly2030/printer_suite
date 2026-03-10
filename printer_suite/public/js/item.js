frappe.ui.form.on("Item", {
    refresh(frm) {
        if (frm.doc.item_group === "Printers") {
            if (!frm.doc.has_serial_no) frm.set_value("has_serial_no", 1);
            if (!frm.doc.is_stock_item) frm.set_value("is_stock_item", 1);
            if (!frm.doc.stock_uom) frm.set_value("stock_uom", "Unit");
            if (!frm.doc.custom_printing_suite) frm.set_value("custom_printing_suite", 1);
        }

        toggle_item_fields(frm);

        if (frm.doc.custom_is_printer) {
            frm.add_custom_button("Add Spare Part", async () => {
                await open_or_create_printer_compatibility(frm, true);
            }, __("Spare Parts"));

            frm.add_custom_button("Show Spare Parts", async () => {
                await show_printer_compatibility(frm);
            }, __("Spare Parts"));
        }
    },

    item_group(frm) {
        if (frm.doc.item_group === "Printers") {
            frm.set_value("is_stock_item", 1);
            frm.set_value("has_serial_no", 1);
            frm.set_value("stock_uom", "Unit");
            frm.set_value("custom_printing_suite", 1);
        }

        if (frm.doc.item_group === "Services") {
            frm.set_value("is_stock_item", 0);
            frm.set_value("has_serial_no", 0);
            frm.set_value("is_sales_item", 1);
            frm.set_value("is_purchase_item", 0);
        }
    },

    custom_is_printer(frm) {
        toggle_item_fields(frm);
    },

    custom_is_spare_part(frm) {
        toggle_item_fields(frm);
    }
});

function toggle_item_fields(frm) {
    if (frm.doc.custom_is_printer) {
        frm.set_df_property("custom_is_spare_part", "hidden", 1);
        if (frm.doc.custom_is_spare_part) frm.set_value("custom_is_spare_part", 0);
    } else {
        frm.set_df_property("custom_is_spare_part", "hidden", 0);
    }

    if (frm.doc.custom_is_spare_part) {
        frm.set_df_property("custom_is_printer", "hidden", 1);
        if (frm.doc.custom_is_printer) frm.set_value("custom_is_printer", 0);
    } else {
        frm.set_df_property("custom_is_printer", "hidden", 0);
    }
}

async function open_or_create_printer_compatibility(frm, go_to_items) {
    if (!frm.doc.name) {
        frappe.msgprint(__("Please save the Item first."));
        return;
    }

    let result = await frappe.db.get_list("Printer Compatibility", {
        filters: { printer_item: frm.doc.name },
        fields: ["name"],
        limit: 1
    });

    if (result.length) {
        await frappe.set_route("Form", "Printer Compatibility", result[0].name);

        if (go_to_items) {
            frappe.after_ajax(() => {
                setTimeout(() => {
                    if (cur_frm && cur_frm.fields_dict.items) {
                        cur_frm.scroll_to_field("items");
                    }
                }, 600);
            });
        }
    } else {
        frappe.new_doc("Printer Compatibility", {
            printer_item: frm.doc.name
        });

        if (go_to_items) {
            frappe.after_ajax(() => {
                setTimeout(() => {
                    if (cur_frm && cur_frm.fields_dict.items) {
                        cur_frm.scroll_to_field("items");
                    }
                }, 600);
            });
        }
    }
}

async function show_printer_compatibility(frm) {
    if (!frm.doc.name) {
        frappe.msgprint(__("Please save the Item first."));
        return;
    }

    let result = await frappe.db.get_list("Printer Compatibility", {
        filters: { printer_item: frm.doc.name },
        fields: ["name"],
        limit: 1
    });

    if (result.length) {
        frappe.set_route("Form", "Printer Compatibility", result[0].name);
    } else {
        frappe.msgprint(__("No Printer Compatibility found for this printer."));
    }
}
