// Op de lijst met banktransacties: een bankafschrift (CAMT.053) inlezen en de open regels opnieuw afletteren.
// Bestaande instellingen van de lijst (van ERPNext) blijven staan.
(() => {
	const bestaand = frappe.listview_settings["Bank Transaction"] || {};
	const onload = bestaand.onload;
	const melding = (r) =>
		__("{0} nieuw, {1} stonden er al, {2} afgeletterd, {3} nog open", [r.nieuw, r.dubbel, r.afgeletterd, r.open]);
	bestaand.onload = function (listview) {
		if (onload) onload.call(this, listview);
		listview.page.add_inner_button(__("Bankafschrift inlezen (CAMT.053)"), () => {
			new frappe.ui.FileUploader({
				restrictions: { allowed_file_types: [".xml"] },
				allow_multiple: false,
				make_attachments_public: false,
				on_success(bestand) {
					frappe
						.call({ method: "openaec_bouw.bank.inlezen_bestand", args: { file_url: bestand.file_url }, freeze: true })
						.then((r) => {
							frappe.msgprint({ title: __("Bankafschrift ingelezen"), message: melding(r.message), indicator: "green" });
							listview.refresh();
						});
				},
			});
		});
		listview.page.add_inner_button(__("Open regels afletteren"), () => {
			frappe.call({ method: "openaec_bouw.bank.letter_open_af", freeze: true }).then((r) => {
				frappe.show_alert({
					message: __("{0} van {1} open regels afgeletterd", [r.message.afgeletterd, r.message.bekeken]),
					indicator: "green",
				});
				listview.refresh();
			});
		});
	};
	frappe.listview_settings["Bank Transaction"] = bestaand;
})();
