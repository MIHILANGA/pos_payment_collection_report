{
    'name': 'POS Payment Collection Excel Report',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Excel report for POS Payment Collections',
    'author': 'Custom',
    'depends': ['point_of_sale', 'account', 'report_xlsx'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/pos_payment_collection_wizard_view.xml',
        'reports/pos_payment_collection_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
