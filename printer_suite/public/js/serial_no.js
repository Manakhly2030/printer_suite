frappe.ui.form.on("Serial No", {
    refresh(frm) {
        if (frm.doc.item_code) {
            frm.add_custom_button("New Refurbishment Job", function () {
                frappe.new_doc("Refurbishment Job", {
                    serial_no: frm.doc.name,
                    item_code: frm.doc.item_code
                });
            });
        }
    }
});
