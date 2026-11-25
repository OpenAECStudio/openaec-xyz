// Op de lijst met inkoopfacturen: een ontvangen UBL-factuur inlezen en van de gekozen facturen een
// SEPA-betaalbestand maken. Bestaande instellingen van de lijst (van ERPNext) blijven staan.
(() => {
	const bestaand = frappe.listview_settings["Purchase Invoice"] || {};
	const onload = bestaand.onload;

	function opslaan(naam, inhoud) {
		const adres = URL.createObjectURL(new Blob([inhoud], { type: "application/xml" }));
		const link = document.createElement("a");
		link.href = adres;
		link.download = naam;
		document.body.appendChild(link);
		link.click();
		link.remove();
		URL.revokeObjectURL(adres);
	}

	function betaalbestand(listview) {
		const facturen = listview.get_checked_items(true);
		if (!facturen.length) {
			frappe.msgprint(__("Vink eerst de facturen aan die je wilt betalen."));
			return;
		}
		frappe.prompt(
			[
				{
					fieldname: "bankrekening",
					label: __("Betalen vanaf"),
					fieldtype: "Link",
					options: "Bank Account",
					reqd: 1,
					get_query: () => ({ filters: { is_company_account: 1, disabled: 0 } }),
				},
				{ fieldname: "datum", label: __("Betaaldatum"), fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
				{
					fieldname: "opnieuw",
					label: __("Ook facturen die al in een betaalbestand zaten"),
					fieldtype: "Check",
				},
			],
			(waarden) => {
				frappe
					.call({ method: "openaec_bouw.sepa.betaalbestand", args: { facturen, ...waarden }, freeze: true })
					.then((r) => {
						opslaan(r.message.naam, r.message.inhoud);
						frappe.msgprint({
							title: __("Betaalbestand gemaakt"),
							message: __("{0} overboekingen, samen {1}. Bied het bestand aan bij je bank.", [
								r.message.aantal,
								format_currency(r.message.totaal, "EUR"),
							]),
							indicator: "green",
						});
						listview.refresh();
					});
			},
			__("SEPA-betaalbestand"),
			__("Maken"),
		);
	}

	bestaand.onload = function (listview) {
		if (onload) onload.call(this, listview);
		listview.page.add_inner_button(__("UBL-factuur inlezen"), () => {
			new frappe.ui.FileUploader({
				restrictions: { allowed_file_types: [".xml"] },
				allow_multiple: false,
				make_attachments_public: false,
				on_success(bestand) {
					frappe
						.call({ method: "openaec_bouw.ubl.inlezen_bestand", args: { file_url: bestand.file_url }, freeze: true })
						.then((r) => frappe.set_route("Form", "Purchase Invoice", r.message.factuur));
				},
			});
		});
		listview.page.add_action_item(__("SEPA-betaalbestand"), () => betaalbestand(listview));
	};
	frappe.listview_settings["Purchase Invoice"] = bestaand;
})();
