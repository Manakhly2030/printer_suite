app_name = "printer_suite"
app_title = "Printer Suite"
app_publisher = "Manakhly"
app_description = "Printer Suite Application for Printing Company "
app_email = "manakhly@erp-developers.com"
app_license = "mit"

# Apps
# ------------------
# Includes in <head>
app_include_css = []
app_include_js = []

# Fixtures to move custom fields / property setters with the app


fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            ["module", "=", "Printer Suite"]
        ]
    },
{
        "dt": "Workspace",
        "filters": [["module", "=", "Printer Suite"]]
    },

    {
        "dt": "Property Setter",
        "filters": [
            ["module", "=", "Printer Suite"]
        ]
    },
    {
        "dt": "Client Script",
        "filters": [
            ["module", "=", "Printer Suite"]
        ]
    },
    "Custom DocPerm"
]
# Attach custom JS to standard doctypes
doctype_js = {
    "Item": "public/js/item.js",
    "Serial No": "public/js/serial_no.js",
    "Purchase Receipt": "public/js/purchase_receipt.js"
}

# Doc Events
doc_events = {
    "Purchase Receipt": {
        "on_submit": "printer_suite.events.purchase_receipt.on_submit"
    },
    "Stock Entry": {
        "on_submit": "printer_suite.events.stock_entry.on_submit"
    }
}

# Optional scheduler placeholder
scheduler_events = {
    "daily": [
        # "printer_suite.api.daily_tasks"
    ]
}
# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "printer_suite",
# 		"logo": "/assets/printer_suite/logo.png",
# 		"title": "Printer Suite",
# 		"route": "/printer_suite",
# 		"has_permission": "printer_suite.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/printer_suite/css/printer_suite.css"
# app_include_js = "/assets/printer_suite/js/printer_suite.js"

# include js, css files in header of web template
# web_include_css = "/assets/printer_suite/css/printer_suite.css"
# web_include_js = "/assets/printer_suite/js/printer_suite.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "printer_suite/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "printer_suite/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "printer_suite.utils.jinja_methods",
# 	"filters": "printer_suite.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "printer_suite.install.before_install"
# after_install = "printer_suite.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "printer_suite.uninstall.before_uninstall"
# after_uninstall = "printer_suite.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "printer_suite.utils.before_app_install"
# after_app_install = "printer_suite.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "printer_suite.utils.before_app_uninstall"
# after_app_uninstall = "printer_suite.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "printer_suite.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"printer_suite.tasks.all"
# 	],
# 	"daily": [
# 		"printer_suite.tasks.daily"
# 	],
# 	"hourly": [
# 		"printer_suite.tasks.hourly"
# 	],
# 	"weekly": [
# 		"printer_suite.tasks.weekly"
# 	],
# 	"monthly": [
# 		"printer_suite.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "printer_suite.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "printer_suite.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "printer_suite.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["printer_suite.utils.before_request"]
# after_request = ["printer_suite.utils.after_request"]

# Job Events
# ----------
# before_job = ["printer_suite.utils.before_job"]
# after_job = ["printer_suite.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"printer_suite.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

