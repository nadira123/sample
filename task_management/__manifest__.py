{
    'name': 'Task Management',
    'version': '1.0',
    'author': 'Nadira',
    'depends': ['base', 'project', 'hr'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'data/sequence.xml',
        'views/task_mgmt_view.xml',
        'views/menu_item.xml'
        # 'views/users_inherit_view.xml'
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'task_management/static/src/css/style.css',
    #     ],
    # },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',

}
