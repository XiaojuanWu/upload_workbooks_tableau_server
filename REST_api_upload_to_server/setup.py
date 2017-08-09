from setuptools import setup

setup(
    name='upload_script',
    version='1.1',
    url='https://github.com/Adapp/tune_BI',
    license='MIT',
    author='Stephen Berndt',
    author_email='stephenb@tune.com',
    description='Content management script for Tune Marketing Intelligence',
    long_description='This can be found at https://github.com/Adapp/tune_BI/tree/master/REST_api_upload_to_server',
    platforms='any',
    install_requires=[
        'lxml',
        'tableaudocumentapi',
        'tableau_tools',
        'psycopg2',
        'sqlalchemy',
        'Naked',
        'argparse'
    ],
    dependency_links=[
        'https://downloads.tableau.com/tssoftware/Tableau-SDK-Python-OSX-64Bit-10-0-0.tar.gz'
    ]
)
