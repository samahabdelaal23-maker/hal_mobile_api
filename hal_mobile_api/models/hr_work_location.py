from odoo import fields, models


class HrWorkLocation(models.Model):
    _inherit = 'hr.work.location'

    hal_latitude = fields.Float(
        string='Latitude',
        digits=(10, 7),
        help='Latitude of this work location used for mobile attendance validation.',
    )

    hal_longitude = fields.Float(
        string='Longitude',
        digits=(10, 7),
        help='Longitude of this work location used for mobile attendance validation.',
    )

    hal_attendance_radius = fields.Float(
        string='Allowed Check-in Radius (m)',
        default=40.0,
        help='Maximum distance in meters allowed for mobile check-in/check-out.',
    )
