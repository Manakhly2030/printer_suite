import frappe


def on_submit(doc, method=None):
    for row in doc.items:
        if not row.serial_no:
            continue

        serials = [x.strip() for x in row.serial_no.split("\n") if x.strip()]

        for sn in serials:
            if not frappe.db.exists("Serial No", sn):
                continue

            values = {}

            if doc.stock_entry_type == "Material Transfer":
                if frappe.db.has_column("Serial No", "custom_refurbishment_status"):
                    values["custom_refurbishment_status"] = "In Stock"

                if frappe.db.has_column("Serial No", "custom_unit_condition"):
                    values["custom_unit_condition"] = "Refurbished"

                if frappe.db.has_column("Serial No", "custom_last_refurbishment_date"):
                    values["custom_last_refurbishment_date"] = frappe.utils.nowdate()

            if values:
                frappe.db.set_value("Serial No", sn, values)
