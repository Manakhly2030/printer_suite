frappe.ui.form.on("Purchase Receipt", {
    refresh(frm) {
        if (frm.doc.custom_shipment_reference) {
            frm.add_custom_button("Open Import Shipment", function () {
                frappe.set_route("Form", "Import Shipment", frm.doc.custom_shipment_reference);
            });
        }
    }
});
