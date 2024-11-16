from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    user_type = fields.Selection([
        ('admin', 'Admin'),
        ('inspector', 'Inspector'),
        ('manager', 'Manager'),
        ('user', 'User')
    ], string="User Type")
