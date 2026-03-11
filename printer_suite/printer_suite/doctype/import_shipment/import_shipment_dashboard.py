from frappe import _

def get_data():
    return {
        "fieldname": "custom_import_shipment",
        "non_standard_fieldnames": {
            "Purchase Receipt": "custom_import_shipment",
            "Landed Cost Voucher": "custom_import_shipment",
        },
        "transactions": [
            {
                "label": _("Procurement"),
                "items": ["Purchase Receipt", "Landed Cost Voucher"],
            }
        ],
    }
