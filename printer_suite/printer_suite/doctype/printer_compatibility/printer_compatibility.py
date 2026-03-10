import frappe
from frappe.model.document import Document

class PrinterCompatibility(Document):
    def validate(self):
        if not self.printer_item:
            frappe.throw("Printer Item is required.")

        if not self.items:
            frappe.throw("Please add at least one compatible item.")

        seen = set()
        item = frappe.get_doc("Item", self.printer_item)
        self.printer_brand = item.custom_printer_brand or ''
        self.printer_model = item.custom_printer_model or ''

        for row in self.items:
            key = row.compatible_item
            if key in seen:
                frappe.throw(f"Duplicate compatible item found: {key}")
            seen.add(key)

            if row.compatible_item:
                c_item = frappe.get_doc("Item", row.compatible_item)
                row.compatible_brand = c_item.custom_printer_brand or ''
                row.compatible_model = c_item.custom_printer_model or ''
