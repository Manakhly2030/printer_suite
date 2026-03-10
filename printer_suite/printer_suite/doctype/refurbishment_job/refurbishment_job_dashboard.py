from frappe import _

def get_data():
    return {
        "non_standard_fieldnames": {
            "Stock Entry": "custom_refurbishment_job",
            "Sales Invoice": "custom_refurbishment_job"
        },
        "transactions": [
            {
                "label": _("Inventory"),
                "items": ["Stock Entry"]
            },
            {
                "label": _("Sales"),
                "items": ["Sales Invoice"]
            }
        ]
    }
