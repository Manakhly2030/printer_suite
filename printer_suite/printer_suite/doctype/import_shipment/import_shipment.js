frappe.ui.form.on("Import Shipment", {
    setup(frm) {
        frm.set_query("purchase_order", function() {
            if (!frm.doc.supplier) {
                return {};
            }

            return {
                filters: {
                    supplier: frm.doc.supplier,
                    docstatus: 1,
                    status: ["not in", ["Closed", "Completed", "Cancelled"]]
                }
            };
        });

        frm.set_query("item_code", "items", function() {
            return {
                filters: {
                    disabled: 0,
                    is_stock_item: 1
                }
            };
        });
    },

    onload(frm) {
        apply_import_export_settings(frm);
    },

    refresh(frm) {
        calculate_import_shipment(frm);

        if (frm.doc.docstatus !== 0) return;

        add_purchase_buttons(frm);
        add_landed_cost_buttons(frm);
    },

    supplier(frm) {
        frm.set_value("purchase_order", "");
    },

    shipping_cost(frm) {
        calculate_import_shipment(frm);
    },

    customs_duty(frm) {
        calculate_import_shipment(frm);
    },

    vat_amount(frm) {
        calculate_import_shipment(frm);
    },

    inland_transport(frm) {
        calculate_import_shipment(frm);
    },

    other_charges(frm) {
        calculate_import_shipment(frm);
    }
});

frappe.ui.form.on("Import Shipment Item", {
    item_code(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.item_code) return;

        frappe.db.get_value("Item", row.item_code, ["item_name", "stock_uom"], function(r) {
            if (r) {
                row.description = r.item_name || "";
                row.uom = r.stock_uom || "";
                frm.refresh_field("items");
                calculate_import_shipment(frm);
            }
        });
    },

    qty(frm, cdt, cdn) {
        calculate_import_shipment(frm);
    },

    purchase_rate(frm, cdt, cdn) {
        calculate_import_shipment(frm);
    },

    items_add(frm, cdt, cdn) {
        calculate_import_shipment(frm);
    },

    items_remove(frm) {
        calculate_import_shipment(frm);
    }
});

function add_purchase_buttons(frm) {
    const group = __("Purchase");

    if (frm.doc.purchase_order) {
        frm.add_custom_button(__("Get Items from Purchase Order"), async () => {
            if (frm.is_dirty()) {
                await frm.save();
            }

            frappe.call({
                method: "printer_suite.printer_suite.doctype.import_shipment.import_shipment.get_items_from_purchase_order",
                args: {
                    purchase_order: frm.doc.purchase_order
                },
                freeze: true,
                freeze_message: "Fetching Purchase Order Items...",
                callback: function(r) {
                    let items = r.message || [];

                    if (!items.length) {
                        frappe.msgprint("No items found in Purchase Order.");
                        return;
                    }

                    frm.clear_table("items");

                    items.forEach(d => {
                        let row = frm.add_child("items");
                        row.item_code = d.item_code || "";
                        row.description = d.description || "";
                        row.qty = d.qty || 0;
                        row.uom = d.uom || "";
                        row.purchase_rate = d.purchase_rate || 0;
                        row.purchase_amount = d.purchase_amount || 0;
                        row.allocated_landed_cost = d.allocated_landed_cost || 0;
                        row.final_unit_cost = d.final_unit_cost || 0;
                        row.final_total_cost = d.final_total_cost || 0;
                        row.purchase_order_item = d.purchase_order_item || "";
                    });

                    frm.refresh_field("items");
                    calculate_import_shipment(frm);

                    frappe.show_alert({
                        message: "Items loaded from Purchase Order.",
                        indicator: "green"
                    });
                }
            });
        }, group);
    }

    if (frm.doc.supplier && frm.doc.target_warehouse && (frm.doc.items || []).length) {
        frm.add_custom_button(__("Create Purchase Receipt"), async () => {
            if (frm.is_dirty()) {
                await frm.save();
            }

            frappe.call({
                method: "printer_suite.printer_suite.doctype.import_shipment.import_shipment.create_purchase_receipt",
                args: {
                    docname: frm.doc.name
                },
                freeze: true,
                freeze_message: "Creating Draft Purchase Receipt...",
                callback: function(r) {
                    if (!r.message) return;

                    frappe.show_alert({
                        message: "Draft Purchase Receipt created: " + r.message,
                        indicator: "green"
                    });

                    frm.reload_doc();
                }
            });
        }, group);
    }

    if (frm.doc.purchase_receipt) {
        frm.add_custom_button(__("Open Last Purchase Receipt"), () => {
            frappe.set_route("Form", "Purchase Receipt", frm.doc.purchase_receipt);
        }, group);
    }

    if (frm.doc.linked_purchase_receipts) {
        frm.add_custom_button(__("Open All Purchase Receipts"), () => {
            open_all_purchase_receipts(frm);
        }, group);
    }
}

function add_landed_cost_buttons(frm) {
    const group = __("Landed Cost");

    frm.add_custom_button(__("Create Landed Cost Voucher"), async () => {
        if (frm.is_dirty()) {
            await frm.save();
        }

        create_lcv_with_pr_selection(frm);
    }, group);

    if (frm.doc.landed_cost_voucher) {
        frm.add_custom_button(__("Open Last Landed Cost Voucher"), () => {
            frappe.set_route("Form", "Landed Cost Voucher", frm.doc.landed_cost_voucher);
        }, group);
    }

    frm.add_custom_button(__("Open All Landed Cost Vouchers"), () => {
        open_all_landed_cost_vouchers(frm);
    }, group);
}

function apply_import_export_settings(frm) {
    frappe.call({
        method: "printer_suite.printer_suite.doctype.import_shipment.import_shipment.get_import_export_settings_data",
        callback: function(r) {
            let d = r.message || {};
            let changed = false;

            if (!frm.doc.target_warehouse && d.default_import_warehouse) {
                frm.set_value("target_warehouse", d.default_import_warehouse);
                changed = true;
            }

            if (!frm.doc.port_of_loading && d.default_port_of_loading) {
                frm.set_value("port_of_loading", d.default_port_of_loading);
                changed = true;
            }

            if (!frm.doc.port_of_arrival && d.default_port_of_arrival) {
                frm.set_value("port_of_arrival", d.default_port_of_arrival);
                changed = true;
            }

            if (!frm.doc.shipping_method && d.default_shipping_method) {
                frm.set_value("shipping_method", d.default_shipping_method);
                changed = true;
            }

            if (changed) {
                calculate_import_shipment(frm);
            }
        }
    });
}

function create_lcv_with_pr_selection(frm) {
    frappe.call({
        method: "printer_suite.printer_suite.doctype.import_shipment.import_shipment.get_linked_purchase_receipts",
        args: {
            docname: frm.doc.name
        },
        freeze: true,
        freeze_message: "Checking linked Purchase Receipts...",
        callback: function(r) {
            let receipts = r.message || [];

            if (!receipts.length) {
                frappe.msgprint("No Purchase Receipt found for this Import Shipment. Please create or link one first.");
                return;
            }

            if (receipts.length === 1) {
                create_lcv(frm, receipts[0]);
                return;
            }

            let dialog = new frappe.ui.Dialog({
                title: "Select Purchase Receipt",
                fields: [
                    {
                        fieldname: "purchase_receipt",
                        fieldtype: "Select",
                        label: "Purchase Receipt",
                        options: receipts.join("\n"),
                        reqd: 1
                    }
                ],
                primary_action_label: "Create Landed Cost Voucher",
                primary_action(values) {
                    dialog.hide();
                    create_lcv(frm, values.purchase_receipt);
                }
            });

            dialog.show();
        }
    });
}

function create_lcv(frm, purchase_receipt) {
    frappe.call({
        method: "printer_suite.printer_suite.doctype.import_shipment.import_shipment.create_landed_cost_voucher",
        args: {
            docname: frm.doc.name,
            purchase_receipt: purchase_receipt
        },
        freeze: true,
        freeze_message: "Creating Draft Landed Cost Voucher...",
        callback: function(r) {
            if (!r.message) return;

            if (r.message.already_exists) {
                frappe.warn(
                    "Landed Cost Voucher Already Exists",
                    `An existing Landed Cost Voucher was found: ${r.message.existing_lcv}`,
                    () => {
                        frappe.set_route("Form", "Landed Cost Voucher", r.message.existing_lcv);
                    },
                    "Open Existing"
                );
                return;
            }

            let lcv_name = r.message.landed_cost_voucher;
            let capitalize_vat = r.message.capitalize_vat_in_inventory;

            let msg = `Draft Landed Cost Voucher created: ${lcv_name}`;
            if (!capitalize_vat && toFloat(frm.doc.vat_amount) > 0) {
                msg += " | VAT was excluded from inventory cost as per Import Export Settings.";
            }

            frappe.show_alert({
                message: msg,
                indicator: "green"
            });

            frm.reload_doc();
            frappe.set_route("Form", "Landed Cost Voucher", lcv_name);
        }
    });
}

function toFloat(value) {
    const num = parseFloat(value);
    return isNaN(num) ? 0 : num;
}

function calculate_import_shipment(frm) {
    let total_landed_cost =
        toFloat(frm.doc.shipping_cost) +
        toFloat(frm.doc.customs_duty) +
        toFloat(frm.doc.vat_amount) +
        toFloat(frm.doc.inland_transport) +
        toFloat(frm.doc.other_charges);

    frm.set_value("total_landed_cost", total_landed_cost);

    let total_qty = 0;

    (frm.doc.items || []).forEach(row => {
        row.purchase_amount = toFloat(row.qty) * toFloat(row.purchase_rate);
        total_qty += toFloat(row.qty);
    });

    frm.set_value("total_qty", total_qty);

    (frm.doc.items || []).forEach(row => {
        if (total_qty > 0) {
            row.allocated_landed_cost = (toFloat(row.qty) / total_qty) * total_landed_cost;
        } else {
            row.allocated_landed_cost = 0;
        }

        if (toFloat(row.qty) > 0) {
            row.final_unit_cost = toFloat(row.purchase_rate) + (toFloat(row.allocated_landed_cost) / toFloat(row.qty));
        } else {
            row.final_unit_cost = toFloat(row.purchase_rate);
        }

        row.final_total_cost = toFloat(row.purchase_amount) + toFloat(row.allocated_landed_cost);
    });

    frm.refresh_field("items");
}

function open_all_purchase_receipts(frm) {
    frappe.route_options = {
        custom_import_shipment: frm.doc.name
    };
    frappe.set_route("List", "Purchase Receipt");
}

function open_all_landed_cost_vouchers(frm) {
    frappe.route_options = {
        custom_import_shipment: frm.doc.name
    };
    frappe.set_route("List", "Landed Cost Voucher");
}
