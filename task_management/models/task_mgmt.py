from xml import etree

from odoo import models, fields, api, exceptions
from odoo.exceptions import UserError
from datetime import date


class Task(models.Model):
    _name = 'task.management'
    _description = 'Task Management'
    _inherit = ['mail.thread']


    name = fields.Char(string="Task Number", required=True, copy=False, readonly=True, default="New")
    date = fields.Date(string="Date", required=True, tracking=True)
    task_name = fields.Char(string="Task Name", required=True)
    user_id = fields.Many2one('res.users', string="Users", domain=lambda self: [('groups_id', 'in', [self.env.ref('task_management.group_user').id])], tracking=True)
    department_id = fields.Many2one('hr.department', string="Department", required=True, tracking=True)
    ledger = fields.Text(string="Ledger/Code", tracking=True)
    voucher_type = fields.Selection([
        ('sales', 'Sales/Purchase'),
        ('receipt', 'Receipt/Payment'),
        ('journal', 'Journal'),
        ('material_issue', 'Material Issue/Receipt'),
        ('other', 'Others')
    ], string="Voucher Type", tracking=True)
    find1 = fields.Text(string="Find 1", tracking=True)
    find2 = fields.Text(string="Find 2", tracking=True)
    remarks = fields.Text(string="Remarks", tracking=True)
    user_manager = fields.Char(string="User/Manager", tracking=True)
    status = fields.Selection([
        ('inspection', 'Inspection'),
        ('monitoring', 'Monitoring'),
        ('user_check', 'User Check'),
        ('action','Action'),
        ('reporting', 'Reporting'),
        ('completed', 'Completed')

    ], string="Status", default='inspection', tracking=True)
    assign_user = fields.Boolean(string="Assign User")

    # Conditional Fields
    comment = fields.Text(string="Comment", help="Required when status is Re-check")
    explanation = fields.Text(string="Explanation", help="Required when status is Reviewed", tracking=True)
    deadline = fields.Date(string="Deadline")
    is_satisfactory = fields.Boolean("Satisfactory", default=False, tracking=True)
    is_deadline_overdue = fields.Boolean(
        string="Is Deadline Overdue",
        compute="_compute_is_deadline_overdue",
        store=True
    )


    current_user_department_id = fields.Many2one(
        'hr.department', string="User's Department", compute="_compute_user_department", store=False
    )



    @api.depends('deadline')
    def _compute_is_deadline_overdue(self):
        for record in self:
            record.is_deadline_overdue = record.deadline and record.deadline < date.today()

    @api.depends('department_id')
    def _compute_user_department(self):
        for record in self:
            # Find the employee record linked to the current user
            employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            # Set the user's department based on the employee's department, or False if not set
            record.current_user_department_id = employee.department_id if employee else False

    # @api.model
    # def create(self, vals):
    #     if self.env.user.user_type not in ['admin', 'inspector']:
    #         raise exceptions.AccessError("Only Admin and Inspector can create tasks.")
    #     return super(Task, self).create(vals)

    @api.model
    def _remove_record_rules(self):
        # Search for specific record rules and delete them
        rules_to_remove = self.env['ir.rule'].search([
            ('name', '=', 'Deny Task Creation for User and Reporting Manager')  # Replace with the record rule's name or other filters
        ])
        rules_to_remove.unlink()

    is_readonly = fields.Boolean(
        compute="_compute_readonly_fields",
        string="Readonly Flag",
        store=False,
    )

    @api.depends('user_id')
    def _compute_readonly_fields(self):
        for record in self:
            user = self.env.user
            if user.has_group('task_management.group_user') or user.has_group(
                    'task_management.group_reporting_manager'):
                record.is_readonly = True
            else:
                record.is_readonly = False

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(Task, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
    #                                                       submenu=submenu)
    #
    #     if self.env.user.has_group('task_management.group_user') or self.env.user.has_group(
    #             'task_management.group_reporting_manager'):
    #         doc = etree.XML(res['arch'])
    #         for field in doc.xpath("//field"):
    #             if field.get('name') != 'explanation':  # Exclude explanation
    #                 field.set('readonly', '1')
    #         res['arch'] = etree.tostring(doc)
    #     return res

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('task.management') or 'New'
        return super(Task, self).create(vals)
        """Override create method to set initial status based on the user creating the task."""
        user = self.env.user
        # If an inspector creates the task, set to 'inspection' status.
        if user.has_group('task_management.group_inspector'):
            vals['status'] = 'inspection'
        # If an admin creates the task, move directly to 'monitoring' status.
        elif user.has_group('task_management.group_admin'):
            vals['status'] = 'inspection'
            vals['user_id'] = user.id  # Set admin as the monitoring user
        elif user.has_group('task_management.group_user') or user.has_group('task_management.group_reporting_manager'):
            raise UserError("only admin can create tasks")

        return super(Task, self).create(vals)

    def action_submit_for_monitoring(self):

        """Move task to monitoring if created by an inspector."""
        if self.env.user.has_group('task_management.group_inspector') and self.status == 'inspection':
            # Move to monitoring status and assign it to the admin
            admin_user = self.env.ref('task_management.group_admin').users[:1]
            print(admin_user,'&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
            if admin_user:
                self.write({'status': 'monitoring', 'user_id': admin_user})
            else:
                raise UserError("No Admin user found to assign the task.")
        elif self.env.user.has_group('task_management.group_admin') and self.status == 'inspection':
            self.write({'status': 'monitoring'})


        else:
            raise UserError("Only Inspectors can submit tasks for monitoring.")


    def action_assign_to_user(self):
        if self.status != 'monitoring':
            raise UserError("Tasks can only be assigned in the Monitoring stage.")
        if not self.env.user.has_group('task_management.group_admin'):
            raise UserError("Only Admins can assign tasks.")
        user_id = self.user_id
        self.write({'assign_user': True, 'status': 'user_check', 'user_id': user_id})

    def action_assign_to_recheck(self):
        self.write({'status': 'inspection'})

    def action_user_add_comment(self):
        if not self.explanation:
            raise UserError("Please provide an explanation before submitting.")

        if self.env.user.has_group('task_management.group_user'):
            self.write({'status': 'action'})
        else:
            raise UserError("Only Users can add comments.")


    def action_admin_review(self):
        if self.env.user.has_group('task_management.group_admin'):
            if self.is_satisfactory:
                self.write({'status': 'completed'})
            else:
                self.write({'status': 'user_check'})
        else:
            raise UserError("Only Admin can review the task.")

    def action_report_to_manager_or_complete(self):
        if self.env.user.has_group('task_management.group_admin') or self.env.user.has_group('task_management.group_inspector') and self.status == 'action':
            self.write({'status': 'reporting'})
        else:
            raise UserError("Only Admin can report the task to the manager.")
        # if self.env.user.has_group('your_module.group_reporting_manager') or self.env.user.has_group('your_module.group_admin'):
        #     new_state = 'completed' if mark_completed else 'reporting'
        #     self.write({'status': new_state})
        # else:
        #     raise UserError("Only Admins and Reporting Managers can mark as completed.")