from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied


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
    # Authenticate mobile application users against Odoo
    # =========================================================

    @http.route(
        '/hal/api/login',
        type='json',
        auth='none',
        methods=['POST'],
        csrf=False,
    )
    def login(self, db=None, login=None, password=None, **kwargs):

        # -----------------------------------------------------
        # Validate database
        # -----------------------------------------------------
        if not db:
            return {
                'success': False,
                'message': 'Database name is required.',
            }

        # -----------------------------------------------------
        # Validate username/password
        # -----------------------------------------------------
        if not login or not password:
            return {
                'success': False,
                'message': 'Username and password are required.',
            }

        try:
            # -------------------------------------------------
            # Prepare Odoo 18 authentication credentials
            # -------------------------------------------------
            credential = {
                'login': login.strip(),
                'password': password,
                'type': 'password',
            }

            # -------------------------------------------------
            # Authenticate against the specified Odoo database
            # -------------------------------------------------
            auth_info = request.session.authenticate(
                db,
                credential,
            )

            uid = auth_info.get('uid') if auth_info else False

            # -------------------------------------------------
            # Invalid credentials
            # -------------------------------------------------
            if not uid:
                return {
                    'success': False,
                    'message': 'Wrong username or password.',
                }

            # -------------------------------------------------
            # Get authenticated Odoo user
            # -------------------------------------------------
            user = request.env['res.users'].sudo().browse(uid)

            if not user.exists():
                return {
                    'success': False,
                    'message': 'User account was not found.',
                }

            # -------------------------------------------------
            # Find linked employee if one exists
            # -------------------------------------------------
            employee = request.env['hr.employee'].sudo().search(
                [
                    ('user_id', '=', uid),
                ],
                limit=1,
            )

            # -------------------------------------------------
            # Successful authentication
            # -------------------------------------------------
            return {
                'success': True,
                'message': 'Login successful.',
                'user': {
                    'id': user.id,
                    'name': user.name or '',
                    'login': user.login or '',
                    'email': user.email or '',
                    'company_id': user.company_id.id,
                    'company_name': user.company_id.name or '',
                    'employee_id': employee.id if employee else False,
                    'employee_name': employee.name if employee else '',
                },
            }

        except AccessDenied:
            return {
                'success': False,
                'message': 'Wrong username or password.',
            }

        except Exception as e:
            return {
                'success': False,
                'message': 'Login error: %s' % str(e),
            }
