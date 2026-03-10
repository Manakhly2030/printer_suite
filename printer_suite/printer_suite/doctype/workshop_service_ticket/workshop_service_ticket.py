# Copyright (c) 2026, Manakhly and contributors
# For license information, please see license.txt

# import frappe

import frappe
from frappe.model.document import Document

class WorkshopServiceTicket(Document):
    def validate(self):
        if self.serial_no and not frappe.db.exists("Serial No", self.serial_no):
            frappe.throw(f"Serial No {self.serial_no} does not exist.")

        if (self.final_cost or 0) < 0:
            frappe.throw("Final Cost cannot be negative.")
