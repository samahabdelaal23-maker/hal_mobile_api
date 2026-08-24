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
- GPS attendance validation
- Google Maps work location configuration
- Leave
- Expenses
- Inventory
    """,

    'author': 'HAL',

    'category': 'Technical',

    'depends': [
        'base',
        'web',
        'hr',
        'hr_attendance',
        'hr_holidays',
        'hr_expense',
        'stock',
    ],

    'data': [
        'views/hr_employee_views.xml',
        'views/hr_work_location_views.xml',
    ],

    'assets': {
        'web.assets_backend': [

            # Google Maps OWL template
            'hal_mobile_api/static/src/xml/google_map_picker.xml',

            # Google Maps field widget
            'hal_mobile_api/static/src/js/google_map_picker.js',

            # Google Maps styling
            'hal_mobile_api/static/src/css/google_map_picker.css',
        ],
    },

    'installable': True,
    'application': False,
    'auto_install': False,

    'license': 'LGPL-3',
}
