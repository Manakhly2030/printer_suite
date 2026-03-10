import frappe
from frappe.model.document import Document
from frappe import _


class ImportShipment(Document):
    def validate(self):
        self.set_defaults_from_settings()
        self.calculate_totals()

    def set_defaults_from_settings(self):
        settings = get_import_export_settings()

        if not self.target_warehouse and settings.get("default_import_warehouse"):
            self.target_warehouse = settings.get("default_import_warehouse")

        if not self.port_of_loading and settings.get("default_port_of_loading"):
            self.port_of_loading = settings.get("default_port_of_loading")

        if not self.port_of_arrival and settings.get("default_port_of_arrival"):
            self.port_of_arrival = settings.get("default_port_of_arrival")

        if not self.shipping_method and settings.get("default_shipping_method"):
            self.shipping_method = settings.get("default_shipping_method")

    def calculate_totals(self):
        self.total_landed_cost = (
            flt(self.shipping_cost)
            + flt(self.customs_duty)
            + flt(self.vat_amount)
            + flt(self.inland_transport)
            + flt(self.other_charges)
        )

        total_qty = 0.0

        for row in self.items or []:
            row.purchase_amount = flt(row.qty) * flt(row.purchase_rate)
            total_qty += flt(row.qty)

        self.total_qty = total_qty

        for row in self.items or []:
            if total_qty > 0:
                row.allocated_landed_cost = (flt(row.qty) / total_qty) * flt(self.total_landed_cost)
            else:
                row.allocated_landed_cost = 0

            if flt(row.qty) > 0:
                row.final_unit_cost = flt(row.purchase_rate) + (flt(row.allocated_landed_cost) / flt(row.qty))
            else:
                row.final_unit_cost = flt(row.purchase_rate)

            row.final_total_cost = flt(row.purchase_amount) + flt(row.allocated_landed_cost)


@frappe.whitelist()
def get_import_export_settings_data():
    return get_import_export_settings()


@frappe.whitelist()
def get_items_from_purchase_order(purchase_order):
    if not purchase_order:
        return []

    po = frappe.get_doc("Purchase Order", purchase_order)

    if po.docstatus != 1:
        frappe.throw(_("Purchase Order must be submitted."))

    items = []
    for row in po.items:
        items.append({
            "item_code": row.item_code,
            "description": row.description or row.item_name,
            "qty": row.qty,
            "uom": row.uom,
            "purchase_rate": row.rate or 0,
            "purchase_amount": flt(row.qty) * flt(row.rate or 0),
            "allocated_landed_cost": 0,
            "final_unit_cost": row.rate or 0,
            "final_total_cost": flt(row.qty) * flt(row.rate or 0),
            "purchase_order_item": row.name
        })

    return items


@frappe.whitelist()
def create_purchase_receipt(docname):
    doc = frappe.get_doc("Import Shipment", docname)

    if not doc.supplier:
        frappe.throw(_("Supplier is required."))

    if not doc.target_warehouse:
        frappe.throw(_("Target Warehouse is required."))

    if not doc.items:
        frappe.throw(_("Please add shipment items first."))

    po_item_map = {}
    po_doc = None

    if doc.purchase_order:
        po_doc = frappe.get_doc("Purchase Order", doc.purchase_order)

        if po_doc.docstatus != 1:
            frappe.throw(_("Purchase Order must be submitted."))

        for row in po_doc.items:
            po_item_map.setdefault(row.item_code, []).append(row)

    pr_items = []

    for row in doc.items:
        if not row.item_code or not row.qty:
            continue

        pr_row = {
            "item_code": row.item_code,
            "qty": row.qty,
            "uom": row.uom,
            "stock_uom": row.uom,
            "warehouse": doc.target_warehouse,
            "rate": row.purchase_rate or 0
        }

        if doc.purchase_order:
            matched_po_row = None
            if row.item_code in po_item_map and po_item_map[row.item_code]:
                matched_po_row = po_item_map[row.item_code][0]

            if matched_po_row:
                pr_row.update({
                    "purchase_order": doc.purchase_order,
                    "purchase_order_item": matched_po_row.name
                })

        pr_items.append(pr_row)

    if not pr_items:
        frappe.throw(_("No valid shipment items found."))

    pr_data = {
        "doctype": "Purchase Receipt",
        "supplier": doc.supplier,
        "items": pr_items
    }

    if frappe.db.has_column("Purchase Receipt", "custom_import_shipment"):
        pr_data["custom_import_shipment"] = doc.name

    if po_doc:
        pr_data["company"] = po_doc.company
        if getattr(po_doc, "currency", None):
            pr_data["currency"] = po_doc.currency
        if getattr(po_doc, "conversion_rate", None):
            pr_data["conversion_rate"] = po_doc.conversion_rate
        if getattr(po_doc, "buying_price_list", None):
            pr_data["buying_price_list"] = po_doc.buying_price_list
        if getattr(po_doc, "set_warehouse", None) and not doc.target_warehouse:
            for d in pr_items:
                d["warehouse"] = po_doc.set_warehouse

    purchase_receipt = frappe.get_doc(pr_data)

    if hasattr(purchase_receipt, "set_missing_values"):
        purchase_receipt.run_method("set_missing_values")

    if hasattr(purchase_receipt, "calculate_taxes_and_totals"):
        purchase_receipt.run_method("calculate_taxes_and_totals")

    purchase_receipt.insert()

    updates = {}

    if frappe.db.has_column("Import Shipment", "purchase_receipt"):
        updates["purchase_receipt"] = purchase_receipt.name

    if frappe.db.has_column("Import Shipment", "linked_purchase_receipts"):
        old_value = (doc.linked_purchase_receipts or "").strip()
        receipt_list = [x.strip() for x in old_value.split(",") if x.strip()]

        if purchase_receipt.name not in receipt_list:
            receipt_list.append(purchase_receipt.name)

        updates["linked_purchase_receipts"] = ", ".join(receipt_list)

    if updates:
        doc.db_set(updates)

    return purchase_receipt.name


@frappe.whitelist()
def get_linked_purchase_receipts(docname):
    doc = frappe.get_doc("Import Shipment", docname)

    receipts = []
    seen = set()

    if getattr(doc, "purchase_receipt", None):
        seen.add(doc.purchase_receipt)
        receipts.append(doc.purchase_receipt)

    linked = (getattr(doc, "linked_purchase_receipts", "") or "").strip()
    for name in [x.strip() for x in linked.split(",") if x.strip()]:
        if name not in seen:
            seen.add(name)
            receipts.append(name)

    return receipts


@frappe.whitelist()
def create_landed_cost_voucher(docname, purchase_receipt=None):
    doc = frappe.get_doc("Import Shipment", docname)

    if not purchase_receipt:
        purchase_receipts = get_linked_purchase_receipts(docname)

        if not purchase_receipts:
            frappe.throw(_("Please create or link a Purchase Receipt first."))

        if len(purchase_receipts) > 1:
            frappe.throw(_("Multiple Purchase Receipts found. Please select one."))

        purchase_receipt = purchase_receipts[0]

    existing_lcv = get_existing_lcv_for_purchase_receipt(purchase_receipt)
    if existing_lcv:
        return {
            "already_exists": 1,
            "existing_lcv": existing_lcv
        }

    pr = frappe.get_doc("Purchase Receipt", purchase_receipt)
    company = pr.company
    settings = get_import_export_settings()

    charges = []

    add_charge(
        charges=charges,
        amount=doc.shipping_cost,
        description="Shipping Cost",
        expense_account=settings.get("default_shipping_account")
    )

    add_charge(
        charges=charges,
        amount=doc.customs_duty,
        description="Customs Duty",
        expense_account=settings.get("default_customs_duty_account")
    )

    add_charge(
        charges=charges,
        amount=doc.inland_transport,
        description="Inland Transport",
        expense_account=settings.get("default_inland_transport_account")
    )

    add_charge(
        charges=charges,
        amount=doc.other_charges,
        description="Other Charges",
        expense_account=settings.get("default_other_charges_account")
    )

    capitalize_vat = cint(settings.get("capitalize_import_vat_in_inventory"))

    if capitalize_vat:
        add_charge(
            charges=charges,
            amount=doc.vat_amount,
            description="VAT Amount",
            expense_account=settings.get("default_import_vat_account")
        )

    if not charges:
        frappe.throw(_("No landed cost charges found to create Landed Cost Voucher."))

    lcv_data = {
        "doctype": "Landed Cost Voucher",
        "company": company,
        "receipt_document_type": "Purchase Receipt",
        "taxes": charges,
        "purchase_receipts": []
    }

    if frappe.db.has_column("Landed Cost Voucher", "custom_import_shipment"):
        lcv_data["custom_import_shipment"] = doc.name

    lcv = frappe.get_doc(lcv_data)

    append_lcv_purchase_receipt_row(lcv, pr)

    if hasattr(lcv, "get_items_from_purchase_receipts"):
        lcv.get_items_from_purchase_receipts()

    if hasattr(lcv, "set_total_taxes_and_charges"):
        lcv.set_total_taxes_and_charges()

    if hasattr(lcv, "calculate_taxes_and_totals"):
        lcv.calculate_taxes_and_totals()

    lcv.insert()

    updates = {}
    if frappe.db.has_column("Import Shipment", "landed_cost_voucher"):
        updates["landed_cost_voucher"] = lcv.name

    if updates:
        doc.db_set(updates)

    return {
        "landed_cost_voucher": lcv.name,
        "capitalize_vat_in_inventory": capitalize_vat,
        "purchase_receipt": purchase_receipt
    }


def get_existing_lcv_for_purchase_receipt(purchase_receipt):
    parents = frappe.get_all(
        "Landed Cost Purchase Receipt",
        filters={"receipt_document": purchase_receipt},
        pluck="parent"
    )

    if not parents:
        return None

    existing = frappe.get_all(
        "Landed Cost Voucher",
        filters={"name": ["in", parents], "docstatus": ["!=", 2]},
        fields=["name"],
        order_by="creation desc",
        limit=1
    )

    return existing[0].name if existing else None


def append_lcv_purchase_receipt_row(lcv, pr):
    child_dt = "Landed Cost Purchase Receipt"
    meta = frappe.get_meta(child_dt)
    fieldnames = {df.fieldname for df in meta.fields}

    row = {
        "receipt_document_type": "Purchase Receipt",
        "receipt_document": pr.name
    }

    if "supplier" in fieldnames:
        row["supplier"] = pr.supplier

    if "supplier_name" in fieldnames:
        row["supplier_name"] = pr.supplier_name or pr.supplier

    if "grand_total" in fieldnames:
        row["grand_total"] = pr.grand_total

    if "base_grand_total" in fieldnames:
        row["base_grand_total"] = pr.base_grand_total

    if "posting_date" in fieldnames:
        row["posting_date"] = pr.posting_date

    lcv.append("purchase_receipts", row)


def get_import_export_settings():
    settings = frappe.get_single("Import Export Settings")

    return {
        "default_import_warehouse": getattr(settings, "default_import_warehouse", None),
        "default_export_warehouse": getattr(settings, "default_export_warehouse", None),
        "default_shipping_account": getattr(settings, "default_shipping_account", None),
        "default_customs_duty_account": getattr(settings, "default_customs_duty_account", None),
        "default_inland_transport_account": getattr(settings, "default_inland_transport_account", None),
        "default_other_charges_account": getattr(settings, "default_other_charges_account", None),
        "default_import_vat_account": getattr(settings, "default_import_vat_account", None),
        "capitalize_import_vat_in_inventory": getattr(settings, "capitalize_import_vat_in_inventory", 0),
        "default_port_of_loading": getattr(settings, "default_port_of_loading", None),
        "default_port_of_arrival": getattr(settings, "default_port_of_arrival", None),
        "default_freight_forwarder": getattr(settings, "default_freight_forwarder", None),
        "default_customs_broker": getattr(settings, "default_customs_broker", None),
        "default_shipping_method": getattr(settings, "default_shipping_method", None),
    }


def add_charge(charges, amount, description, expense_account):
    amount = flt(amount)
    if amount <= 0:
        return

    if not expense_account:
        frappe.throw(_("Please set default account for {0} in Import Export Settings.").format(description))

    charges.append({
        "expense_account": expense_account,
        "description": description,
        "amount": amount
    })


def flt(value):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def cint(value):
    try:
        return int(value or 0)
    except Exception:
        return 0
