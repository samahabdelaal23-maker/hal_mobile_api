from odoo import http
from odoo.http import request


class HalMobileApi(http.Controller):

    # =========================================================
    # PING
    # Used to test connectivity between Flutter and Odoo
    # =========================================================

    @http.route(
        '/hal/api/ping',
        type='json',
        auth='public',
        methods=['POST'],
        csrf=False,
    )
    def ping(self, **kwargs):
        return {
            'success': True,
            'message': 'HAL successfully connected to Odoo.',
            'database': request.env.cr.dbname,
            'server': 'Odoo 18',
        }

    # =========================================================
    # LOGIN
    # Mobile employee login
    # =========================================================

    @http.route(
        '/hal/api/login',
        type='json',
        auth='public',
        methods=['POST'],
        csrf=False,
    )
    def login(self, login=None, password=None, **kwargs):

        # -----------------------------------------------------
        # Validate credentials
        # -----------------------------------------------------
        if not login or not password:
            return {
                'success': False,
                'message': 'Username and password are required.',
            }

        try:
            login_value = login.strip()

            # -------------------------------------------------
            # Search employee
            #
            # CURRENT TEST:
            # login     -> employee work email
            # password  -> employee PIN code
            # -------------------------------------------------
            employee = request.env['hr.employee'].sudo().search(
                [
                    ('work_email', '=ilike', login_value),
                ],
                limit=1,
            )

            # -------------------------------------------------
            # Employee does not exist
            # -------------------------------------------------
            if not employee:
                return {
                    'success': False,
                    'message': 'Wrong username or password.',
                }

            # -------------------------------------------------
            # Read employee PIN
            # -------------------------------------------------
            employee_pin = employee.pin or ''

            # -------------------------------------------------
            # Compare password with employee PIN
            # -------------------------------------------------
            if str(employee_pin) != str(password):
                return {
                    'success': False,
                    'message': 'Wrong username or password.',
                }

            # -------------------------------------------------
            # Successful employee login
            # -------------------------------------------------
            return {
                'success': True,
                'message': 'Login successful.',
                'employee_id': employee.id,
                'employee_name': employee.name or '',
            }

        except Exception as e:
            return {
                'success': False,
                'message': 'Login error: %s' % str(e),
            }
