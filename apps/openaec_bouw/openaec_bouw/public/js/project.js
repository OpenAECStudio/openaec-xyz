// Op het project: het klantenportaal. Zien wat de klant ziet, een verborgen link om te bekijken, en klanten toegang geven.
frappe.ui.form.on("Project", {
	refresh(frm) {
		if (frm.is_new()) return;
		const groep = __("Klantenportaal");
		frm.add_custom_button(__("Zien als de klant"), () => window.open(`/portaal/p/${encodeURIComponent(frm.doc.name)}`), groep);
		frm.add_custom_button(
			__("Verborgen link maken"),
			() => {
				frappe.prompt(
					[
						{ fieldname: "omschrijving", label: __("Voor wie"), fieldtype: "Data" },
						{ fieldname: "dagen", label: __("Geldig (dagen)"), fieldtype: "Int", default: 90 },
					],
					(waarden) =>
						frappe
							.call({ method: "openaec_bouw.portaal.link_maken", args: { project: frm.doc.name, ...waarden } })
							.then((r) => {
								const d = new frappe.ui.Dialog({
									title: __("Verborgen link"),
									fields: [
										{
											fieldtype: "HTML",
											options: `<p>${__("Wie deze link heeft, kan het project bekijken (niet reageren) tot {0}. De link is alleen nu te zien; intrekken kan bij Portaallink.", [frappe.datetime.str_to_user(r.message.geldig_tot)])}</p>`,
										},
										{ fieldname: "url", fieldtype: "Data", read_only: 1, default: r.message.url },
									],
									primary_action_label: __("Kopiëren"),
									primary_action: () => frappe.utils.copy_to_clipboard(r.message.url),
								});
								d.show();
							}),
					__("Verborgen link maken"),
					__("Maken"),
				);
			},
			groep,
		);
		frm.add_custom_button(
			__("Klant toegang geven"),
			() => frappe.new_doc("Portaaltoegang", { project: frm.doc.name }),
			groep,
		);
		frm.add_custom_button(
			__("Foto toevoegen"),
			() => frappe.new_doc("Bouwfoto", { project: frm.doc.name, gedeeld: 1 }),
			groep,
		);
	},
});
