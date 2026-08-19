{
    'name': 'HAL Mobile API',

    'version': '18.0.1.0.0',

    'summary': 'REST/JSON API backend for HAL mobile application',

    'description': """
HAL Mobile API
==============

API backend for the HAL Flutter mobile application.

Provides:
- Mobile authentication
- Employee access
- Attendance
- Leave
- Expenses
- Inventory
    """,

    'author': 'HAL',

    'category': 'Technical',

    'depends': [
        'base',
        'hr',
        'hr_attendance',
        'hr_holidays',
        'hr_expense',
        'stock',
    ],

    'data': [],

    'installable': True,
    'application': False,
    'auto_install': False,

    'license': 'LGPL-3',
}
