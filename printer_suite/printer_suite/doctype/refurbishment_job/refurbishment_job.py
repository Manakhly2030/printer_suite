import frappe
from frappe.model.document import Document
from frappe import _


class RefurbishmentJob(Document):

    def validate(self):
        if not self.intake_date:
            self.intake_date = frappe.utils.nowdate()

        if self.status == "Completed" and self.qc_result != "Passed":
            frappe.throw(_("You cannot set Status to Completed unless QC Result is Passed."))

        self.calculate_totals()

    def calculate_totals(self):
        parts_cost = 0

        for row in self.get("spare_parts") or []:
            row.amount = (row.qty or 0) * (row.rate or 0)
            parts_cost += row.amount or 0

        self.parts_cost = parts_cost
        self.total_refurbishment_cost = (
            (self.parts_cost or 0)
            + (self.labor_cost or 0)
            + (self.other_cost or 0)
        )


def get_item_cost(item_code, source_warehouse=None):
    valuation_rate = 0

    if source_warehouse:
        valuation_rate = frappe.db.get_value(
            "Bin",
            {"item_code": item_code, "warehouse": source_warehouse},
            "valuation_rate"
        ) or 0

    if valuation_rate:
        return valuation_rate, "Valuation Rate"

    last_pr_rate = frappe.db.sql("""
        select pri.rate
        from `tabPurchase Receipt Item` pri
        inner join `tabPurchase Receipt` pr on pr.name = pri.parent
        where pri.item_code = %s
          and pr.docstatus = 1
        order by pr.posting_date desc, pr.posting_time desc
        limit 1
    """, (item_code,), as_dict=True)

    if last_pr_rate and last_pr_rate[0].get("rate"):
        return last_pr_rate[0]["rate"], "Last Purchase Receipt"

    last_pi_rate = frappe.db.sql("""
        select pii.rate
        from `tabPurchase Invoice Item` pii
        inner join `tabPurchase Invoice` pi on pi.name = pii.parent
        where pii.item_code = %s
          and pi.docstatus = 1
        order by pi.posting_date desc, pi.posting_time desc
        limit 1
    """, (item_code,), as_dict=True)

    if last_pi_rate and last_pi_rate[0].get("rate"):
        return last_pi_rate[0]["rate"], "Last Purchase Invoice"

    item_price = frappe.db.get_value(
        "Item Price",
        {"item_code": item_code, "selling": 0},
        "price_list_rate"
    )

    if item_price:
        return item_price, "Item Price"

    return 0, "No Price"


@frappe.whitelist()
def get_spare_part_options(printer_item, source_warehouse=None):
    if not printer_item:
        return []

    compatibility_name = frappe.db.get_value(
        "Printer Compatibility",
        {"printer_item": printer_item},
        "name"
    )

    if not compatibility_name:
        return []

    rows = frappe.get_all(
        "Printer Compatibility Item",
        filters={"parent": compatibility_name},
        fields=["spare_part_type", "compatible_item"]
    )

    result = []

    for row in rows:
        item = frappe.db.get_value(
            "Item",
            row.compatible_item,
            [
                "item_name",
                "stock_uom",
                "custom_is_spare_part",
                "custom_spare_part_type"
            ],
            as_dict=True
        )

        if not item:
            continue

        if not item.custom_is_spare_part:
            continue

        rate, source = get_item_cost(row.compatible_item, source_warehouse)

        result.append({
            "spare_part_type": row.spare_part_type or item.custom_spare_part_type or "",
            "item_code": row.compatible_item,
            "description": item.item_name,
            "uom": item.stock_uom or "Nos",
            "rate": rate,
            "price_source": source
        })

    return result


@frappe.whitelist()
def create_material_issue_entry(docname):
    doc = frappe.get_doc("Refurbishment Job", docname)

    if doc.material_issue_entry:
        return doc.material_issue_entry

    if not doc.printer_item:
        frappe.throw(_("Printer Item is required."))

    if not doc.serial_no:
        frappe.throw(_("Serial No is required."))

    if not doc.source_warehouse:
        frappe.throw(_("Source Warehouse is required."))

    if not doc.get("spare_parts"):
        frappe.throw(_("Please add spare parts first."))

    items = []

    for row in doc.spare_parts:
        if not row.item_code or not row.qty:
            continue

        source_warehouse = row.source_warehouse or doc.source_warehouse
        if not source_warehouse:
            frappe.throw(_("Source Warehouse is required for spare part row #{0}.").format(row.idx))

        items.append({
            "item_code": row.item_code,
            "qty": row.qty,
            "uom": row.uom or "Nos",
            "s_warehouse": source_warehouse,
            "allow_zero_valuation_rate": 0
        })

    if not items:
        frappe.throw(_("No valid spare parts found to issue."))

    stock_entry = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Issue",
        "custom_refurbishment_job": doc.name,
        "items": items
    })
    stock_entry.insert()
    stock_entry.submit()

    job_updates = {
        "material_issue_entry": stock_entry.name,
        "status": "Under Refurbishment"
    }

    if not doc.inspection_date:
        job_updates["inspection_date"] = frappe.utils.nowdate()

    doc.db_set(job_updates)

    if doc.serial_no and frappe.db.exists("Serial No", doc.serial_no):
        serial_updates = {}

        if frappe.db.has_column("Serial No", "custom_refurbishment_status"):
            serial_updates["custom_refurbishment_status"] = "Under Refurbishment"

        if frappe.db.has_column("Serial No", "custom_unit_condition"):
            current_condition = frappe.db.get_value("Serial No", doc.serial_no, "custom_unit_condition")
            if not current_condition:
                serial_updates["custom_unit_condition"] = "For Refurbishment"

        if serial_updates:
            frappe.db.set_value("Serial No", doc.serial_no, serial_updates)

    return stock_entry.name


@frappe.whitelist()
def create_transfer_entry(docname):
    doc = frappe.get_doc("Refurbishment Job", docname)

    if doc.transfer_entry:
        return doc.transfer_entry

    if not doc.printer_item:
        frappe.throw(_("Printer Item is required."))

    if not doc.serial_no:
        frappe.throw(_("Serial No is required."))

    if not doc.target_warehouse:
        frappe.throw(_("Target Warehouse is required."))

    if doc.qc_result != "Passed":
        frappe.throw(_("QC Result must be Passed before transfer to ready warehouse."))

    serial_data = frappe.db.get_value(
        "Serial No",
        doc.serial_no,
        ["warehouse", "status"],
        as_dict=True
    )

    if not serial_data:
        frappe.throw(_("Serial No {0} not found.").format(doc.serial_no))

    serial_warehouse = serial_data.warehouse or doc.source_warehouse
    serial_status = serial_data.status

    if serial_status in ["Delivered", "Inactive"]:
        frappe.throw(
            _("Serial No {0} cannot be transferred because its status is {1}.").format(
                doc.serial_no, serial_status
            )
        )

    if not serial_warehouse:
        frappe.throw(
            _("Serial No {0} does not have a warehouse assigned and Source Warehouse is also empty.").format(doc.serial_no)
        )

    item_row = {
        "item_code": doc.printer_item,
        "qty": 1,
        "s_warehouse": serial_warehouse,
        "t_warehouse": doc.target_warehouse,
        "serial_no": doc.serial_no
    }

    stock_entry = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Transfer",
        "custom_refurbishment_job": doc.name,
        "items": [item_row]
    })
    stock_entry.insert()
    stock_entry.submit()

    job_updates = {
        "transfer_entry": stock_entry.name,
        "status": "Completed",
        "completion_date": frappe.utils.nowdate()
    }

    if frappe.db.has_column("Refurbishment Job", "target_condition"):
        job_updates["target_condition"] = "Refurbished"

    if frappe.db.has_column("Refurbishment Job", "ready_for_sale"):
        job_updates["ready_for_sale"] = 1

    doc.db_set(job_updates)

    if doc.serial_no and frappe.db.exists("Serial No", doc.serial_no):
        serial_updates = {}

        if frappe.db.has_column("Serial No", "custom_refurbishment_status"):
            serial_updates["custom_refurbishment_status"] = "Ready for Sale"

        if frappe.db.has_column("Serial No", "custom_unit_condition"):
            serial_updates["custom_unit_condition"] = "Refurbished"

        if frappe.db.has_column("Serial No", "custom_last_refurbishment_date"):
            serial_updates["custom_last_refurbishment_date"] = frappe.utils.nowdate()

        if serial_updates:
            frappe.db.set_value("Serial No", doc.serial_no, serial_updates)

    return stock_entry.name
