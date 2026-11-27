// Bedrijfskalender: opnieuw vullen uit de cao (zolang hij concept is) en vaststellen als feestdagenlijst.
frappe.ui.form.on("Bedrijfskalender", {
	refresh(frm) {
		if (frm.is_new() || frm.doc.status === "Vastgesteld") return;
		frm.add_custom_button(__("Opnieuw uit de cao"), () =>
			frappe.call({ method: "openaec_bouw.openaec_bouw.doctype.bedrijfskalender.bedrijfskalender.vernieuwen", args: { naam: frm.doc.name }, freeze: true }).then(() => frm.reload_doc()),
		);
		frm.add_custom_button(__("Vaststellen"), () =>
			frappe.confirm(__("De kalender wordt de feestdagenlijst van de medewerkers met deze cao. Doorgaan?"), () =>
				frappe.call({ method: "openaec_bouw.openaec_bouw.doctype.bedrijfskalender.bedrijfskalender.vaststellen", args: { naam: frm.doc.name }, freeze: true }).then(() => frm.reload_doc()),
			),
		).addClass("btn-primary");
	},
});
