from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied


class HalMobileApi(http.Controller):

    # ---------------------------------------------------------
    # PING
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # LOGIN
    # ---------------------------------------------------------

    @http.route(
        '/hal/api/login',
        type='json',
        auth='none',
        methods=['POST'],
        csrf=False,
    )
    def login(self, login=None, password=None, **kwargs):

        if not login or not password:
            return {
                'success': False,
                'message': 'Username and password are required.',
            }

        db = request.db

        if not db:
            return {
                'success': False,
                'message': 'Database not available.',
            }

        try:

            credential = {
                'login': login,
                'password': password,
                'type': 'password',
            }

            auth_info = request.session.authenticate(
                db,
                credential,
            )

            uid = auth_info.get('uid')

            if not uid:
                return {
                    'success': False,
                    'message': 'Wrong username or password.',
                }

            user = request.env['res.users'].sudo().browse(uid)

            employee = request.env['hr.employee'].sudo().search(
                [('user_id', '=', uid)],
                limit=1
            )

            return {
                'success': True,
                'message': 'Login successful.',
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'login': user.login,
                    'email': user.email or '',
                    'company_id': user.company_id.id,
                    'company_name': user.company_id.name,
                    'employee_id': employee.id if employee else False,
                },
            }

        except AccessDenied:

            return {
                'success': False,
                'message': 'Wrong username or password.',
            }

        except Exception:

            return {
                'success': False,
                'message': 'Unable to login to Odoo.',
            }
