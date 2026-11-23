// Standaard het vorige kwartaal: dat is het tijdvak waarover de aangifte nu gedaan wordt.
const btw_kwartaal = Math.floor(new Date().getMonth() / 3);
const btw_van = new Date(new Date().getFullYear(), btw_kwartaal * 3 - 3, 1);
const btw_tot = new Date(new Date().getFullYear(), btw_kwartaal * 3, 0);

frappe.query_reports["Btw-aangifte"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Bedrijf"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "van",
			label: __("Van"),
			fieldtype: "Date",
			default: frappe.datetime.obj_to_str(btw_van),
			reqd: 1,
		},
		{
			fieldname: "tot",
			label: __("Tot en met"),
			fieldtype: "Date",
			default: frappe.datetime.obj_to_str(btw_tot),
			reqd: 1,
		},
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		return data && data.vet ? `<b>${value}</b>` : value;
	},
};
