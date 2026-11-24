// Standaard het vorige kwartaal: dat is het tijdvak waarover de aangifte nu gedaan wordt.
const icp_kwartaal = Math.floor(new Date().getMonth() / 3);
const icp_van = new Date(new Date().getFullYear(), icp_kwartaal * 3 - 3, 1);
const icp_tot = new Date(new Date().getFullYear(), icp_kwartaal * 3, 0);

frappe.query_reports["Opgaaf ICP"] = {
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
			default: frappe.datetime.obj_to_str(icp_van),
			reqd: 1,
		},
		{
			fieldname: "tot",
			label: __("Tot en met"),
			fieldtype: "Date",
			default: frappe.datetime.obj_to_str(icp_tot),
			reqd: 1,
		},
	],
};
