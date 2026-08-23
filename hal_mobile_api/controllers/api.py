from odoo import http
from odoo.http import request


class HalMobileApi(http.Controller):

    # =========================================================
    # PING
    # Test connectivity between Flutter and Odoo
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
    #
    # Current authentication:
    # Username -> hr.employee.work_email
    # Password -> hr.employee.pin
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
            # Find employee by Work Email
            # -------------------------------------------------

            employee = request.env['hr.employee'].sudo().search(
                [
                    ('work_email', '=ilike', login_value),
                ],
                limit=1,
            )

            # -------------------------------------------------
            # Employee not found
            # -------------------------------------------------

            if not employee:
                return {
                    'success': False,
                    'message': 'Wrong username or password.',
                }

            # -------------------------------------------------
            # Get employee PIN
            # -------------------------------------------------

            employee_pin = employee.pin or ''

            # -------------------------------------------------
            # Compare entered password with employee PIN
            # -------------------------------------------------

            if str(employee_pin) != str(password):
                return {
                    'success': False,
                    'message': 'Wrong username or password.',
                }

            # -------------------------------------------------
            # Get employee image
            #
            # image_128 is used because the mobile application
            # only needs a small profile/avatar image.
            # -------------------------------------------------

            employee_image = ''

            if employee.image_128:
                employee_image = employee.image_128.decode('utf-8')

            # -------------------------------------------------
            # Successful login
            # -------------------------------------------------

            return {
                'success': True,
                'message': 'Login successful.',
                'employee_id': employee.id,
                'employee_name': employee.name or '',
                'employee_image': employee_image,
            }

        except Exception as e:
            return {
                'success': False,
                'message': 'Login error: %s' % str(e),
            }
