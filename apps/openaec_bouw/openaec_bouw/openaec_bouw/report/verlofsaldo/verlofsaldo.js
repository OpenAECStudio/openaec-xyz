// Standaard het lopende kalenderjaar.
frappe.query_reports["Verlofsaldo"] = {
	filters: [
		{ fieldname: "company", label: __("Bedrijf"), fieldtype: "Link", options: "Company", default: frappe.defaults.get_user_default("Company") },
		{ fieldname: "van", label: __("Van"), fieldtype: "Date", default: frappe.datetime.year_start(), reqd: 1 },
		{ fieldname: "tot", label: __("Tot en met"), fieldtype: "Date", default: frappe.datetime.year_end(), reqd: 1 },
		{ fieldname: "medewerker", label: __("Medewerker"), fieldtype: "Link", options: "Employee" },
		{ fieldname: "verlofsoort", label: __("Verlofsoort"), fieldtype: "Link", options: "Leave Type" },
	],
};
