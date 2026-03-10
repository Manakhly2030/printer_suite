// Copyright (c) 2026, Manakhly and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Import Export Settings", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on("Import Export Settings", {

    setup(frm) {

        const expense_accounts = function() {
            return {
                filters: {
                    is_group: 0,
                    root_type: "Expense"
                }
            };
        };

        const vat_accounts = function() {
            return {
                filters: {
                    is_group: 0,
                    root_type: "Asset"
                }
            };
        };

        frm.set_query("default_shipping_account", expense_accounts);
        frm.set_query("default_customs_duty_account", expense_accounts);
        frm.set_query("default_inland_transport_account", expense_accounts);
        frm.set_query("default_other_charges_account", expense_accounts);

        frm.set_query("default_import_vat_account", vat_accounts);

    }

});
