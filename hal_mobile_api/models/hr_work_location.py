from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrWorkLocation(models.Model):
    _inherit = 'hr.work.location'

    hal_latitude = fields.Float(
        string='Latitude',
        digits=(10, 7),
        help=(
            'Latitude of this work location. '
            'Used by HAL Mobile to validate attendance.'
        ),
    )

    hal_longitude = fields.Float(
        string='Longitude',
        digits=(10, 7),
        help=(
            'Longitude of this work location. '
            'Used by HAL Mobile to validate attendance.'
        ),
    )

    hal_attendance_radius = fields.Float(
        string='Allowed Check-in Radius (m)',
        default=40.0,
        help=(
            'Maximum distance in meters from this work '
            'location where an employee may check in.'
        ),
    )

    # =========================================================
    # VALIDATION
    # =========================================================

    @api.constrains(
        'hal_latitude',
        'hal_longitude',
        'hal_attendance_radius',
    )
    def _check_hal_location_values(self):
        for record in self:

            if record.hal_latitude:
                if not -90 <= record.hal_latitude <= 90:
                    raise ValidationError(
                        'Latitude must be between -90 and 90.'
                    )

            if record.hal_longitude:
                if not -180 <= record.hal_longitude <= 180:
                    raise ValidationError(
                        'Longitude must be between -180 and 180.'
                    )

            if record.hal_attendance_radius < 0:
                raise ValidationError(
                    'Allowed attendance radius cannot be negative.'
                )

    # =========================================================
    # GOOGLE MAPS API KEY
    # =========================================================

    @api.model
    def get_hal_google_maps_api_key(self):
        """
        Called only by the Odoo backend map widget.

        The Google Maps browser key is stored centrally inside
        ir.config_parameter instead of being stored on every
        work location.
        """

        return (
            self.env['ir.config_parameter']
            .sudo()
            .get_param(
                'hal_mobile_api.google_maps_api_key',
                default='',
            )
        )
