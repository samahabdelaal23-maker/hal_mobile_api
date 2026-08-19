from odoo import http
from odoo.http import request


class HalMobileApi(http.Controller):

    @http.route(
        '/hal/api/ping',
        type='json',
        auth='public',
        methods=['POST'],
        csrf=False,
    )
    def ping(self, **kwargs):
        """
        Simple connectivity test.

        Used by the HAL Flutter application to verify that
        the Odoo backend is reachable.
        """

        return {
            'success': True,
            'message': 'HAL successfully connected to Odoo.',
            'database': request.env.cr.dbname,
            'server': 'Odoo 18',
        }