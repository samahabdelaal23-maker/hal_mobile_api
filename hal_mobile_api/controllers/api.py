from datetime import timezone
from math import radians, sin, cos, sqrt, atan2

from odoo import http, fields
from odoo.http import request

from werkzeug.security import check_password_hash


class HalMobileApi(http.Controller):

    # =========================================================
    # HELPERS
    # =========================================================

    def _datetime_to_utc_iso(self, value):
        if not value:
            return False

        return value.replace(
            tzinfo=timezone.utc
        ).isoformat()

    def _calculate_distance_meters(
        self,
        lat1,
        lon1,
        lat2,
        lon2,
    ):
        """
        Calculate distance between two GPS coordinates
        using the Haversine formula.

        Returns distance in meters.
        """

        earth_radius = 6371000.0

        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)

        delta_lat = lat2_rad - lat1_rad
        delta_lon = lon2_rad - lon1_rad

        a = (
            sin(delta_lat / 2) ** 2
            + cos(lat1_rad)
            * cos(lat2_rad)
            * sin(delta_lon / 2) ** 2
        )

        c = 2 * atan2(
            sqrt(a),
            sqrt(1 - a),
        )

        return earth_radius * c

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
    def login(
        self,
        login=None,
        password=None,
        **kwargs,
    ):

        if not login or not password:
            return {
                'success': False,
                'message': 'Username and password are required.',
            }

        try:
            login_value = login.strip()

            employee = request.env[
                'hr.employee'
            ].sudo().search(
                [
                    ('active', '=', True),
                    ('mobile_app_access', '=', True),
                    ('work_email', '=ilike', login_value),
                ],
                limit=1,
            )

            if not employee:
                return {
                    'success': False,
                    'message': 'Wrong username or password.',
                }

            password_hash = (
                employee.mobile_app_password_hash
                or ''
            )

            if not password_hash:
                return {
                    'success': False,
                    'message': (
                        'Mobile application password '
                        'is not configured.'
                    ),
                }

            try:
                password_valid = (
                    check_password_hash(
                        password_hash,
                        password,
                    )
                )
            except Exception:
                password_valid = False

            if not password_valid:
                return {
                    'success': False,
                    'message': 'Wrong username or password.',
                }

            employee_image = ''

            if employee.image_128:
                employee_image = (
                    employee.image_128.decode(
                        'utf-8'
                    )
                )

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
    def attendance_status(
        self,
        employee_id=None,
        **kwargs,
    ):

        if not employee_id:
            return {
                'success': False,
                'message': 'Employee ID is required.',
            }

        try:
            employee = request.env[
                'hr.employee'
            ].sudo().browse(
                int(employee_id)
            )

            if not employee.exists():
                return {
                    'success': False,
                    'message': 'Employee not found.',
                }

            attendance = request.env[
                'hr.attendance'
            ].sudo().search(
                [
                    (
                        'employee_id',
                        '=',
                        employee.id,
                    ),
                    (
                        'check_out',
                        '=',
                        False,
                    ),
                ],
                order='check_in desc',
                limit=1,
            )

            if attendance:
                return {
                    'success': True,
                    'checked_in': True,
                    'attendance_id': attendance.id,
                    'check_in':
                        self._datetime_to_utc_iso(
                            attendance.check_in
                        ),
                    'check_out': False,
                }

            last_attendance = request.env[
                'hr.attendance'
            ].sudo().search(
                [
                    (
                        'employee_id',
                        '=',
                        employee.id,
                    ),
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
                'message': (
                    'Could not load attendance status.'
                ),
            }

    # =========================================================
    # CHECK IN WITH GPS VALIDATION
    # =========================================================

    @http.route(
        '/hal/api/attendance/checkin',
        type='json',
        auth='public',
        methods=['POST'],
        csrf=False,
    )
    def attendance_checkin(
        self,
        employee_id=None,
        latitude=None,
        longitude=None,
        **kwargs,
    ):

        # -----------------------------------------------------
        # Validate Employee ID
        # -----------------------------------------------------

        if not employee_id:
            return {
                'success': False,
                'message': 'Employee ID is required.',
            }

        # -----------------------------------------------------
        # Validate GPS values
        # -----------------------------------------------------

        if latitude is None or longitude is None:
            return {
                'success': False,
                'message': (
                    'Your current location is required '
                    'to check in.'
                ),
            }

        try:
            employee = request.env[
                'hr.employee'
            ].sudo().browse(
                int(employee_id)
            )

            if not employee.exists():
                return {
                    'success': False,
                    'message': 'Employee not found.',
                }

            # -------------------------------------------------
            # Employee Work Location
            # -------------------------------------------------

            work_location = employee.work_location_id

            if not work_location:
                return {
                    'success': False,
                    'message': (
                        'No work location is assigned '
                        'to this employee.'
                    ),
                }

            # -------------------------------------------------
            # Office GPS configuration
            # -------------------------------------------------

            office_latitude = (
                work_location.hal_latitude
            )

            office_longitude = (
                work_location.hal_longitude
            )

            allowed_radius = (
                work_location.hal_attendance_radius
            )

            # Treat 0 / 0 as not configured.
            if (
                not office_latitude
                and not office_longitude
            ):
                return {
                    'success': False,
                    'message': (
                        'GPS coordinates are not configured '
                        'for your work location.'
                    ),
                }

            if (
                not allowed_radius
                or allowed_radius <= 0
            ):
                return {
                    'success': False,
                    'message': (
                        'Attendance radius is not configured '
                        'for your work location.'
                    ),
                }

            # -------------------------------------------------
            # Convert mobile coordinates
            # -------------------------------------------------

            try:
                employee_latitude = float(
                    latitude
                )

                employee_longitude = float(
                    longitude
                )

            except (
                TypeError,
                ValueError,
            ):
                return {
                    'success': False,
                    'message': (
                        'Invalid mobile GPS coordinates.'
                    ),
                }

            # -------------------------------------------------
            # Coordinate validation
            # -------------------------------------------------

            if not (
                -90.0
                <= employee_latitude
                <= 90.0
            ):
                return {
                    'success': False,
                    'message': (
                        'Invalid latitude received.'
                    ),
                }

            if not (
                -180.0
                <= employee_longitude
                <= 180.0
            ):
                return {
                    'success': False,
                    'message': (
                        'Invalid longitude received.'
                    ),
                }

            # -------------------------------------------------
            # Calculate distance
            # -------------------------------------------------

            distance = (
                self._calculate_distance_meters(
                    employee_latitude,
                    employee_longitude,
                    office_latitude,
                    office_longitude,
                )
            )

            # -------------------------------------------------
            # Employee outside allowed area
            # -------------------------------------------------

            if distance > allowed_radius:
                return {
                    'success': False,
                    'message': (
                        'You are outside the allowed '
                        'check-in area.'
                    ),
                    'distance_meters': round(
                        distance,
                        1,
                    ),
                    'allowed_radius_meters':
                        allowed_radius,
                }

            # -------------------------------------------------
            # Already checked in?
            # -------------------------------------------------

            existing_attendance = (
                request.env[
                    'hr.attendance'
                ]
                .sudo()
                .search(
                    [
                        (
                            'employee_id',
                            '=',
                            employee.id,
                        ),
                        (
                            'check_out',
                            '=',
                            False,
                        ),
                    ],
                    order='check_in desc',
                    limit=1,
                )
            )

            if existing_attendance:
                return {
                    'success': False,
                    'message': (
                        'Employee is already checked in.'
                    ),
                }

            # -------------------------------------------------
            # Create attendance
            # -------------------------------------------------

            attendance = request.env[
                'hr.attendance'
            ].sudo().create(
                {
                    'employee_id': employee.id,
                    'check_in':
                        fields.Datetime.now(),
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

                'check_in':
                    self._datetime_to_utc_iso(
                        attendance.check_in
                    ),

                'distance_meters': round(
                    distance,
                    1,
                ),

                'allowed_radius_meters':
                    allowed_radius,

                'work_location_id':
                    work_location.id,

                'work_location_name':
                    work_location.name or '',
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
    def attendance_checkout(
        self,
        employee_id=None,
        **kwargs,
    ):

        if not employee_id:
            return {
                'success': False,
                'message': 'Employee ID is required.',
            }

        try:
            employee = request.env[
                'hr.employee'
            ].sudo().browse(
                int(employee_id)
            )

            if not employee.exists():
                return {
                    'success': False,
                    'message': 'Employee not found.',
                }

            attendance = request.env[
                'hr.attendance'
            ].sudo().search(
                [
                    (
                        'employee_id',
                        '=',
                        employee.id,
                    ),
                    (
                        'check_out',
                        '=',
                        False,
                    ),
                ],
                order='check_in desc',
                limit=1,
            )

            if not attendance:
                return {
                    'success': False,
                    'message': (
                        'No active check in was found.'
                    ),
                }

            attendance.sudo().write(
                {
                    'check_out':
                        fields.Datetime.now(),
                }
            )

            return {
                'success': True,
                'message': 'Check out successful.',
                'attendance_id': attendance.id,
                'employee_id': employee.id,
                'employee_name': employee.name or '',

                'check_in':
                    self._datetime_to_utc_iso(
                        attendance.check_in
                    ),

                'check_out':
                    self._datetime_to_utc_iso(
                        attendance.check_out
                    ),
            }

        except Exception:
            return {
                'success': False,
                'message': 'Check out failed.',
            }
