from odoo import http, fields
from odoo.http import request


class HalMobileApi(http.Controller):

    # =========================================================
    # PING
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
    # =========================================================

    @http.route(
        '/hal/api/login',
        type='json',
        auth='public',
        methods=['POST'],
        csrf=False,
    )
    def login(self, login=None, password=None, **kwargs):

        if not login or not password:
            return {
                'success': False,
                'message': 'Username and password are required.',
            }

        try:
            login_value = login.strip()

            employee = request.env['hr.employee'].sudo().search(
                [
                    ('work_email', '=ilike', login_value),
                ],
                limit=1,
            )

            if not employee:
                return {
                    'success': False,
                    'message': 'Wrong username or password.',
                }

            employee_pin = employee.pin or ''

            if str(employee_pin) != str(password):
                return {
                    'success': False,
                    'message': 'Wrong username or password.',
                }

            employee_image = ''

            if employee.image_128:
                employee_image = employee.image_128.decode('utf-8')

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

    # =========================================================
    # ATTENDANCE STATUS
    # =========================================================

    @http.route(
        '/hal/api/attendance/status',
        type='json',
        auth='public',
        methods=['POST'],
        csrf=False,
    )
    def attendance_status(self, employee_id=None, **kwargs):

        if not employee_id:
            return {
                'success': False,
                'message': 'Employee ID is required.',
            }

        try:
            employee = request.env['hr.employee'].sudo().browse(
                int(employee_id)
            )

            if not employee.exists():
                return {
                    'success': False,
                    'message': 'Employee not found.',
                }

            attendance = request.env['hr.attendance'].sudo().search(
                [
                    ('employee_id', '=', employee.id),
                    ('check_out', '=', False),
                ],
                order='check_in desc',
                limit=1,
            )

            if attendance:
                return {
                    'success': True,
                    'checked_in': True,
                    'attendance_id': attendance.id,
                    'check_in': (
                        attendance.check_in.isoformat()
                        if attendance.check_in
                        else False
                    ),
                    'check_out': False,
                }

            last_attendance = request.env['hr.attendance'].sudo().search(
                [
                    ('employee_id', '=', employee.id),
                ],
                order='check_in desc',
                limit=1,
            )

            return {
                'success': True,
                'checked_in': False,
                'attendance_id': (
                    last_attendance.id
                    if last_attendance
                    else False
                ),
                'check_in': (
                    last_attendance.check_in.isoformat()
                    if last_attendance and last_attendance.check_in
                    else False
                ),
                'check_out': (
                    last_attendance.check_out.isoformat()
                    if last_attendance and last_attendance.check_out
                    else False
                ),
            }

        except Exception as e:
            return {
                'success': False,
                'message': 'Attendance status error: %s' % str(e),
            }

    # =========================================================
    # CHECK IN
    # =========================================================

    @http.route(
        '/hal/api/attendance/checkin',
        type='json',
        auth='public',
        methods=['POST'],
        csrf=False,
    )
    def attendance_checkin(self, employee_id=None, **kwargs):

        if not employee_id:
            return {
                'success': False,
                'message': 'Employee ID is required.',
            }

        try:
            employee = request.env['hr.employee'].sudo().browse(
                int(employee_id)
            )

            if not employee.exists():
                return {
                    'success': False,
                    'message': 'Employee not found.',
                }

            existing_attendance = (
                request.env['hr.attendance']
                .sudo()
                .search(
                    [
                        ('employee_id', '=', employee.id),
                        ('check_out', '=', False),
                    ],
                    limit=1,
                )
            )

            if existing_attendance:
                return {
                    'success': False,
                    'message': 'Employee is already checked in.',
                }

            attendance = request.env['hr.attendance'].sudo().create({
                'employee_id': employee.id,
                'check_in': fields.Datetime.now(),
            })

            return {
                'success': True,
                'message': 'Check in successful.',
                'attendance_id': attendance.id,
                'employee_id': employee.id,
                'employee_name': employee.name or '',
                'check_in': (
                    attendance.check_in.isoformat()
                    if attendance.check_in
                    else False
                ),
            }

        except Exception as e:
            return {
                'success': False,
                'message': 'Check in error: %s' % str(e),
            }

    # =========================================================
    # CHECK OUT
    # =========================================================

    @http.route(
        '/hal/api/attendance/checkout',
        type='json',
        auth='public',
        methods=['POST'],
        csrf=False,
    )
    def attendance_checkout(self, employee_id=None, **kwargs):

        if not employee_id:
            return {
                'success': False,
                'message': 'Employee ID is required.',
            }

        try:
            employee = request.env['hr.employee'].sudo().browse(
                int(employee_id)
            )

            if not employee.exists():
                return {
                    'success': False,
                    'message': 'Employee not found.',
                }

            attendance = request.env['hr.attendance'].sudo().search(
                [
                    ('employee_id', '=', employee.id),
                    ('check_out', '=', False),
                ],
                order='check_in desc',
                limit=1,
            )

            if not attendance:
                return {
                    'success': False,
                    'message': 'No active check in was found.',
                }

            attendance.sudo().write({
                'check_out': fields.Datetime.now(),
            })

            return {
                'success': True,
                'message': 'Check out successful.',
                'attendance_id': attendance.id,
                'employee_id': employee.id,
                'employee_name': employee.name or '',
                'check_in': (
                    attendance.check_in.isoformat()
                    if attendance.check_in
                    else False
                ),
                'check_out': (
                    attendance.check_out.isoformat()
                    if attendance.check_out
                    else False
                ),
            }

        except Exception as e:
            return {
                'success': False,
                'message': 'Check out error: %s' % str(e),
            }
