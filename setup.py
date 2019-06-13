from setuptools import setup, find_packages

version = '1.0.11'

requires = [
    'setuptools',
    'restkit>=0.27.2'
]
test_requires = requires + [
    'webtest',
    'freezegun',
    'python-coveralls',
]
docs_requires = requires + [
    'sphinxcontrib-httpdomain',
]

entry_points = {
    'paste.app_factory': [
        'main = openprocurement.audit.api.app:main'
    ],
    'openprocurement.audit.api.plugins': [
        'api = openprocurement.audit.api:includeme',
        'monitoring = openprocurement.audit.monitoring:includeme',
        'inspection = openprocurement.audit.inspection:includeme',
    ]
}

setup(name='openprocurement.audit.api',
      version=version,
      long_description=open("README.rst").read(),
      classifiers=[
          "Programming Language :: Python",
      ],
      author='RaccoonGang',
      author_email='info@raccoongang.com',
      license='Apache License 2.0',
      url='https://github.com/ProzorroUKR/openprocurement.audit.api',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['openprocurement', 'openprocurement.audit'],
      include_package_data=True,
      package_data={'': ['data/*.json']},
      zip_safe=False,
      install_requires=requires,
      tests_require=test_requires,
      extras_require={'test': test_requires, 'docs': docs_requires},
      test_suite="openprocurement.audit.api.tests.main.suite",
      entry_points=entry_points)
