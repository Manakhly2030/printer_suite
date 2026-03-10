import frappe

@frappe.whitelist()
def get_compatible_items(printer_item):
    compatibility_docs = frappe.get_all(
        "Printer Compatibility",
        filters={"printer_item": printer_item},
        pluck="name"
    )

    if not compatibility_docs:
        return []

    result = frappe.get_all(
        "Printer Compatibility Item",
        filters={"parent": ["in", compatibility_docs]},
        fields=["compatible_item", "item_type", "notes"]
    )
    return result
