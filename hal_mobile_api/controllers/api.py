from datetime import timezone

from odoo import http, fields
from odoo.http import request

from werkzeug.security import check_password_hash


class HalMobileApi(http.Controller):

    # =========================================================
    # DATETIME HELPER
    # =========================================================

    def _datetime_to_utc_iso(self, value):
        """
        Odoo stores Datetime fields in UTC.

        Odoo returns them internally as naive datetime objects,
        so we explicitly mark the value as UTC before sending
        it to Flutter.

        Example:
        2026-08-24 06:34:00
        becomes:
        2026-08-24T06:34:00+00:00
        """

        if not value:
            return False

        return value.replace(
            tzinfo=timezone.utc
        ).isoformat()

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
    #
    # Mobile App Login:
    #
    # Username:
    # hr.employee.work_email
    #
    # Password:
    # HAL Mobile App Password
    #
    # The password itself is NOT stored.
    # Only mobile_app_password_hash is stored in Odoo.
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
        # Validate input
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
            # Only employees with Mobile App Access enabled
            # are allowed to log in.
            # -------------------------------------------------

            employee = request.env['hr.employee'].sudo().search(
                [
                    ('active', '=', True),
                    ('mobile_app_access', '=', True),
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
            # Ensure employee has a mobile password configured
            # -------------------------------------------------

            password_hash = employee.mobile_app_password_hash or ''

            if not password_hash:
                return {
                    'success': False,
                    'message': 'Mobile application password is not configured.',
                }

            # -------------------------------------------------
            # Verify entered password against stored hash
            # -------------------------------------------------

            try:
                password_valid = check_password_hash(
                    password_hash,
                    password,
                )
            except Exception:
                password_valid = False

            if not password_valid:
                return {
                    'success': False,
                    'message': 'Wrong username or password.',
                }

            # -------------------------------------------------
            # Employee image
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

        except Exception:
            return {
                'success': False,
                'message': 'Login error. Please try again.',
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

        # -----------------------------------------------------
        # Validate Employee ID
        # -----------------------------------------------------

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

            # -------------------------------------------------
            # Look for currently open attendance
            # -------------------------------------------------

            attendance = request.env['hr.attendance'].sudo().search(
                [
                    ('employee_id', '=', employee.id),
                    ('check_out', '=', False),
                ],
                order='check_in desc',
                limit=1,
            )

            # -------------------------------------------------
            # Employee is currently checked in
            # -------------------------------------------------

            if attendance:
                return {
                    'success': True,
                    'checked_in': True,
                    'attendance_id': attendance.id,
                    'check_in': self._datetime_to_utc_iso(
                        attendance.check_in
                    ),
                    'check_out': False,
                }

            # -------------------------------------------------
            # Get last completed attendance
            # -------------------------------------------------

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
                    self._datetime_to_utc_iso(
                        last_attendance.check_in
                    )
                    if (
                        last_attendance
                        and last_attendance.check_in
                    )
                    else False
                ),

                'check_out': (
                    self._datetime_to_utc_iso(
                        last_attendance.check_out
                    )
                    if (
                        last_attendance
                        and last_attendance.check_out
                    )
                    else False
                ),
            }

        except Exception:
            return {
                'success': False,
                'message': 'Could not load attendance status.',
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

        # -----------------------------------------------------
        # Validate Employee ID
        # -----------------------------------------------------

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

            # -------------------------------------------------
            # Check if employee already has an open attendance
            # -------------------------------------------------

            existing_attendance = (
                request.env['hr.attendance']
                .sudo()
                .search(
                    [
                        ('employee_id', '=', employee.id),
                        ('check_out', '=', False),
                    ],
                    order='check_in desc',
                    limit=1,
                )
            )

            if existing_attendance:
                return {
                    'success': False,
                    'message': 'Employee is already checked in.',
                }

            # -------------------------------------------------
            # Create attendance record
            # -------------------------------------------------

            attendance = request.env['hr.attendance'].sudo().create(
                {
                    'employee_id': employee.id,
                    'check_in': fields.Datetime.now(),
                }
            )

            # -------------------------------------------------
            # Success
            # -------------------------------------------------

            return {
                'success': True,
                'message': 'Check in successful.',
                'attendance_id': attendance.id,
                'employee_id': employee.id,
                'employee_name': employee.name or '',

                'check_in': self._datetime_to_utc_iso(
                    attendance.check_in
                ),
            }

        except Exception:
            return {
                'success': False,
                'message': 'Check in failed.',
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

        # -----------------------------------------------------
        # Validate Employee ID
        # -----------------------------------------------------

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

            # -------------------------------------------------
            # Find employee's current open attendance
            # -------------------------------------------------

            attendance = request.env['hr.attendance'].sudo().search(
                [
                    ('employee_id', '=', employee.id),
                    ('check_out', '=', False),
                ],
                order='check_in desc',
                limit=1,
            )

            # -------------------------------------------------
            # No open attendance
            # -------------------------------------------------

            if not attendance:
                return {
                    'success': False,
                    'message': 'No active check in was found.',
                }

            # -------------------------------------------------
            # Set Check Out time
            # -------------------------------------------------

            attendance.sudo().write(
                {
                    'check_out': fields.Datetime.now(),
                }
            )

            # -------------------------------------------------
            # Success
            # -------------------------------------------------

            return {
                'success': True,
                'message': 'Check out successful.',
                'attendance_id': attendance.id,
                'employee_id': employee.id,
                'employee_name': employee.name or '',

                'check_in': self._datetime_to_utc_iso(
                    attendance.check_in
                ),

                'check_out': self._datetime_to_utc_iso(
                    attendance.check_out
                ),
            }

        except Exception:
            return {
                'success': False,
                'message': 'Check out failed.',
            }
