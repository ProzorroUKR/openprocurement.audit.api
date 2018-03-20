from setuptools import setup, find_packages

version = '1.0.0'

requires = [
    'setuptools',
    'openprocurement.api>=2.4',
]
test_requires = requires + [
    'webtest',
    'python-coveralls',
]
docs_requires = requires + [
    'sphinxcontrib-httpdomain',
]

entry_points = {
    'openprocurement.api.plugins': [
        'audit = openprocurement.audit.api:includeme'
    ]
}

setup(name='openprocurement.audit.api',
      version=version,
      description="",
      long_description=open("README.md").read(),
      classifiers=[
        "Programming Language :: Python",
      ],
      keywords='',
      author='RaccoonGang',
      author_email='info@raccoongang.com',
      license='Apache License 2.0',
      url='https://github.com/alekseystryukov/openprocurement.audit.api',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['openprocurement', 'openprocurement.audit'],
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=test_requires,
      extras_require={'test': test_requires, 'docs': docs_requires},
      test_suite="openprocurement.audit.api.tests.main.suite",
      entry_points=entry_points,
      )
