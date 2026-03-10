import frappe

def on_submit(doc, method=None):
    """
    When a Purchase Receipt is submitted, optionally link it back to Import Shipment.
    Requires a custom field on Purchase Receipt called 'shipment_reference'.
    """
    shipment_reference = getattr(doc, "shipment_reference", None)
    if not shipment_reference:
        return

    if not frappe.db.exists("Import Shipment", shipment_reference):
        frappe.throw(f"Import Shipment {shipment_reference} does not exist.")

    shipment = frappe.get_doc("Import Shipment", shipment_reference)

    existing = shipment.get("linked_purchase_receipts") or ""
    refs = [x.strip() for x in existing.split(",") if x.strip()]

    if doc.name not in refs:
        refs.append(doc.name)
        shipment.db_set("linked_purchase_receipts", ", ".join(refs))
