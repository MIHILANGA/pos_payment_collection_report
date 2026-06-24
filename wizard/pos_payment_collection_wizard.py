from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PosPaymentCollectionWizard(models.TransientModel):
    _name = 'pos.payment.collection.wizard'
    _description = 'POS Payment Collection Report Wizard'

    date_start = fields.Date(
        string='Start Date',
        required=True,
        default=fields.Date.context_today
    )
    date_stop = fields.Date(
        string='End Date',
        required=True,
        default=fields.Date.context_today
    )
    all_reps = fields.Boolean(
        string='All Reps',
        default=False
    )
    sales_rep_id = fields.Many2one(
        'pos.config',
        string='Rep / Session Config'
    )

    @api.constrains('date_start', 'date_stop')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_stop and rec.date_start > rec.date_stop:
                raise ValidationError(_("Start Date cannot be later than End Date."))

    @api.constrains('all_reps', 'sales_rep_id')
    def _check_rep(self):
        for rec in self:
            if not rec.all_reps and not rec.sales_rep_id:
                raise ValidationError(_("Please select a Rep / Session Config or check 'All Reps'."))

    def action_generate_excel_report(self):
        self.ensure_one()
        data = {
            'date_start': self.date_start,
            'date_stop': self.date_stop,
            'all_reps': self.all_reps,
            'sales_rep_id': self.sales_rep_id.id if self.sales_rep_id else False,
            'sales_rep_name': self.sales_rep_id.name if self.sales_rep_id else '',
        }
        return self.env.ref('pos_payment_collection_report.action_pos_payment_collection_report_xlsx').report_action(self, data=data)
