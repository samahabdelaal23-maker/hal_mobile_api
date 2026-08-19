{
    'name': 'HAL Mobile API',

    'version': '18.0.1.0.0',

    'summary': 'REST/JSON API backend for HAL mobile application',

    'description': """
HAL Mobile API
==============

Provides secure API endpoints for the HAL Flutter mobile application.

The module uses existing Odoo models for:
- Users
- Employees
- Attendance
- Leave
- Expenses
- Inventory

No duplicate business tables are created.
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
