import datetime
import pytz
from odoo import models, fields, api

class PosPaymentCollectionReportXlsx(models.AbstractModel):
    _name = 'report.pos_payment_collection_report.report_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'POS Payment Collection Excel Report'

    def generate_xlsx_report(self, workbook, data, objects):
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'left',
            'valign': 'vcenter',
        })

        meta_label_format = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'left',
            'valign': 'vcenter',
        })

        meta_value_format = workbook.add_format({
            'font_size': 10,
            'align': 'left',
            'valign': 'vcenter',
        })

        header_format = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#D9E1F2',
            'text_wrap': True
        })

        data_left_format = workbook.add_format({
            'font_size': 10,
            'align': 'left',
            'valign': 'vcenter',
            'border': 1
        })

        data_center_format = workbook.add_format({
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })

        amount_format = workbook.add_format({
            'font_size': 10,
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '#,##0.00'
        })

        total_label_format = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#F2F2F2'
        })

        total_amount_format = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#F2F2F2',
            'num_format': '#,##0.00'
        })

        worksheet = workbook.add_worksheet('Payment Collection Report')
        
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 25)  
        worksheet.set_column('C:C', 15)  
        worksheet.set_column('D:D', 20)  
        worksheet.set_column('E:E', 18)  
        worksheet.set_column('F:F', 18)  
        worksheet.set_column('G:G', 18)  
        worksheet.set_column('H:H', 18)  

        wizard = objects[0]
        date_start = wizard.date_start
        date_stop = wizard.date_stop
        all_reps = wizard.all_reps
        sales_rep = wizard.sales_rep_id

        worksheet.write('A2', 'Payment Collection Report', title_format)
        worksheet.write('A4', 'Select Date :', meta_label_format)
        worksheet.write('B4', date_start.strftime('%Y-%m-%d') if date_start else '', meta_value_format)
        worksheet.write('C4', date_stop.strftime('%Y-%m-%d') if date_stop else '', meta_value_format)

        worksheet.write('A5', 'Rep Name :', meta_label_format)
        worksheet.write('B5', sales_rep.name if (sales_rep and not all_reps) else 'All', meta_value_format)
        worksheet.write('C5', 'All Rep :', meta_label_format)
        worksheet.write('D5', 'Yes' if all_reps else 'No', meta_value_format)

        headers = [
            'Rep Name', 'Customer Name', 'Invoice Date', 'Invoice Name',
            'Invoice Amount', 'Cash Collection', 'Cheque Collection', 'Due Amount'
        ]
        
        row = 6
        for col_idx, header in enumerate(headers):
            worksheet.write(row, col_idx, header, header_format)
        worksheet.set_row(row, 25)
        row += 1

        user_tz = self.env.user.tz or 'UTC'
        local_tz = pytz.timezone(user_tz)

        start_local = local_tz.localize(datetime.datetime.combine(date_start, datetime.time.min))
        start_utc = start_local.astimezone(pytz.utc).replace(tzinfo=None)

        end_local = local_tz.localize(datetime.datetime.combine(date_stop, datetime.time.max))
        end_utc = end_local.astimezone(pytz.utc).replace(tzinfo=None)

        pos_domain = [
            ('date_order', '>=', start_utc),
            ('date_order', '<=', end_utc),
            ('state', 'in', ['paid', 'done', 'invoiced']),
        ]
        if not all_reps and sales_rep:
            pos_domain.append(('config_id', '=', sales_rep.id))

        orders = self.env['pos.order'].search(pos_domain, order='date_order asc')

        payment_domain = [
            ('date', '>=', date_start),
            ('date', '<=', date_stop),
            ('payment_type', '=', 'inbound'),
            ('partner_type', '=', 'customer'),
            ('state', 'in', ['posted', 'in_process', 'paid']),
        ]

        if not all_reps and sales_rep:
            rep_name = sales_rep.name
            matching_users = self.env['res.users'].search([('name', '=', rep_name)])
            payment_domain.append(('create_uid', 'in', matching_users.ids))
        else:
            configs = self.env['pos.config'].search([])
            config_names = configs.mapped('name')
            matching_users = self.env['res.users'].search([('name', 'in', config_names)])
            payment_domain.append(('create_uid', 'in', matching_users.ids))

        payments = self.env['account.payment'].search(payment_domain, order='date asc')

        report_rows = []

        for order in orders:
            cash_amount = 0.0
            cheque_amount = 0.0
            for pay in order.payment_ids:
                pay_method = pay.payment_method_id
                pay_name = pay_method.name or ''
                
                is_credit = False
                if pay_method.journal_id:
                    name_lower = pay_name.lower()
                    if 'credit' in name_lower and 'card' not in name_lower:
                        is_credit = True
                    elif 'receivable' in name_lower:
                        is_credit = True
                else:
                    is_credit = True

                if is_credit:
                    continue 

                if pay_method.journal_id.type == 'cash':
                    cash_amount += pay.amount
                else:
                    cheque_amount += pay.amount

            if order.account_move:
                due_amount = order.account_move.amount_residual
            else:
                due_amount = order.amount_total - cash_amount - cheque_amount

            local_date = fields.Datetime.context_timestamp(self, order.date_order).date()
            inv_date = order.account_move.invoice_date if order.account_move else local_date

            report_rows.append({
                'rep_name': order.config_id.name or '',
                'customer_name': order.partner_id.name or '',
                'invoice_date': inv_date,
                'invoice_name': order.account_move.name or order.name or '',
                'invoice_amount': order.amount_total,
                'cash_collection': cash_amount,
                'cheque_collection': cheque_amount,
                'due_amount': due_amount,
            })

        for payment in payments:
            cash_col = payment.amount if payment.journal_id.type == 'cash' else 0.0
            cheque_col = payment.amount if payment.journal_id.type != 'cash' else 0.0

            report_rows.append({
                'rep_name': payment.create_uid.name or '',
                'customer_name': payment.partner_id.name or '',
                'invoice_date': payment.date,
                'invoice_name': payment.name or '',
                'invoice_amount': payment.amount,
                'cash_collection': cash_col,
                'cheque_collection': cheque_col,
                'due_amount': 0.0,
            })
        report_rows.sort(key=lambda r: (r['invoice_date'] or datetime.date.min, r['invoice_name'] or ''))

        total_inv_amount = 0.0
        total_cash_col = 0.0
        total_cheque_col = 0.0
        total_due_amount = 0.0

        for r_data in report_rows:
            worksheet.write(row, 0, r_data['rep_name'], data_left_format)
            worksheet.write(row, 1, r_data['customer_name'], data_left_format)
            
            f_date = r_data['invoice_date']
            if isinstance(f_date, (datetime.date, datetime.datetime)):
                f_date = f_date.strftime('%Y-%m-%d')
            worksheet.write(row, 2, f_date or '', data_center_format)
            
            worksheet.write(row, 3, r_data['invoice_name'], data_center_format)
            worksheet.write(row, 4, r_data['invoice_amount'], amount_format)
            worksheet.write(row, 5, r_data['cash_collection'], amount_format)
            worksheet.write(row, 6, r_data['cheque_collection'], amount_format)
            worksheet.write(row, 7, r_data['due_amount'], amount_format)

            total_inv_amount += r_data['invoice_amount']
            total_cash_col += r_data['cash_collection']
            total_cheque_col += r_data['cheque_collection']
            total_due_amount += r_data['due_amount']
            
            worksheet.set_row(row, 20)
            row += 1

        worksheet.merge_range(row, 0, row, 3, 'Total', total_label_format)
        worksheet.write(row, 4, total_inv_amount, total_amount_format)
        worksheet.write(row, 5, total_cash_col, total_amount_format)
        worksheet.write(row, 6, total_cheque_col, total_amount_format)
        worksheet.write(row, 7, total_due_amount, total_amount_format)
        worksheet.set_row(row, 22)
