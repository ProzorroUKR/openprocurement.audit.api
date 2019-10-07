from setuptools import setup, find_packages

version = '1.0.11'

requires = [
    'pyramid<1.10.0',
    'schematics<2.0.0',
    'cornice==1.2.0.dev0',
    'restkit>=0.27.2',
    'couchdb-schematics',
    'barbecue',
    'chaussette',
    'cornice',
    'couchdb-schematics',
    'gevent',
    'iso8601',
    'isodate',
    'zope.component',
    'zope.configuration',
    'esculator',
    'pycrypto',
    'libnacl',
    'pbkdf2',
    'six',
    'pytz',
    'pyramid_exclog',
    'jsonpatch==1.13-jsondiff.unicode.replacefix.0',
    'rfc6266==0.0.6',
    'openprocurement_client==1.0b3'
]
test_requires = requires + [
    'pytest',
    'pytest-xdist',
    'webtest',
    'freezegun',
    'python-coveralls',
    'mock',
    'coverage',
    'pytest-cov',
]
setup_requires = [
    'pytest-runner',
    'setuptools==33.1.1',
    'six',
]
dependency_links = [
    "https://github.com/ProzorroUKR/openprocurement.client.python/tarball/1.0b3#egg=openprocurement_client-1.0b3",
    "https://github.com/ProzorroUKR/esculator/tarball/master#egg=esculator",
    "https://github.com/ProzorroUKR/dateorro/tarball/master#egg=dateorro",
    "https://github.com/ProzorroUKR/barbecue/tarball/master#egg=barbecue",
    "https://github.com/ProzorroUKR/cornice/tarball/1.2.0.dev0#egg=cornice-1.2.0.dev0",
    "https://github.com/ProzorroUKR/rfc6266/tarball/0.0.6#egg=rfc6266-0.0.6",
    "https://github.com/ProzorroUKR/python-json-patch/tarball/1.13-jsondiff.unicode.replacefix.0#egg=jsonpatch-1.13-jsondiff.unicode.replacefix.0",
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
      setup_requires=setup_requires,
      tests_require=test_requires,
      extras_require={'test': test_requires},
      dependency_links=dependency_links,
      entry_points=entry_points)
