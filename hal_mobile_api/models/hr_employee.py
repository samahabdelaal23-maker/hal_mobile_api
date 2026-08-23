from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from werkzeug.security import generate_password_hash


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    mobile_app_access = fields.Boolean(
        string='Mobile App Access',
        default=False,
        help='Enable this employee to sign in to the HAL mobile application.',
    )

    mobile_app_password = fields.Char(
        string='Mobile App Password',
        copy=False,
        help='Password used by this employee to sign in to the HAL mobile application.',
    )

    mobile_app_password_hash = fields.Char(
        string='Mobile App Password Hash',
        copy=False,
        groups='hr.group_hr_manager',
    )

    @api.constrains('work_email', 'mobile_app_access')
    def _check_unique_mobile_work_email(self):
        for employee in self:
            if not employee.mobile_app_access:
                continue

            if not employee.work_email:
                raise ValidationError(
                    _(
                        'Work Email is required when Mobile App Access '
                        'is enabled.'
                    )
                )

            duplicate = self.sudo().search([
                ('id', '!=', employee.id),
                ('mobile_app_access', '=', True),
                ('work_email', '=ilike', employee.work_email.strip()),
            ], limit=1)

            if duplicate:
                raise ValidationError(
                    _(
                        'This Work Email is already used by another '
                        'employee with Mobile App Access.'
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            password = vals.pop('mobile_app_password', False)

            if password:
                vals['mobile_app_password_hash'] = (
                    generate_password_hash(password)
                )

        return super().create(vals_list)

    def write(self, vals):
        password = vals.pop('mobile_app_password', False)

        if password:
            vals['mobile_app_password_hash'] = (
                generate_password_hash(password)
            )

        return super().write(vals)
