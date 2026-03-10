frappe.ui.form.on("Refurbishment Job", {
    setup(frm) {
        frm.set_query("printer_item", function() {
            return {
                filters: {
                    item_group: "Printers"
                }
            };
        });

        frm.set_query("serial_no", function() {
            if (!frm.doc.printer_item) {
                return {
                    filters: {
                        name: ["=", ""]
                    }
                };
            }

            return {
                filters: {
                    item_code: frm.doc.printer_item
                }
            };
        });

        frm.set_query("item_code", "spare_parts", function(doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            let filters = {
                custom_is_spare_part: 1
            };

            if (row.spare_part_type) {
                filters.custom_spare_part_type = row.spare_part_type;
            }

            return { filters: filters };
        });
    },

    onload(frm) {
        cleanup_duplicated_doc(frm);
    },

    printer_item(frm) {
        frm.set_value("serial_no", "");
    },

    refresh(frm) {
        if (frm.doc.docstatus !== 0) return;

        if (frm.doc.printer_item && !frm.doc.material_issue_entry) {
            frm.add_custom_button("Suggest Spare Parts", () => {
                open_spare_parts_dialog(frm);
            });
        }

        if (!frm.doc.material_issue_entry && (frm.doc.spare_parts || []).length) {
            frm.add_custom_button("Create Material Issue", async () => {
                if (frm.is_dirty()) {
                    await frm.save();
                }

                frappe.call({
                    method: "printer_suite.printer_suite.doctype.refurbishment_job.refurbishment_job.create_material_issue_entry",
                    args: {
                        docname: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: "Creating Material Issue...",
                    callback: function(r) {
                        if (!r.message) return;

                        frappe.show_alert({
                            message: "Material Issue created: " + r.message,
                            indicator: "green"
                        });

                        frm.reload_doc();
                    }
                });
            });
        }

        if (
            frm.doc.status !== "Cancelled" &&
            frm.doc.qc_result === "Passed" &&
            frm.doc.target_warehouse &&
            frm.doc.printer_item &&
            frm.doc.serial_no &&
            !frm.doc.transfer_entry
        ) {
            frm.add_custom_button("Transfer to Ready Warehouse", async () => {
                if (frm.is_dirty()) {
                    await frm.save();
                }

                frappe.call({
                    method: "printer_suite.printer_suite.doctype.refurbishment_job.refurbishment_job.create_transfer_entry",
                    args: {
                        docname: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: "Creating Transfer Entry...",
                    callback: function(r) {
                        if (!r.message) return;

                        frappe.show_alert({
                            message: "Transfer Entry created: " + r.message,
                            indicator: "green"
                        });

                        frm.reload_doc();
                    }
                });
            });
        }
    },

    labor_cost(frm) {
        calculate_totals(frm);
    },

    other_cost(frm) {
        calculate_totals(frm);
    }
});

frappe.ui.form.on("Refurbishment Job Item", {
    qty(frm, cdt, cdn) {
        calculate_row(frm, cdt, cdn);
    },

    rate(frm, cdt, cdn) {
        calculate_row(frm, cdt, cdn);
    },

    spare_part_type(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.item_code = "";
        row.description = "";
        row.rate = 0;
        row.amount = 0;
        frm.refresh_field("spare_parts");
        calculate_totals(frm);
    },

    item_code(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.item_code) return;

        frappe.db.get_value("Item", row.item_code, ["item_name", "stock_uom", "standard_rate"], function(r) {
            if (r) {
                row.description = r.item_name || "";
                row.uom = r.stock_uom || "Nos";
                row.rate = r.standard_rate || 0;
                row.amount = (row.qty || 0) * (row.rate || 0);
                frm.refresh_field("spare_parts");
                calculate_totals(frm);
            }
        });
    },

    spare_parts_remove(frm) {
        calculate_totals(frm);
    }
});

function cleanup_duplicated_doc(frm) {
    if (!frm.is_new()) return;
    if (frm.__duplicate_cleanup_done) return;

    const looks_duplicated =
        !!frm.doc.material_issue_entry ||
        !!frm.doc.transfer_entry ||
        !!frm.doc.sales_invoice ||
        !!frm.doc.inspection_date ||
        !!frm.doc.completion_date ||
        !!frm.doc.intake_date ||
        (frm.doc.status && frm.doc.status !== "Draft") ||
        (frm.doc.qc_result && frm.doc.qc_result !== "Pending") ||
        !!frm.doc.ready_for_sale;

    if (!looks_duplicated) return;

    frm.__duplicate_cleanup_done = true;

    frm.set_value("status", "Draft");
    frm.set_value("intake_date", null);
    frm.set_value("inspection_date", null);
    frm.set_value("completion_date", null);
    frm.set_value("material_issue_entry", null);
    frm.set_value("transfer_entry", null);
    frm.set_value("sales_invoice", null);
    frm.set_value("ready_for_sale", 0);
    frm.set_value("qc_result", "Pending");

    calculate_totals(frm);
}

function open_spare_parts_dialog(frm) {
    frappe.call({
        method: "printer_suite.printer_suite.doctype.refurbishment_job.refurbishment_job.get_spare_part_options",
        args: {
            printer_item: frm.doc.printer_item,
            source_warehouse: frm.doc.source_warehouse
        },
        freeze: true,
        freeze_message: "Fetching suggested spare parts...",
        callback: function(r) {
            let data = r.message || [];

            if (!data.length) {
                frappe.msgprint("No spare parts suggestions found for this printer.");
                return;
            }

            let dialog = new frappe.ui.Dialog({
                title: "Select Spare Parts",
                size: "extra-large",
                fields: [
                    {
                        fieldname: "parts_table",
                        fieldtype: "Table",
                        label: "Suggested Spare Parts",
                        cannot_add_rows: true,
                        in_place_edit: true,
                        fields: [
                            {
                                fieldname: "select_item",
                                fieldtype: "Check",
                                label: "Select",
                                in_list_view: 1,
                                columns: 1
                            },
                            {
                                fieldname: "spare_part_type",
                                fieldtype: "Data",
                                label: "Spare Part Type",
                                read_only: 1,
                                in_list_view: 1,
                                columns: 2
                            },
                            {
                                fieldname: "item_code",
                                fieldtype: "Data",
                                label: "Item Code",
                                read_only: 1,
                                in_list_view: 1,
                                columns: 2
                            },
                            {
                                fieldname: "description",
                                fieldtype: "Data",
                                label: "Description",
                                read_only: 1,
                                in_list_view: 1,
                                columns: 3
                            },
                            {
                                fieldname: "qty",
                                fieldtype: "Float",
                                label: "Qty",
                                default: 1,
                                in_list_view: 1,
                                columns: 1
                            },
                            {
                                fieldname: "rate",
                                fieldtype: "Currency",
                                label: "Rate",
                                in_list_view: 1,
                                columns: 2
                            },
                            {
                                fieldname: "uom",
                                fieldtype: "Data",
                                label: "UOM",
                                read_only: 1,
                                in_list_view: 1,
                                columns: 1
                            },
                            {
                                fieldname: "price_source",
                                fieldtype: "Data",
                                label: "Price Source",
                                read_only: 1,
                                in_list_view: 1,
                                columns: 2
                            }
                        ],
                        data: data.map(d => ({
                            select_item: 1,
                            spare_part_type: d.spare_part_type || "",
                            item_code: d.item_code || "",
                            description: d.description || "",
                            qty: 1,
                            rate: d.rate || 0,
                            uom: d.uom || "Nos",
                            price_source: d.price_source || "No Cost Found"
                        }))
                    }
                ],
                primary_action_label: "Add Selected",
                primary_action(values) {
                    let selected = (values.parts_table || []).filter(row => row.select_item && row.item_code);

                    if (!selected.length) {
                        frappe.msgprint("Please select at least one spare part.");
                        return;
                    }

                    let existing_items = new Set(
                        (frm.doc.spare_parts || [])
                            .filter(row => row.item_code)
                            .map(row => row.item_code)
                    );

                    let first_affected_row_name = null;
                    let added_count = 0;
                    let updated_count = 0;

                    selected.forEach(d => {
                        if (!d.item_code) return;

                        let target_row =
                            (frm.doc.spare_parts || []).find(row =>
                                row.spare_part_type === d.spare_part_type && !row.item_code
                            ) ||
                            (frm.doc.spare_parts || []).find(row =>
                                row.spare_part_type === d.spare_part_type && row.item_code === d.item_code
                            );

                        if (target_row) {
                            if (!target_row.item_code || target_row.item_code === d.item_code) {
                                target_row.spare_part_type = d.spare_part_type || target_row.spare_part_type || "";
                                target_row.item_code = d.item_code || target_row.item_code || "";
                                target_row.description = d.description || target_row.description || "";
                                target_row.qty = target_row.qty || d.qty || 1;
                                target_row.uom = d.uom || target_row.uom || "Nos";
                                target_row.rate = d.rate || target_row.rate || 0;
                                target_row.amount = (target_row.qty || 0) * (target_row.rate || 0);
                                target_row.source_warehouse = target_row.source_warehouse || frm.doc.source_warehouse || "";

                                if (!first_affected_row_name) {
                                    first_affected_row_name = target_row.name;
                                }

                                existing_items.add(d.item_code);
                                updated_count++;
                                return;
                            }
                        }

                        if (existing_items.has(d.item_code)) {
                            return;
                        }

                        let row = frm.add_child("spare_parts");
                        row.spare_part_type = d.spare_part_type || "";
                        row.item_code = d.item_code || "";
                        row.description = d.description || "";
                        row.qty = d.qty || 1;
                        row.uom = d.uom || "Nos";
                        row.rate = d.rate || 0;
                        row.amount = (row.qty || 0) * (row.rate || 0);
                        row.source_warehouse = frm.doc.source_warehouse || "";

                        if (!first_affected_row_name) {
                            first_affected_row_name = row.name;
                        }

                        existing_items.add(d.item_code);
                        added_count++;
                    });

                    frm.refresh_field("spare_parts");
                    calculate_totals(frm);
                    dialog.hide();

                    frappe.show_alert({
                        message: `Spare parts applied. Added: ${added_count}, Updated: ${updated_count}`,
                        indicator: "green"
                    });

                    if (first_affected_row_name) {
                        setTimeout(() => {
                            scroll_to_child_table(frm);
                        }, 300);
                    }
                }
            });

            dialog.show();
        }
    });
}

function calculate_row(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    row.amount = (row.qty || 0) * (row.rate || 0);
    frm.refresh_field("spare_parts");
    calculate_totals(frm);
}

function calculate_totals(frm) {
    let total_parts_cost = 0;

    (frm.doc.spare_parts || []).forEach(row => {
        total_parts_cost += row.amount || 0;
    });

    frm.set_value("parts_cost", total_parts_cost);

    let total =
        (total_parts_cost || 0) +
        (frm.doc.labor_cost || 0) +
        (frm.doc.other_cost || 0);

    frm.set_value("total_refurbishment_cost", total);
}

function scroll_to_child_table(frm) {
    let field = frm.fields_dict.spare_parts;
    if (!field || !field.$wrapper) return;

    $("html, body").animate({
        scrollTop: field.$wrapper.offset().top - 120
    }, 400);
}
