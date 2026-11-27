"""De verlofaanvraag van Frappe HR, met verlof in uren.

Voor een verlofsoort in uren (`in_uren`) slaat deze klasse de controles en het grootboek in dagen van Frappe over: het
saldo staat in de verlofboekingen en wordt getoetst in `personeel.aanvraag_controleren`. Andere verlofsoorten (ziekte,
onbetaald verlof) werken zoals Frappe ze heeft.
"""

from hrms.hr.doctype.leave_application.leave_application import LeaveApplication, get_number_of_leave_days

from openaec_bouw.personeel import in_uren


class Verlofaanvraag(LeaveApplication):
	def _in_uren(self) -> bool:
		return bool(self.leave_type) and in_uren(self.leave_type)

	def validate_balance_leaves(self):
		if not self._in_uren():
			return super().validate_balance_leaves()
		if self.from_date and self.to_date:
			self.total_leave_days = get_number_of_leave_days(
				self.employee, self.leave_type, self.from_date, self.to_date, self.half_day, self.half_day_date
			)

	def validate_dates_across_allocation(self):
		if not self._in_uren():
			return super().validate_dates_across_allocation()

	def validate_back_dated_application(self):
		if not self._in_uren():
			return super().validate_back_dated_application()

	def create_leave_ledger_entry(self, submit=True):
		if not self._in_uren():
			return super().create_leave_ledger_entry(submit)
