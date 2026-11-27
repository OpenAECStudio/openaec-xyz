// Op het bedrijf: naar de bedrijfsinstellingen, de auditfile (XAF) van een boekjaar downloaden, en bij een bedrijf zonder boekingen het
// Nederlandse rekeningschema van OpenAEC Bouw zetten.
frappe.ui.form.on("Company", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Bedrijfsinstellingen"), () => frappe.set_route("Form", "Bedrijfsinstellingen", frm.doc.name));
		frm.add_custom_button(
			__("Auditfile (XAF)"),
			() => {
				frappe.prompt(
					[{ fieldname: "boekjaar", label: __("Boekjaar"), fieldtype: "Link", options: "Fiscal Year", reqd: 1 }],
					(waarden) => {
						const vraag = new URLSearchParams({ bedrijf: frm.doc.name, boekjaar: waarden.boekjaar });
						window.open(`/api/method/openaec_bouw.auditfile.download?${vraag}`);
					},
					__("Auditfile downloaden"),
					__("Downloaden"),
				);
			},
			__("Nederland"),
		);
		if (frappe.user.has_role("System Manager")) {
			frm.add_custom_button(
				__("Nederlands rekeningschema zetten"),
				() => {
					frappe.confirm(
						__("Het rekeningschema en de btw-sjablonen van dit bedrijf worden vervangen. Dat kan alleen zolang er niet geboekt is. Doorgaan?"),
						() =>
							frappe.call({
								method: "openaec_bouw.boekhouding.zet_rekeningschema",
								args: { bedrijf: frm.doc.name },
								freeze: true,
							}).then((r) => {
								frappe.show_alert({ message: __("{0} rekeningen gezet", [r.message.rekeningen]), indicator: "green" });
								frm.reload_doc();
							}),
					);
				},
				__("Nederland"),
			);
		}
	},
});
