{
    'name': 'Task Management',
    'version': '1.0',
    'author': 'Nadira',
    'depends': ['base', 'project', 'hr'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'views/task_mgmt_view.xml',
        # 'views/users_inherit_view.xml'
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',

}
